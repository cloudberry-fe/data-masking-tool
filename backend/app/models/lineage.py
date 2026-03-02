"""
数据血缘相关数据模型
"""
from sqlalchemy import (
    Column,
    BigInteger,
    String,
    Text,
    DateTime,
    ForeignKey,
    func,
)
from sqlalchemy.orm import relationship

from app.core.database import Base


class DataLineage(Base):
    """数据表"""

    __tablename__ = "data_lineage"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="ID")
    datasource_id = Column(BigInteger, ForeignKey("datasource.id"), nullable=False, index=True, comment="数据源ID")
    lineage_type = Column(String(32), comment="血缘类型")
    source_node = Column(String(512), comment="源节点")
    target_node = Column(String(512), comment="目标节点")
    relation_type = Column(String(32), comment="关系类型")
    transform_logic = Column(Text, comment="转换逻辑")
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")

    # 关联
    datasource = relationship("DataSource", back_populates="lineages")
