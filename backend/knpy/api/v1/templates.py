from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from knpy.core.database import get_db
from knpy.api.v1.users import get_current_user
from knpy.models.user import User
from knpy.schemas.document_template import (
    DocumentTemplateCreate,
    DocumentTemplateUpdate,
    DocumentTemplateResponse
)
from knpy.services.document_template_service import (
    get_templates,
    get_template,
    create_template,
    update_template,
    delete_template
)

router = APIRouter(prefix="/templates", tags=["文档模板"])


@router.get("", response_model=List[DocumentTemplateResponse])
def list_templates(
    category_id: Optional[int] = Query(None),
    is_public: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取文档模板列表"""
    return get_templates(db, category_id=category_id, is_public=is_public)


@router.get("/{template_id}", response_model=DocumentTemplateResponse)
def get_template_detail(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取模板详情"""
    template = get_template(db, template_id)
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    return template


@router.post("", response_model=DocumentTemplateResponse)
def create_document_template(
    template: DocumentTemplateCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建文档模板"""
    return create_template(db, template, current_user.id)


@router.put("/{template_id}", response_model=DocumentTemplateResponse)
def update_document_template(
    template_id: int,
    template_update: DocumentTemplateUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新文档模板"""
    template = update_template(db, template_id, template_update)
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    return template


@router.delete("/{template_id}")
def delete_document_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除文档模板"""
    success = delete_template(db, template_id)
    if not success:
        raise HTTPException(status_code=404, detail="模板不存在")
    return {"message": "模板已删除"}