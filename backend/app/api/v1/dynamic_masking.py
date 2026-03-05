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
import traceback
import logging

from app.core.database import get_db
from app.schemas.common import Response, PageResponse
from app.api.deps import CurrentUser, DBSession, AuditLogger

router = APIRouter()
logger = logging.getLogger(__name__)


# ==================== 请求模型 ====================

class CreateDynamicRuleRequest(BaseModel):
    """创建动态脱敏规则请求"""
    rule_name: Optional[str] = Field(default=None, description="规则名称 (snake_case)")
    ruleName: Optional[str] = Field(default=None, description="规则名称 (camelCase)")
    datasource_id: Optional[int] = Field(default=None, description="数据源ID (snake_case)")
    datasourceId: Optional[int] = Field(default=None, description="数据源ID (camelCase)")
    schema_name: str = Field(default="public", description="Schema名 (snake_case)")
    schemaName: Optional[str] = Field(default=None, description="Schema名 (camelCase)")
    table_name: Optional[str] = Field(default=None, description="表名 (snake_case)")
    tableName: Optional[str] = Field(default=None, description="表名 (camelCase)")
    masked_roles: Optional[List[str]] = Field(default=None, description="被脱敏的数据库角色列表 (snake_case)")
    maskedRoles: Optional[List[str]] = Field(default=None, description="被脱敏的数据库角色列表 (camelCase)")
    exempted_roles: Optional[List[str]] = Field(default=None, description="豁免角色列表 (snake_case)")
    exemptedRoles: Optional[List[str]] = Field(default=None, description="豁免角色列表 (camelCase)")
    description: Optional[str] = Field(default=None, description="描述")

    def get_rule_name(self) -> str:
        return self.rule_name or self.ruleName

    def get_datasource_id(self) -> int:
        return self.datasource_id or self.datasourceId

    def get_schema_name(self) -> str:
        return self.schema_name or self.schemaName or "public"

    def get_table_name(self) -> str:
        return self.table_name or self.tableName

    def get_masked_roles(self) -> List[str]:
        return self.masked_roles or self.maskedRoles or []

    def get_exempted_roles(self) -> List[str]:
        return self.exempted_roles or self.exemptedRoles or []


class UpdateDynamicRuleRequest(BaseModel):
    """更新动态脱敏规则请求"""
    rule_name: Optional[str] = Field(default=None, description="规则名称")
    ruleName: Optional[str] = Field(default=None, description="规则名称 (camelCase)")
    schema_name: Optional[str] = Field(default=None, description="Schema名")
    schemaName: Optional[str] = Field(default=None, description="Schema名 (camelCase)")
    table_name: Optional[str] = Field(default=None, description="表名")
    tableName: Optional[str] = Field(default=None, description="表名 (camelCase)")
    masked_roles: Optional[List[str]] = Field(default=None, description="被脱敏角色列表")
    maskedRoles: Optional[List[str]] = Field(default=None, description="被脱敏角色列表 (camelCase)")
    exempted_roles: Optional[List[str]] = Field(default=None, description="豁免角色列表")
    exemptedRoles: Optional[List[str]] = Field(default=None, description="豁免角色列表 (camelCase)")
    description: Optional[str] = Field(default=None, description="描述")


class AddColumnRuleRequest(BaseModel):
    """添加字段规则请求"""
    column_name: Optional[str] = Field(default=None, description="字段名 (snake_case)")
    columnName: Optional[str] = Field(default=None, description="字段名 (camelCase)")
    masking_algorithm: Optional[str] = Field(default=None, description="脱敏算法 (snake_case)")
    maskingAlgorithm: Optional[str] = Field(default=None, description="脱敏算法 (camelCase)")
    algorithm_params: Optional[Dict[str, Any]] = Field(default=None, description="算法参数 (snake_case)")
    algorithmParams: Optional[Dict[str, Any]] = Field(default=None, description="算法参数 (camelCase)")

    def get_column_name(self) -> str:
        return self.column_name or self.columnName

    def get_masking_algorithm(self) -> str:
        return self.masking_algorithm or self.maskingAlgorithm

    def get_algorithm_params(self) -> Dict[str, Any]:
        return self.algorithm_params or self.algorithmParams or {}


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
    """获取动态脱敏规则列表"""
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
            "errorMessage": r.error_message,
            "createdAt": r.created_at.isoformat() if r.created_at else None,
        } for r in rules],
        total=total,
        page=page,
        page_size=page_size
    ))


@router.get("/rules/{rule_id}", response_model=Response)
def get_dynamic_rule(
    rule_id: int,
    db: DBSession,
    current_user: CurrentUser,
):
    """获取动态脱敏规则详情"""
    from app.models.dynamic_masking import DynamicMaskingRule

    rule = db.get(DynamicMaskingRule, rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="规则不存在")

    return Response(data={
        "id": rule.id,
        "ruleName": rule.rule_name,
        "datasourceId": rule.datasource_id,
        "schemaName": rule.schema_name,
        "tableName": rule.table_name,
        "maskedRoles": rule.masked_roles,
        "exemptedRoles": rule.exempted_roles,
        "status": rule.status,
        "isEnabled": rule.is_enabled,
        "errorMessage": rule.error_message,
        "description": rule.description,
        "createdAt": rule.created_at.isoformat() if rule.created_at else None,
        "columnRules": [{
            "id": col.id,
            "columnName": col.column_name,
            "maskingAlgorithm": col.masking_algorithm,
            "algorithmParams": col.algorithm_params,
        } for col in rule.column_rules]
    })


@router.post("/rules", response_model=Response)
def create_dynamic_rule(
    request: CreateDynamicRuleRequest,
    db: DBSession,
    current_user: CurrentUser,
    audit: AuditLogger,
):
    """创建动态脱敏规则"""
    from app.models.dynamic_masking import DynamicMaskingRule

    rule_name = request.get_rule_name()
    datasource_id = request.get_datasource_id()
    schema_name = request.get_schema_name()
    table_name = request.get_table_name()
    masked_roles = request.get_masked_roles()
    exempted_roles = request.get_exempted_roles()

    if not rule_name:
        raise HTTPException(status_code=400, detail="规则名称不能为空")
    if not datasource_id:
        raise HTTPException(status_code=400, detail="数据源ID不能为空")
    if not table_name:
        raise HTTPException(status_code=400, detail="表名不能为空")
    if not masked_roles:
        raise HTTPException(status_code=400, detail="被脱敏角色列表不能为空")

    rule = DynamicMaskingRule(
        rule_name=rule_name,
        datasource_id=datasource_id,
        schema_name=schema_name,
        table_name=table_name,
        masked_roles=masked_roles,
        exempted_roles=exempted_roles,
        description=request.description,
        created_by=current_user.id,
    )

    db.add(rule)
    db.commit()
    db.refresh(rule)

    audit("CREATE", "dynamic_masking", f"创建动态脱敏规则: {rule_name}")

    return Response(data={
        "id": rule.id,
        "ruleName": rule.rule_name,
        "message": "创建成功，请配置字段脱敏规则"
    })


@router.put("/rules/{rule_id}", response_model=Response)
def update_dynamic_rule(
    rule_id: int,
    request: UpdateDynamicRuleRequest,
    db: DBSession,
    current_user: CurrentUser,
    audit: AuditLogger,
):
    """更新动态脱敏规则"""
    from app.models.dynamic_masking import DynamicMaskingRule

    rule = db.get(DynamicMaskingRule, rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="规则不存在")

    # 只有 DRAFT 状态才能修改
    if rule.status not in ("DRAFT", "INACTIVE"):
        raise HTTPException(status_code=400, detail="已启用的规则不能修改，请先禁用")

    # 更新字段
    if request.rule_name or request.ruleName:
        rule.rule_name = request.rule_name or request.ruleName
    if request.schema_name or request.schemaName:
        rule.schema_name = request.schema_name or request.schemaName
    if request.table_name or request.tableName:
        rule.table_name = request.table_name or request.tableName
    if request.masked_roles or request.maskedRoles:
        rule.masked_roles = request.masked_roles or request.maskedRoles
    if request.exempted_roles or request.exemptedRoles:
        rule.exempted_roles = request.exempted_roles or request.exemptedRoles
    if request.description is not None:
        rule.description = request.description

    # 清除之前的错误信息
    rule.error_message = None

    db.commit()
    db.refresh(rule)

    audit("UPDATE", "dynamic_masking", f"更新动态脱敏规则: {rule.rule_name}")

    return Response(data={
        "id": rule.id,
        "ruleName": rule.rule_name,
        "message": "更新成功"
    })


@router.post("/rules/{rule_id}/columns", response_model=Response)
def add_column_rule(
    rule_id: int,
    request: AddColumnRuleRequest,
    db: DBSession,
    current_user: CurrentUser,
):
    """为动态脱敏规则添加字段脱敏配置"""
    from app.models.dynamic_masking import DynamicMaskingRule, DynamicMaskingColumnRule

    column_name = request.get_column_name()
    masking_algorithm = request.get_masking_algorithm()
    algorithm_params = request.get_algorithm_params()

    if not column_name:
        raise HTTPException(status_code=400, detail="字段名不能为空")
    if not masking_algorithm:
        raise HTTPException(status_code=400, detail="脱敏算法不能为空")

    rule = db.get(DynamicMaskingRule, rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="规则不存在")

    column_rule = DynamicMaskingColumnRule(
        rule_id=rule_id,
        column_name=column_name,
        masking_algorithm=masking_algorithm,
        algorithm_params=algorithm_params,
    )

    db.add(column_rule)
    db.commit()

    return Response(message=f"字段 {column_name} 脱敏规则添加成功")


@router.delete("/rules/{rule_id}/columns/{column_id}", response_model=Response)
def delete_column_rule(
    rule_id: int,
    column_id: int,
    db: DBSession,
    current_user: CurrentUser,
):
    """删除字段规则"""
    from app.models.dynamic_masking import DynamicMaskingColumnRule

    rule = db.get(DynamicMaskingColumnRule, column_id)
    if not rule or rule.rule_id != rule_id:
        raise HTTPException(status_code=404, detail="字段规则不存在")

    db.delete(rule)
    db.commit()

    return Response(message="删除成功")


@router.post("/rules/{rule_id}/enable", response_model=Response)
def enable_dynamic_rule(
    rule_id: int,
    db: DBSession,
    current_user: CurrentUser,
    audit: AuditLogger,
):
    """
    启用动态脱敏规则

    执行操作：
    1. 为表字段设置 SECURITY LABEL
    2. 为角色设置 SECURITY LABEL
    3. 创建脱敏视图
    4. 授权角色
    """
    from app.models.dynamic_masking import DynamicMaskingRule
    from app.models.datasource import DataSource
    from app.services.datasource_service import DataSourceService
    from app.utils.hashdata_anon import HashDataAnonManager, MaskingColumnConfig, MaskingTableConfig

    rule = db.get(DynamicMaskingRule, rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="规则不存在")

    if not rule.column_rules:
        raise HTTPException(status_code=400, detail="请先配置字段脱敏规则")

    datasource = db.get(DataSource, rule.datasource_id)
    if not datasource:
        raise HTTPException(status_code=400, detail="数据源不存在")

    try:
        datasource_config = DataSourceService.get_datasource_config(datasource)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"数据源配置错误: {str(e)}")

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

    table_config = MaskingTableConfig(
        source_table=f"{rule.schema_name}.{rule.table_name}",
        target_table="",
        columns=column_configs,
    )

    masked_role = rule.masked_roles[0] if rule.masked_roles else "masked"

    sql = anon_manager.generate_dynamic_masking_sql(
        table_config,
        source_schema=rule.schema_name,
        masked_role=masked_role,
        exempted_roles=rule.exempted_roles or [],
    )

    # 执行 SQL
    conn = None
    cursor = None
    executed_statements = []

    def split_sql_statements(sql_script: str) -> list:
        """
        智能分割 SQL 语句，正确处理 dollar-quoted 字符串
        """
        statements = []
        current = []
        in_dollar_quote = False
        dollar_tag = None
        lines = sql_script.split('\n')

        for line in lines:
            stripped = line.strip()

            # 跳过注释行
            if stripped.startswith("--"):
                continue

            current.append(line)

            # 检测 dollar-quoted 字符串
            if not in_dollar_quote:
                # 查找 $$ 或 $tag$ 开始
                import re
                match = re.search(r'\$([a-zA-Z_][a-zA-Z0-9_]*)?\$', line)
                if match:
                    in_dollar_quote = True
                    dollar_tag = match.group(0)
                    # 检查同一行是否有结束标签
                    if line.count(dollar_tag) >= 2:
                        in_dollar_quote = False
                        dollar_tag = None
            else:
                # 查找结束标签
                if dollar_tag and dollar_tag in line:
                    in_dollar_quote = False
                    dollar_tag = None

            # 检测语句结束（不在 dollar-quote 中时）
            if not in_dollar_quote and stripped.endswith(";"):
                stmt = '\n'.join(current).strip()
                if stmt and stmt != ";":
                    # 移除行内注释
                    clean_stmt = '\n'.join(
                        ln.split('--')[0].rstrip() if '--' in ln and not ln.strip().startswith('--') else ln
                        for ln in current
                    ).strip()
                    if clean_stmt and clean_stmt != ";":
                        statements.append(clean_stmt)
                current = []

        # 处理最后一个语句（如果没有分号结尾）
        if current:
            stmt = '\n'.join(current).strip()
            if stmt:
                statements.append(stmt)

        return statements

    try:
        import psycopg2
        conn = anon_manager._get_connection(datasource_config)
        cursor = conn.cursor()

        statements = split_sql_statements(sql)
        for statement in statements:
            if statement.strip():
                executed_statements.append(statement)
                logger.info(f"执行SQL: {statement[:200]}...")
                cursor.execute(statement)

        conn.commit()

        # 更新状态
        rule.is_enabled = True
        rule.status = "ACTIVE"
        rule.error_message = None
        db.commit()

        audit("EXECUTE", "dynamic_masking", f"启用动态脱敏规则: {rule.rule_name}")

        return Response(
            message=f"动态脱敏规则已启用，{rule.table_name} 表已配置角色脱敏",
            data={"sql": sql, "executedStatements": len(executed_statements)}
        )

    except Exception as e:
        # 记录详细错误
        error_detail = str(e)
        tb = traceback.format_exc()
        logger.error(f"启用动态脱敏失败: {error_detail}\n{tb}")

        # 记录错误到数据库
        rule.error_message = f"{error_detail}"
        rule.status = "ERROR"
        db.commit()

        if conn:
            conn.rollback()

        # 返回详细错误信息
        return Response(
            code=500,
            message=f"启用失败: {error_detail}",
            data={
                "error": error_detail,
                "sql": sql,
                "executedStatements": len(executed_statements),
                "hint": "请检查表名和字段名是否正确，数据源连接是否正常"
            }
        )

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@router.post("/rules/{rule_id}/disable", response_model=Response)
def disable_dynamic_rule(
    rule_id: int,
    db: DBSession,
    current_user: CurrentUser,
    audit: AuditLogger,
):
    """禁用动态脱敏规则"""
    from app.models.dynamic_masking import DynamicMaskingRule
    from app.models.datasource import DataSource
    from app.services.datasource_service import DataSourceService

    rule = db.get(DynamicMaskingRule, rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="规则不存在")

    datasource = db.get(DataSource, rule.datasource_id)
    if not datasource:
        raise HTTPException(status_code=400, detail="数据源不存在")

    datasource_config = DataSourceService.get_datasource_config(datasource)

    # 生成禁用 SQL
    table_full = f"{rule.schema_name}.{rule.table_name}"
    masked_role = rule.masked_roles[0] if rule.masked_roles else "masked"

    sql_parts = [
        "-- 禁用动态脱敏",
        f"DROP VIEW IF EXISTS {table_full}_masked;",
    ]

    # 移除列的 SECURITY LABEL
    for col_rule in rule.column_rules:
        sql_parts.append(
            f"SECURITY LABEL FOR anon ON COLUMN {table_full}.{col_rule.column_name} IS NULL;"
        )

    # 移除角色的 SECURITY LABEL
    sql_parts.append(f"-- 移除角色的脱敏标记")
    sql_parts.append(f"SECURITY LABEL FOR anon ON ROLE {masked_role} IS NULL;")

    sql = "\n".join(sql_parts)

    conn = None
    cursor = None

    def split_sql_statements(sql_script: str) -> list:
        """智能分割 SQL 语句"""
        statements = []
        for line in sql_script.split('\n'):
            stripped = line.strip()
            if stripped and not stripped.startswith("--"):
                # 简单处理：按分号分割
                if stripped.endswith(";"):
                    statements.append(stripped)
                elif statements:
                    statements[-1] += " " + stripped
                else:
                    statements.append(stripped)
        return statements

    try:
        import psycopg2
        from app.utils.hashdata_anon import HashDataAnonManager
        anon_manager = HashDataAnonManager(datasource_config)
        conn = anon_manager._get_connection(datasource_config)
        cursor = conn.cursor()

        for statement in split_sql_statements(sql):
            if statement.strip():
                cursor.execute(statement)

        conn.commit()

        # 更新状态
        rule.is_enabled = False
        rule.status = "INACTIVE"
        rule.error_message = None
        db.commit()

        audit("EXECUTE", "dynamic_masking", f"禁用动态脱敏规则: {rule.rule_name}")

        return Response(message="动态脱敏规则已禁用")

    except Exception as e:
        error_detail = str(e)
        logger.error(f"禁用动态脱敏失败: {error_detail}")

        if conn:
            conn.rollback()

        rule.error_message = error_detail
        db.commit()

        return Response(
            code=500,
            message=f"禁用失败: {error_detail}",
            data={"error": error_detail, "hint": "角色或表可能已被删除"}
        )

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@router.delete("/rules/{rule_id}", response_model=Response)
def delete_dynamic_rule(
    rule_id: int,
    db: DBSession,
    current_user: CurrentUser,
    audit: AuditLogger,
):
    """删除动态脱敏规则"""
    from app.models.dynamic_masking import DynamicMaskingRule

    rule = db.get(DynamicMaskingRule, rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="规则不存在")

    if rule.is_enabled:
        raise HTTPException(status_code=400, detail="请先禁用规则")

    rule_name = rule.rule_name
    db.delete(rule)
    db.commit()

    audit("DELETE", "dynamic_masking", f"删除动态脱敏规则: {rule_name}")

    return Response(message="删除成功")


@router.get("/rules/{rule_id}/preview-sql", response_model=Response)
def preview_dynamic_rule_sql(
    rule_id: int,
    db: DBSession,
    current_user: CurrentUser,
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
        "schemaName": rule.schema_name,
        "maskedRoles": rule.masked_roles,
        "exemptedRoles": rule.exempted_roles,
        "columnRules": [{"columnName": col.column_name, "maskingAlgorithm": col.masking_algorithm} for col in rule.column_rules]
    })
