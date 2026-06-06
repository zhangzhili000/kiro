from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from knpy.core.database import get_db
from knpy.api.v1.users import get_current_user
from knpy.models.user import User
from knpy.models.team import Team, TeamMember, TeamDocument
from knpy.models.document import Document
from knpy.schemas.team import (
    TeamCreate, TeamUpdate, TeamResponse, TeamMemberResponse, TeamDocumentResponse
)

router = APIRouter(prefix="/teams", tags=["团队知识库"])


@router.get("", response_model=List[TeamResponse])
def list_teams(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取用户所属的团队列表"""
    member_teams = db.query(TeamMember).filter(TeamMember.user_id == current_user.id).all()
    team_ids = [mt.team_id for mt in member_teams]
    return db.query(Team).filter(Team.id.in_(team_ids), Team.is_active == True).all()


@router.get("/{team_id}", response_model=TeamResponse)
def get_team(
    team_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取团队详情"""
    team = db.query(Team).filter(Team.id == team_id, Team.is_active == True).first()
    if not team:
        raise HTTPException(status_code=404, detail="团队不存在")
    
    # 验证用户是否属于该团队
    member = db.query(TeamMember).filter(
        TeamMember.team_id == team_id,
        TeamMember.user_id == current_user.id
    ).first()
    if not member:
        raise HTTPException(status_code=403, detail="无权限访问该团队")
    
    return team


@router.post("", response_model=TeamResponse)
def create_team(
    team: TeamCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建团队"""
    db_team = Team(
        name=team.name,
        description=team.description,
        icon=team.icon
    )
    db.add(db_team)
    db.commit()
    db.refresh(db_team)
    
    # 添加创建者为团队成员（owner）
    member = TeamMember(
        team_id=db_team.id,
        user_id=current_user.id,
        role="owner"
    )
    db.add(member)
    db.commit()
    
    return db_team


@router.put("/{team_id}", response_model=TeamResponse)
def update_team(
    team_id: int,
    team_update: TeamUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新团队信息"""
    team = db.query(Team).filter(Team.id == team_id, Team.is_active == True).first()
    if not team:
        raise HTTPException(status_code=404, detail="团队不存在")
    
    # 验证用户是否为团队管理员
    member = db.query(TeamMember).filter(
        TeamMember.team_id == team_id,
        TeamMember.user_id == current_user.id
    ).first()
    if not member or member.role not in ["owner", "admin"]:
        raise HTTPException(status_code=403, detail="无权限修改团队")
    
    update_data = team_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(team, key, value)
    
    db.commit()
    db.refresh(team)
    return team


@router.delete("/{team_id}")
def delete_team(
    team_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除团队"""
    team = db.query(Team).filter(Team.id == team_id, Team.is_active == True).first()
    if not team:
        raise HTTPException(status_code=404, detail="团队不存在")
    
    # 验证用户是否为团队所有者
    member = db.query(TeamMember).filter(
        TeamMember.team_id == team_id,
        TeamMember.user_id == current_user.id
    ).first()
    if not member or member.role != "owner":
        raise HTTPException(status_code=403, detail="只有所有者可以删除团队")
    
    team.is_active = False
    db.commit()
    return {"message": "团队已删除"}


@router.get("/{team_id}/members", response_model=List[TeamMemberResponse])
def list_team_members(
    team_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取团队成员列表"""
    # 验证用户是否属于该团队
    member = db.query(TeamMember).filter(
        TeamMember.team_id == team_id,
        TeamMember.user_id == current_user.id
    ).first()
    if not member:
        raise HTTPException(status_code=403, detail="无权限访问该团队")
    
    return db.query(TeamMember).filter(TeamMember.team_id == team_id).all()


@router.post("/{team_id}/members")
def add_team_member(
    team_id: int,
    user_id: int,
    role: str = "member",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """添加团队成员"""
    team = db.query(Team).filter(Team.id == team_id, Team.is_active == True).first()
    if not team:
        raise HTTPException(status_code=404, detail="团队不存在")
    
    # 验证用户是否为团队管理员
    member = db.query(TeamMember).filter(
        TeamMember.team_id == team_id,
        TeamMember.user_id == current_user.id
    ).first()
    if not member or member.role not in ["owner", "admin"]:
        raise HTTPException(status_code=403, detail="无权限添加成员")
    
    # 检查用户是否已在团队中
    existing_member = db.query(TeamMember).filter(
        TeamMember.team_id == team_id,
        TeamMember.user_id == user_id
    ).first()
    if existing_member:
        raise HTTPException(status_code=400, detail="用户已在团队中")
    
    new_member = TeamMember(
        team_id=team_id,
        user_id=user_id,
        role=role
    )
    db.add(new_member)
    db.commit()
    return {"message": "成员已添加"}


@router.delete("/{team_id}/members/{user_id}")
def remove_team_member(
    team_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """移除团队成员"""
    member = db.query(TeamMember).filter(
        TeamMember.team_id == team_id,
        TeamMember.user_id == user_id
    ).first()
    if not member:
        raise HTTPException(status_code=404, detail="成员不存在")
    
    # 验证用户是否有权限移除
    current_member = db.query(TeamMember).filter(
        TeamMember.team_id == team_id,
        TeamMember.user_id == current_user.id
    ).first()
    if not current_member or (current_member.role not in ["owner", "admin"] and current_user.id != user_id):
        raise HTTPException(status_code=403, detail="无权限移除成员")
    
    db.delete(member)
    db.commit()
    return {"message": "成员已移除"}


@router.get("/{team_id}/documents", response_model=List[dict])
def list_team_documents(
    team_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取团队文档列表"""
    member = db.query(TeamMember).filter(
        TeamMember.team_id == team_id,
        TeamMember.user_id == current_user.id
    ).first()
    if not member:
        raise HTTPException(status_code=403, detail="无权限访问该团队")
    
    team_docs = db.query(TeamDocument).filter(TeamDocument.team_id == team_id).all()
    doc_ids = [td.document_id for td in team_docs]
    documents = db.query(Document).filter(Document.id.in_(doc_ids), Document.is_deleted == False).all()
    
    results = []
    for doc in documents:
        results.append({
            "id": doc.id,
            "title": doc.title,
            "author_id": doc.author_id,
            "category_id": doc.category_id,
            "view_count": doc.view_count,
            "created_at": doc.created_at,
            "updated_at": doc.updated_at
        })
    
    return results


@router.post("/{team_id}/documents")
def add_team_document(
    team_id: int,
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """添加文档到团队"""
    team = db.query(Team).filter(Team.id == team_id, Team.is_active == True).first()
    if not team:
        raise HTTPException(status_code=404, detail="团队不存在")
    
    document = db.query(Document).filter(Document.id == document_id, Document.is_deleted == False).first()
    if not document:
        raise HTTPException(status_code=404, detail="文档不存在")
    
    # 验证用户是否为团队成员
    member = db.query(TeamMember).filter(
        TeamMember.team_id == team_id,
        TeamMember.user_id == current_user.id
    ).first()
    if not member:
        raise HTTPException(status_code=403, detail="无权限访问该团队")
    
    # 检查文档是否已在团队中
    existing = db.query(TeamDocument).filter(
        TeamDocument.team_id == team_id,
        TeamDocument.document_id == document_id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="文档已在团队中")
    
    team_doc = TeamDocument(
        team_id=team_id,
        document_id=document_id,
        added_by=current_user.id
    )
    db.add(team_doc)
    db.commit()
    return {"message": "文档已添加到团队"}


@router.delete("/{team_id}/documents/{document_id}")
def remove_team_document(
    team_id: int,
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """从团队中移除文档"""
    team_doc = db.query(TeamDocument).filter(
        TeamDocument.team_id == team_id,
        TeamDocument.document_id == document_id
    ).first()
    if not team_doc:
        raise HTTPException(status_code=404, detail="文档不在团队中")
    
    # 验证用户是否有权限移除
    member = db.query(TeamMember).filter(
        TeamMember.team_id == team_id,
        TeamMember.user_id == current_user.id
    ).first()
    if not member or member.role not in ["owner", "admin"]:
        raise HTTPException(status_code=403, detail="无权限移除文档")
    
    db.delete(team_doc)
    db.commit()
    return {"message": "文档已从团队移除"}