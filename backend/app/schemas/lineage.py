"""
血缘分析相关Schema
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class LineageNode(BaseModel):
    """血缘节点"""

    id: str = Field(..., description="节点ID")
    name: str = Field(..., description="节点名称")
    type: str = Field(..., description="节点类型：TABLE/COLUMN")
    datasource_id: Optional[int] = Field(default=None, description="数据源ID")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="元数据")


class LineageEdge(BaseModel):
    """血缘边"""

    id: str = Field(..., description="边ID")
    source: str = Field(..., description="源节点ID")
    target: str = Field(..., description="目标节点ID")
    type: str = Field(default="TRANSFORM", description="关系类型")
    transform_logic: Optional[str] = Field(default=None, description="转换逻辑")


class LineageGraph(BaseModel):
    """血缘图谱"""

    nodes: List[LineageNode] = Field(default_factory=list, description="节点列表")
    edges: List[LineageEdge] = Field(default_factory=list, description="边列表")


class LineageAnalysisRequest(BaseModel):
    """血缘分析请求"""

    datasource_id: int = Field(..., description="数据源ID")
    node_type: Optional[str] = Field(default="TABLE", description="节点类型")
    start_node: Optional[str] = Field(default=None, description="起始节点")
    depth: int = Field(default=3, ge=1, le=10, description="分析深度")
    direction: str = Field(default="BOTH", description="方向：UPSTREAM/DOWNSTREAM/BOTH")
