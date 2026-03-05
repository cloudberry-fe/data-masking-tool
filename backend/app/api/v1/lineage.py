"""
血缘分析API
"""
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.common import Response, PageResponse
from app.schemas.lineage import (
    LineageGraph,
    LineageAnalysisRequest,
    LineageRelationCreate,
    LineageRelationResponse,
    LineageScanResult,
    ImpactAnalysisRequest,
)
from app.services.lineage_service import LineageService
from app.api.deps import CurrentUser, DBSession, AuditLogger

router = APIRouter()


@router.get("/graph", response_model=Response[LineageGraph])
def get_lineage_graph(
    db: DBSession,
    current_user: CurrentUser,
    datasource_id: Optional[int] = None,
    node_name: Optional[str] = None,
    depth: int = 3,
    direction: str = "BOTH",
):
    """获取血缘图谱"""
    graph = LineageService.get_lineage_graph(
        db, datasource_id, node_name, depth, direction
    )
    return Response(data=LineageGraph(**graph))


@router.post("/scan", response_model=Response[LineageScanResult])
def scan_datasource(
    datasource_id: int,
    db: DBSession,
    current_user: CurrentUser,
    audit: AuditLogger,
):
    """扫描数据源，自动提取血缘关系"""
    result = LineageService.scan_datasource(db, datasource_id)

    audit("SCAN", "lineage", f"扫描数据源血缘: 数据源ID={datasource_id}")

    return Response(
        data=LineageScanResult(**result),
        message="扫描完成" if result["success"] else "扫描失败"
    )


@router.post("/relations", response_model=Response[LineageRelationResponse])
def add_relation(
    request: LineageRelationCreate,
    db: DBSession,
    current_user: CurrentUser,
    audit: AuditLogger,
):
    """手动添加血缘关系"""
    lineage = LineageService.add_relation(
        db,
        request.datasource_id,
        request.source_node,
        request.target_node,
        request.relation_type,
        request.transform_logic
    )

    audit("CREATE", "lineage", f"添加血缘关系: {request.source_node} -> {request.target_node}")

    return Response(data=LineageRelationResponse.model_validate(lineage), message="添加成功")


@router.get("/relations", response_model=Response[List[LineageRelationResponse]])
def get_relations(
    db: DBSession,
    current_user: CurrentUser,
    datasource_id: Optional[int] = None,
):
    """获取血缘关系列表"""
    from sqlalchemy import select
    from app.models.lineage import DataLineage

    query = select(DataLineage)
    if datasource_id:
        query = query.where(DataLineage.datasource_id == datasource_id)

    lineages = db.scalars(query).all()
    return Response(data=[LineageRelationResponse.model_validate(l) for l in lineages])


@router.delete("/relations/{lineage_id}", response_model=Response)
def delete_relation(
    lineage_id: int,
    db: DBSession,
    current_user: CurrentUser,
    audit: AuditLogger,
):
    """删除血缘关系"""
    success = LineageService.delete_relation(db, lineage_id)

    if not success:
        raise HTTPException(status_code=404, detail="血缘关系不存在")

    audit("DELETE", "lineage", f"删除血缘关系: ID={lineage_id}")
    return Response(message="删除成功")


@router.post("/impact", response_model=Response[LineageGraph])
def analyze_impact(
    request: ImpactAnalysisRequest,
    db: DBSession,
    current_user: CurrentUser,
    audit: AuditLogger,
):
    """影响分析 - 查找所有下游节点"""
    audit("ANALYZE", "lineage", f"影响分析: {request.node_name}")

    graph = LineageService.analyze_impact(
        db, request.datasource_id, request.node_name, request.depth
    )
    return Response(data=LineageGraph(**graph))


@router.post("/source", response_model=Response[LineageGraph])
def analyze_source(
    request: ImpactAnalysisRequest,
    db: DBSession,
    current_user: CurrentUser,
    audit: AuditLogger,
):
    """来源分析 - 查找所有上游节点"""
    audit("ANALYZE", "lineage", f"来源分析: {request.node_name}")

    graph = LineageService.analyze_source(
        db, request.datasource_id, request.node_name, request.depth
    )
    return Response(data=LineageGraph(**graph))


@router.delete("/clear/{datasource_id}", response_model=Response)
def clear_lineages(
    datasource_id: int,
    db: DBSession,
    current_user: CurrentUser,
    audit: AuditLogger,
):
    """清除数据源的所有血缘关系"""
    count = LineageService.clear_lineages(db, datasource_id)

    audit("DELETE", "lineage", f"清除数据源血缘关系: 数据源ID={datasource_id}, 数量={count}")
    return Response(message=f"已删除 {count} 条血缘关系")
