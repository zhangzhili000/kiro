from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from collections import deque

from kiro_knbase.models.document import Document
from kiro_knbase.models.category import Category, Tag
from kiro_platform.models.user import User
from kiro_knbase.schemas.knowledge_graph import (
    GraphData, GraphNode, GraphEdge, PathNode, PathEdge, ShortestPathResponse
)


def build_knowledge_graph(db: Session, max_nodes: int = 500) -> GraphData:
    """构建知识图谱数据"""
    nodes = []
    edges = []
    node_id_map = {}

    # 1. 添加文档节点
    documents = db.query(Document).filter(Document.is_deleted == False).limit(max_nodes // 2).all()
    for doc in documents:
        node_id = f"doc_{doc.id}"
        nodes.append(GraphNode(
            id=node_id,
            label=doc.title,
            type="document",
            properties={
                "id": doc.id,
                "title": doc.title,
                "status": doc.status,
                "view_count": doc.view_count,
                "created_at": doc.created_at.isoformat() if doc.created_at else None
            }
        ))
        node_id_map[doc.id] = node_id

    # 2. 添加分类节点
    categories = db.query(Category).all()
    for cat in categories:
        node_id = f"cat_{cat.id}"
        nodes.append(GraphNode(
            id=node_id,
            label=cat.name,
            type="category",
            properties={
                "id": cat.id,
                "name": cat.name,
                "description": cat.description
            }
        ))
        node_id_map[f"cat_{cat.id}"] = node_id

    # 3. 添加标签节点
    tags = db.query(Tag).all()
    for tag in tags:
        node_id = f"tag_{tag.id}"
        nodes.append(GraphNode(
            id=node_id,
            label=tag.name,
            type="tag",
            properties={
                "id": tag.id,
                "name": tag.name
            }
        ))
        node_id_map[f"tag_{tag.id}"] = node_id

    # 4. 添加用户节点
    users = db.query(User).filter(User.is_active == True).all()
    for user in users:
        node_id = f"user_{user.id}"
        nodes.append(GraphNode(
            id=node_id,
            label=user.username,
            type="user",
            properties={
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role
            }
        ))
        node_id_map[f"user_{user.id}"] = node_id

    # 5. 添加关系边
    edge_id = 0

    # 分类包含文档的关系
    for doc in documents:
        if doc.category_id:
            cat_node_id = f"cat_{doc.category_id}"
            doc_node_id = node_id_map.get(doc.id)
            if cat_node_id in node_id_map.values() and doc_node_id:
                edges.append(GraphEdge(
                    id=f"edge_{edge_id}",
                    source=cat_node_id,
                    target=doc_node_id,
                    label="包含",
                    type="CONTAINS",
                    properties={}
                ))
                edge_id += 1

    # 文档标记标签的关系
    for doc in documents:
        doc_node_id = node_id_map.get(doc.id)
        if doc_node_id and doc.tags:
            for doc_tag in doc.tags:
                tag = doc_tag.tag
                if tag:
                    tag_node_id = f"tag_{tag.id}"
                    if tag_node_id in node_id_map.values():
                        edges.append(GraphEdge(
                            id=f"edge_{edge_id}",
                            source=doc_node_id,
                            target=tag_node_id,
                            label="标记",
                            type="TAGGED",
                            properties={}
                        ))
                        edge_id += 1

    # 用户创作文档的关系
    for doc in documents:
        doc_node_id = node_id_map.get(doc.id)
        user_node_id = f"user_{doc.author_id}"
        if doc_node_id and user_node_id in node_id_map.values():
            edges.append(GraphEdge(
                id=f"edge_{edge_id}",
                source=user_node_id,
                target=doc_node_id,
                label="创作",
                type="AUTHORED",
                properties={}
            ))
            edge_id += 1

    return GraphData(nodes=nodes, edges=edges)


def find_shortest_path(db: Session, source_id: str, target_id: str, max_depth: int = 5) -> Optional[ShortestPathResponse]:
    """查找两个节点之间的最短路径"""
    graph_data = build_knowledge_graph(db)

    # 构建邻接表
    adj = {}
    for edge in graph_data.edges:
        if edge.source not in adj:
            adj[edge.source] = []
        if edge.target not in adj:
            adj[edge.target] = []
        adj[edge.source].append((edge.target, edge))
        adj[edge.target].append((edge.source, edge))

    # BFS 查找最短路径
    queue = deque([(source_id, [])])
    visited = {source_id}

    while queue:
        current, path = queue.popleft()

        if current == target_id:
            # 构建响应
            path_nodes = []
            path_edges = []

            for node_id in path + [current]:
                node = next((n for n in graph_data.nodes if n.id == node_id), None)
                if node:
                    path_nodes.append(PathNode(id=node.id, label=node.label, type=node.type))

            for i in range(len(path)):
                edge = next((e for e in graph_data.edges 
                           if (e.source == path[i] and e.target == path[i+1]) or 
                              (e.source == path[i+1] and e.target == path[i])), None)
                if edge:
                    path_edges.append(PathEdge(source=edge.source, target=edge.target, label=edge.label))

            return ShortestPathResponse(
                path=path_nodes,
                edges=path_edges,
                length=len(path)
            )

        if len(path) >= max_depth:
            continue

        for neighbor, edge in adj.get(current, []):
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append((neighbor, path + [current]))

    return None


def get_related_nodes(db: Session, node_id: str, max_depth: int = 2, node_types: Optional[List[str]] = None) -> GraphData:
    """获取相关节点"""
    graph_data = build_knowledge_graph(db)

    # 构建邻接表
    adj = {}
    for edge in graph_data.edges:
        if edge.source not in adj:
            adj[edge.source] = []
        if edge.target not in adj:
            adj[edge.target] = []
        adj[edge.source].append((edge.target, edge))
        adj[edge.target].append((edge.source, edge))

    # BFS 获取相关节点
    queue = deque([(node_id, 0)])
    visited = {node_id}
    related_nodes = []
    related_edges = []

    while queue:
        current, depth = queue.popleft()

        if depth >= max_depth:
            continue

        for neighbor, edge in adj.get(current, []):
            if neighbor not in visited:
                visited.add(neighbor)
                
                # 检查节点类型
                node = next((n for n in graph_data.nodes if n.id == neighbor), None)
                if node and (not node_types or node.type in node_types):
                    related_nodes.append(node)
                    related_edges.append(edge)
                    queue.append((neighbor, depth + 1))

    return GraphData(nodes=related_nodes, edges=related_edges)