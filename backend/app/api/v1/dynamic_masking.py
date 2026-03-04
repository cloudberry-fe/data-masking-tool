"""
动态脱敏 API

动态脱敏特点:
- 针对表配置脱敏规则
- 为特定数据库角色设置脱敏
- 使用 PostgreSQL SECURITY LABEL 机制
- 查询时实时脱敏
"""
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.common import Response, PageResponse
from app.api.deps import CurrentUser, DBSession, AuditLogger

router = APIRouter()


# ==================== 请求模型 ====================

class CreateDynamicRuleRequest(BaseModel):
    """创建动态脱敏规则请求"""
    rule_name: str = Field(..., description="规则名称")
    datasource_id: int = Field(..., description="数据源ID")
    schema_name: str = Field(default="public", description="Schema名")
    table_name: str = Field(..., description="表名")
    masked_roles: List[str] = Field(..., description="被脱敏的数据库角色列表")
    exempted_roles: Optional[List[str]] = Field(default=None, description="豁免角色列表")
    description: Optional[str] = Field(default=None, description="描述")


class AddColumnRuleRequest(BaseModel):
    """添加字段规则请求"""
    column_name: str = Field(..., description="字段名")
    masking_algorithm: str = Field(..., description="脱敏算法")
    algorithm_params: Optional[Dict[str, Any]] = Field(default=None, description="算法参数")


# ==================== 动态脱敏规则 ====================

@router.get("/rules", response_model=Response[PageResponse])
def get_dynamic_rules(
    db: DBSession,
    current_user: CurrentUser,
    page: int = 1,
    page_size: int = 20,
    datasource_id: Optional[int] = None,
    status: Optional[str] = None,
):
    """
    获取动态脱敏规则列表

    动态脱敏规则为特定表配置角色脱敏：
    - 指定表和字段
    - 配置被脱敏的数据库角色
    - 配置豁免角色（可查看原始数据）
    """
    from app.models.dynamic_masking import DynamicMaskingRule

    query = db.query(DynamicMaskingRule)

    if datasource_id:
        query = query.filter(DynamicMaskingRule.datasource_id == datasource_id)
    if status:
        query = query.filter(DynamicMaskingRule.status == status)

    total = query.count()
    rules = query.offset((page - 1) * page_size).limit(page_size).all()

    return Response(data=PageResponse(
        items=[{
            "id": r.id,
            "ruleName": r.rule_name,
            "datasourceId": r.datasource_id,
            "schemaName": r.schema_name,
            "tableName": r.table_name,
            "maskedRoles": r.masked_roles,
            "exemptedRoles": r.exempted_roles,
            "status": r.status,
            "isEnabled": r.is_enabled,
            "createdAt": r.created_at.isoformat() if r.created_at else None,
        } for r in rules],
        total=total,
        page=page,
        page_size=page_size
    ))


@router.post("/rules", response_model=Response)
def create_dynamic_rule(
    request: CreateDynamicRuleRequest,
    db: DBSession = None,
    current_user: CurrentUser = None,
    audit: AuditLogger = None,
):
    """
    创建动态脱敏规则

    参数:
    - rule_name: 规则名称
    - datasource_id: 数据源ID
    - schema_name: Schema名
    - table_name: 表名
    - masked_roles: 被脱敏的数据库角色列表（这些角色查询时会看到脱敏数据）
    - exempted_roles: 豁免角色列表（这些角色可查看原始数据）
    """
    from app.models.dynamic_masking import DynamicMaskingRule

    rule = DynamicMaskingRule(
        rule_name=request.rule_name,
        datasource_id=request.datasource_id,
        schema_name=request.schema_name or "public",
        table_name=request.table_name,
        masked_roles=request.masked_roles,
        exempted_roles=request.exempted_roles or [],
        description=request.description,
        created_by=current_user.id,
    )

    db.add(rule)
    db.commit()
    db.refresh(rule)

    audit("CREATE", "dynamic_masking", f"创建动态脱敏规则: {request.rule_name}")

    return Response(data={
        "id": rule.id,
        "ruleName": rule.rule_name,
        "message": "创建成功，请配置字段脱敏规则"
    })


@router.post("/rules/{rule_id}/columns", response_model=Response)
def add_column_rule(
    rule_id: int,
    request: AddColumnRuleRequest,
    db: DBSession = None,
    current_user: CurrentUser = None,
):
    """
    为动态脱敏规则添加字段脱敏配置

    参数:
    - rule_id: 规则ID
    - column_name: 字段名
    - masking_algorithm: 脱敏算法（如 anon.partial, anon.fake_email）
    - algorithm_params: 算法参数
    """
    from app.models.dynamic_masking import DynamicMaskingRule, DynamicMaskingColumnRule

    rule = db.get(DynamicMaskingRule, rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="规则不存在")

    column_rule = DynamicMaskingColumnRule(
        rule_id=rule_id,
        column_name=request.column_name,
        masking_algorithm=request.masking_algorithm,
        algorithm_params=request.algorithm_params or {},
    )

    db.add(column_rule)
    db.commit()

    return Response(message=f"字段 {request.column_name} 脱敏规则添加成功")


@router.post("/rules/{rule_id}/enable", response_model=Response)
def enable_dynamic_rule(
    rule_id: int,
    db: DBSession = None,
    current_user: CurrentUser = None,
    audit: AuditLogger = None,
):
    """
    启用动态脱敏规则

    执行操作：
    1. 为表字段设置 SECURITY LABEL
    2. 创建脱敏视图（可选）
    3. 授权角色
    """
    from app.models.dynamic_masking import DynamicMaskingRule
    from app.models.datasource import DataSource
    from app.services.datasource_service import DataSourceService
    from app.utils.hashdata_anon import HashDataAnonManager, MaskingColumnConfig

    rule = db.get(DynamicMaskingRule, rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="规则不存在")

    if not rule.column_rules:
        raise HTTPException(status_code=400, detail="请先配置字段脱敏规则")

    datasource = db.get(DataSource, rule.datasource_id)
    datasource_config = DataSourceService.get_datasource_config(datasource)

    anon_manager = HashDataAnonManager(datasource_config)

    # 生成 SQL
    column_configs = [
        MaskingColumnConfig(
            column_name=col.column_name,
            algorithm=col.masking_algorithm,
            params=col.algorithm_params or {},
        )
        for col in rule.column_rules
    ]

    from app.utils.hashdata_anon import MaskingTableConfig
    table_config = MaskingTableConfig(
        source_table=f"{rule.schema_name}.{rule.table_name}",
        target_table="",  # 动态脱敏不需要目标表
        columns=column_configs,
    )

    sql = anon_manager.generate_dynamic_masking_sql(
        table_config,
        source_schema=rule.schema_name,
        masked_role=rule.masked_roles[0] if rule.masked_roles else "masked",
        exempted_roles=rule.exempted_roles or [],
    )

    # 执行 SQL
    try:
        import psycopg2
        conn = anon_manager._get_connection(datasource_config)
        cursor = conn.cursor()

        for statement in sql.split(";"):
            lines = statement.strip().split('\n')
            actual_sql = ' '.join(line.strip() for line in lines
                                  if line.strip() and not line.strip().startswith("--"))
            if actual_sql:
                cursor.execute(actual_sql)

        conn.commit()
        cursor.close()
        conn.close()

        # 更新状态
        rule.is_enabled = True
        rule.status = "ACTIVE"
        db.commit()

        audit("EXECUTE", "dynamic_masking", f"启用动态脱敏规则: {rule.rule_name}")

        return Response(
            message=f"动态脱敏规则已启用，{rule.table_name} 表已配置角色脱敏",
            data={"sql": sql}
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"启用失败: {str(e)}")


@router.post("/rules/{rule_id}/disable", response_model=Response)
def disable_dynamic_rule(
    rule_id: int,
    db: DBSession = None,
    current_user: CurrentUser = None,
    audit: AuditLogger = None,
):
    """
    禁用动态脱敏规则

    执行操作：
    1. 移除 SECURITY LABEL
    2. 删除脱敏视图（如有）
    """
    from app.models.dynamic_masking import DynamicMaskingRule
    from app.models.datasource import DataSource
    from app.services.datasource_service import DataSourceService

    rule = db.get(DynamicMaskingRule, rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="规则不存在")

    datasource = db.get(DataSource, rule.datasource_id)
    datasource_config = DataSourceService.get_datasource_config(datasource)

    # 生成禁用 SQL
    table_full = f"{rule.schema_name}.{rule.table_name}"

    sql_parts = [
        "-- 禁用动态脱敏",
        f"DROP VIEW IF EXISTS {table_full}_masked;",
    ]

    # 移除 SECURITY LABEL
    for col_rule in rule.column_rules:
        sql_parts.append(
            f"SECURITY LABEL FOR anon ON COLUMN {table_full}.{col_rule.column_name} IS NULL;"
        )

    sql = "\n".join(sql_parts)

    try:
        import psycopg2
        anon_manager = HashDataAnonManager(datasource_config)
        conn = anon_manager._get_connection(datasource_config)
        cursor = conn.cursor()

        for statement in sql.split(";"):
            if statement.strip():
                cursor.execute(statement)

        conn.commit()
        cursor.close()
        conn.close()

        # 更新状态
        rule.is_enabled = False
        rule.status = "INACTIVE"
        db.commit()

        audit("EXECUTE", "dynamic_masking", f"禁用动态脱敏规则: {rule.rule_name}")

        return Response(message=f"动态脱敏规则已禁用")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"禁用失败: {str(e)}")


@router.delete("/rules/{rule_id}", response_model=Response)
def delete_dynamic_rule(
    rule_id: int,
    db: DBSession = None,
    current_user: CurrentUser = None,
    audit: AuditLogger = None,
):
    """删除动态脱敏规则"""
    from app.models.dynamic_masking import DynamicMaskingRule

    rule = db.get(DynamicMaskingRule, rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="规则不存在")

    if rule.is_enabled:
        raise HTTPException(status_code=400, detail="请先禁用规则")

    db.delete(rule)
    db.commit()

    audit("DELETE", "dynamic_masking", f"删除动态脱敏规则: {rule.rule_name}")

    return Response(message="删除成功")


@router.get("/rules/{rule_id}/preview-sql", response_model=Response)
def preview_dynamic_rule_sql(
    rule_id: int,
    db: DBSession = None,
    current_user: CurrentUser = None,
):
    """预览动态脱敏 SQL（不执行）"""
    from app.models.dynamic_masking import DynamicMaskingRule
    from app.models.datasource import DataSource
    from app.services.datasource_service import DataSourceService
    from app.utils.hashdata_anon import HashDataAnonManager, MaskingColumnConfig, MaskingTableConfig

    rule = db.get(DynamicMaskingRule, rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="规则不存在")

    datasource = db.get(DataSource, rule.datasource_id)
    datasource_config = DataSourceService.get_datasource_config(datasource)

    anon_manager = HashDataAnonManager(datasource_config)

    column_configs = [
        MaskingColumnConfig(
            column_name=col.column_name,
            algorithm=col.masking_algorithm,
            params=col.algorithm_params or {},
        )
        for col in rule.column_rules
    ]

    table_config = MaskingTableConfig(
        source_table=f"{rule.schema_name}.{rule.table_name}",
        target_table="",
        columns=column_configs,
    )

    sql = anon_manager.generate_dynamic_masking_sql(
        table_config,
        source_schema=rule.schema_name,
        masked_role=rule.masked_roles[0] if rule.masked_roles else "masked",
        exempted_roles=rule.exempted_roles or [],
    )

    return Response(data={
        "sql": sql,
        "tableName": rule.table_name,
        "maskedRoles": rule.masked_roles,
        "exemptedRoles": rule.exempted_roles,
    })
