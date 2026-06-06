from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from knpy.core.database import get_db
from knpy.api.v1.users import get_current_user
from knpy.models.user import User
from knpy.schemas.knowledge_graph import (
    GraphData, ShortestPathRequest, ShortestPathResponse, RelatedNodesRequest
)
from knpy.services.knowledge_graph_service import (
    build_knowledge_graph, find_shortest_path, get_related_nodes
)

router = APIRouter(prefix="/knowledge-graph", tags=["知识图谱"])


@router.get("", response_model=GraphData)
def get_graph(
    max_nodes: int = Query(500, ge=10, le=2000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取知识图谱数据"""
    return build_knowledge_graph(db, max_nodes=max_nodes)


@router.get("/nodes")
def get_nodes(
    node_type: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取节点列表"""
    graph_data = build_knowledge_graph(db)
    
    if node_type:
        nodes = [node for node in graph_data.nodes if node.type == node_type]
    else:
        nodes = graph_data.nodes
    
    return {"nodes": nodes, "total": len(nodes)}


@router.get("/edges")
def get_edges(
    edge_type: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取关系列表"""
    graph_data = build_knowledge_graph(db)
    
    if edge_type:
        edges = [edge for edge in graph_data.edges if edge.type == edge_type]
    else:
        edges = graph_data.edges
    
    return {"edges": edges, "total": len(edges)}


@router.post("/shortest-path", response_model=ShortestPathResponse)
def get_shortest_path(
    request: ShortestPathRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """查找两个节点之间的最短路径"""
    result = find_shortest_path(
        db, 
        source_id=request.source_id, 
        target_id=request.target_id, 
        max_depth=request.max_depth
    )
    
    if not result:
        raise HTTPException(status_code=404, detail="未找到路径")
    
    return result


@router.post("/related-nodes", response_model=GraphData)
def get_related(
    request: RelatedNodesRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取相关节点"""
    return get_related_nodes(
        db,
        node_id=request.node_id,
        max_depth=request.max_depth,
        node_types=request.node_types
    )