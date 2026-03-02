"""
血缘分析API
"""
from typing import Optional, List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.common import Response
from app.schemas.lineage import (
    LineageGraph,
    LineageAnalysisRequest,
)
from app.api.deps import CurrentUser, DBSession, AuditLogger

router = APIRouter()


@router.get("/graph", response_model=Response[LineageGraph])
def get_lineage_graph(
    datasource_id: Optional[int] = None,
    node_type: Optional[str] = "TABLE",
    db: Session = Depends(get_db),
    current_user: CurrentUser = None,
):
    """获取血缘图谱"""
    # 演示数据
    graph = LineageGraph(
        nodes=[
            {"id": "node1", "name": "customer", "type": "TABLE", "datasource_id": datasource_id},
            {"id": "node2", "name": "customer_masked", "type": "TABLE", "datasource_id": datasource_id},
            {"id": "node3", "name": "orders", "type": "TABLE", "datasource_id": datasource_id},
        ],
        edges=[
            {"id": "e1", "source": "node1", "target": "node2", "type": "TRANSFORM", "transform_logic": "脱敏处理"},
            {"id": "e2", "source": "node1", "target": "node3", "type": "JOIN", "transform_logic": "关联订单"},
        ]
    )
    return Response(data=graph)


@router.post("/analysis", response_model=Response[LineageGraph])
def analyze_lineage(
    request: LineageAnalysisRequest,
    db: Session = Depends(get_db),
    current_user: CurrentUser = None,
    audit: AuditLogger = None,
):
    """执行血缘分析"""
    audit("EXECUTE", "lineage", f"执行血缘分析: 数据源ID={request.datasource_id}")

    # 演示实现
    graph = LineageGraph(
        nodes=[
            {"id": "start_node", "name": request.start_node or "source_table", "type": request.node_type, "datasource_id": request.datasource_id},
            {"id": "target_node", "name": "target_table", "type": request.node_type, "datasource_id": request.datasource_id},
        ],
        edges=[
            {"id": "e1", "source": "start_node", "target": "target_node", "type": "TRANSFORM", "transform_logic": "数据流转"},
        ]
    )
    return Response(data=graph)
