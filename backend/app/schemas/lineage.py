"""
血缘分析相关Schema
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime


class LineageNode(BaseModel):
    """血缘节点"""

    id: str = Field(..., description="节点ID")
    name: str = Field(..., description="节点名称")
    type: str = Field(default="TABLE", description="节点类型：TABLE/COLUMN")
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


class LineageRelationCreate(BaseModel):
    """创建血缘关系"""

    datasource_id: int = Field(..., description="数据源ID")
    source_node: str = Field(..., min_length=1, max_length=512, description="源节点")
    target_node: str = Field(..., min_length=1, max_length=512, description="目标节点")
    relation_type: str = Field(default="TRANSFORM", description="关系类型")
    transform_logic: Optional[str] = Field(default=None, max_length=2000, description="转换逻辑")


class LineageRelationResponse(BaseModel):
    """血缘关系响应"""

    id: int
    datasource_id: int
    lineage_type: Optional[str] = None
    source_node: str
    target_node: str
    relation_type: Optional[str] = None
    transform_logic: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class LineageScanResult(BaseModel):
    """血缘扫描结果"""

    success: bool = Field(..., description="是否成功")
    relations_found: int = Field(default=0, description="发现的关系数")
    relations_saved: int = Field(default=0, description="保存的关系数")
    errors: List[str] = Field(default_factory=list, description="错误信息")


class ImpactAnalysisRequest(BaseModel):
    """影响分析请求"""

    datasource_id: int = Field(..., description="数据源ID")
    node_name: str = Field(..., description="节点名称")
    depth: int = Field(default=3, ge=1, le=10, description="分析深度")
