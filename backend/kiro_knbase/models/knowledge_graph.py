"""
知识图谱模型
"""
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Enum, Float
from sqlalchemy.orm import relationship
from datetime import datetime
from kiro_platform.core.timezone_utils import get_beijing_time
from kiro_platform.core.database import Base


class KnowledgeGraphNode(Base):
    """知识图谱节点"""
    __tablename__ = "knowledge_graph_nodes"
    
    id = Column(Integer, primary_key=True, index=True)
    node_type = Column(Enum("document", "concept", "entity", "event", name="node_type_enum"), nullable=False)
    title = Column(String(500), nullable=False)
    description = Column(Text)
    document_id = Column(Integer, ForeignKey("documents.id"))
    embedding = Column(Text)  # 向量嵌入，用于相似度计算
    created_at = Column(DateTime, default=get_beijing_time)
    
    document = relationship("Document", back_populates="graph_node")
    relations_as_source = relationship("KnowledgeGraphRelation", foreign_keys="KnowledgeGraphRelation.source_node_id", back_populates="source_node")
    relations_as_target = relationship("KnowledgeGraphRelation", foreign_keys="KnowledgeGraphRelation.target_node_id", back_populates="target_node")


class KnowledgeGraphRelation(Base):
    """知识图谱关系"""
    __tablename__ = "knowledge_graph_relations"
    
    id = Column(Integer, primary_key=True, index=True)
    source_node_id = Column(Integer, ForeignKey("knowledge_graph_nodes.id"), nullable=False)
    target_node_id = Column(Integer, ForeignKey("knowledge_graph_nodes.id"), nullable=False)
    relation_type = Column(Enum("related_to", "contains", "references", "derived_from", "similar_to", name="relation_type_enum"), nullable=False)
    confidence = Column(Float, default=1.0)  # 关系置信度 0-1
    created_at = Column(DateTime, default=get_beijing_time)
    
    source_node = relationship("KnowledgeGraphNode", foreign_keys=[source_node_id], back_populates="relations_as_source")
    target_node = relationship("KnowledgeGraphNode", foreign_keys=[target_node_id], back_populates="relations_as_target")
