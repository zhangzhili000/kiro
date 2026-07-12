from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Optional

from kiro_platform.core.database import get_db
from ...schemas.document import (
    DocumentCreate, DocumentUpdate, DocumentResponse, DocumentListResponse,
    DocumentVersionResponse, DocumentDownloadRequest, DocumentIndexStatusResponse
)
from ...models import Document, DocumentVersion, DocumentShare, DocumentTag
from kiro_platform.models import UserFavorite, DocumentLike, User
from kiro_platform.api.v1.users import get_current_user
from ...services.document_permission_service import (
    check_document_view_permission,
    check_document_edit_permission,
    check_document_delete_permission,
    get_documents_with_view_permission
)

router = APIRouter(prefix="/documents", tags=["文档"])


@router.get("", response_model=List[DocumentListResponse])
def list_documents(
    page: int = 1,
    page_size: int = 20,
    category_id: Optional[int] = None,
    tag_id: Optional[int] = None,
    permission: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 获取用户有权限查看的文档
    accessible_docs = get_documents_with_view_permission(db, current_user.id)
    accessible_doc_ids = {doc.id for doc in accessible_docs}
    
    # 获取用户创建的文档
    author_docs = db.query(Document).filter(
        Document.author_id == current_user.id,
        Document.is_deleted == False
    ).all()
    author_doc_ids = {doc.id for doc in author_docs}
    
    # 获取公开文档
    public_docs = db.query(Document).filter(
        Document.permission == "public",
        Document.is_deleted == False
    ).all()
    public_doc_ids = {doc.id for doc in public_docs}
    
    # 合并所有可访问的文档ID
    all_accessible_ids = accessible_doc_ids | author_doc_ids | public_doc_ids
    
    query = db.query(Document).filter(
        Document.id.in_(all_accessible_ids),
        Document.is_deleted == False
    )
    
    if category_id:
        query = query.filter(Document.category_id == category_id)
    if permission:
        query = query.filter(Document.permission == permission)

    query = query.order_by(Document.updated_at.desc())
    offset = (page - 1) * page_size
    documents = query.offset(offset).limit(page_size).all()

    result = []
    for doc in documents:
        author_name = None
        if doc.author_id:
            author = db.query(User).filter(User.id == doc.author_id).first()
            author_name = author.username if author else None

        category_name = None
        if doc.category_id:
            from kiro_knbase.models.category import Category
            category = db.query(Category).filter(Category.id == doc.category_id).first()
            category_name = category.name if category else None

        result.append({
            "id": doc.id,
            "title": doc.title,
            "author_id": doc.author_id,
            "author_name": author_name,
            "category_id": doc.category_id,
            "category_name": category_name,
            "permission": doc.permission,
            "view_count": doc.view_count,
            "like_count": doc.like_count,
            "comment_count": doc.comment_count,
            "created_at": doc.created_at,
            "updated_at": doc.updated_at
        })

    return result


@router.get("/trash", response_model=List[DocumentListResponse])
def list_trash(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # 显示用户自己删除的文档，以及用户创建的并且被删除的文档
    documents = db.query(Document).filter(
        Document.is_deleted == True,
        or_(
            Document.author_id == current_user.id,  # 用户创建的文档
            Document.deleted_by == current_user.id  # 用户删除的文档
        )
    ).all()

    result = []
    for doc in documents:
        author_name = None
        if doc.author_id:
            author = db.query(User).filter(User.id == doc.author_id).first()
            author_name = author.username if author else None

        category_name = None
        if doc.category_id:
            from kiro_knbase.models.category import Category
            category = db.query(Category).filter(Category.id == doc.category_id).first()
            category_name = category.name if category else None

        result.append({
            "id": doc.id,
            "title": doc.title,
            "author_id": doc.author_id,
            "author_name": author_name,
            "category_id": doc.category_id,
            "category_name": category_name,
            "permission": doc.permission,
            "view_count": doc.view_count,
            "like_count": doc.like_count,
            "comment_count": doc.comment_count,
            "created_at": doc.created_at,
            "updated_at": doc.updated_at
        })

    return result


@router.get("/{document_id}", response_model=DocumentResponse)
def get_document(document_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="文档不存在")

    # 检查权限
    if not check_document_view_permission(db, document_id, current_user.id):
        raise HTTPException(status_code=403, detail="无权限查看该文档")

    document.view_count += 1
    db.commit()

    author_name = None
    if document.author_id:
        author = db.query(User).filter(User.id == document.author_id).first()
        author_name = author.username if author else None

    category_name = None
    if document.category_id:
        from kiro_knbase.models.category import Category
        category = db.query(Category).filter(Category.id == document.category_id).first()
        category_name = category.name if category else None

    tags = []
    document_tags = db.query(DocumentTag).filter(DocumentTag.document_id == document.id).all()
    for doc_tag in document_tags:
        from kiro_knbase.models.category import Tag
        tag = db.query(Tag).filter(Tag.id == doc_tag.tag_id).first()
        if tag:
            tags.append(tag.name)

    result = {
        "id": document.id,
        "title": document.title,
        "content": document.content,
        "html_content": document.html_content,
        "author_id": document.author_id,
        "author_name": author_name,
        "category_id": document.category_id,
        "category_name": category_name,
        "permission": document.permission,
        "view_count": document.view_count,
        "like_count": document.like_count,
        "comment_count": document.comment_count,
        "is_deleted": document.is_deleted,
        "deleted_at": document.deleted_at,
        "created_at": document.created_at,
        "updated_at": document.updated_at,
        "tags": tags
    }

    return result


@router.post("", response_model=DocumentResponse)
def create_document(document: DocumentCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    doc_data = document.model_dump(exclude={"tag_ids"})
    db_document = Document(**doc_data, author_id=current_user.id, status="draft")
    db.add(db_document)
    db.commit()
    db.refresh(db_document)

    if document.tag_ids:
        for tag_id in document.tag_ids:
            doc_tag = DocumentTag(document_id=db_document.id, tag_id=tag_id)
            db.add(doc_tag)
        db.commit()

    # 异步创建索引
    from kiro_knbase.services.async_task_service import async_task_service
    async_task_service.create_document_index(db_document.id)

    author_name = current_user.username
    category_name = None
    if db_document.category_id:
        from kiro_knbase.models.category import Category
        category = db.query(Category).filter(Category.id == db_document.category_id).first()
        category_name = category.name if category else None

    tags = []
    if document.tag_ids:
        for tag_id in document.tag_ids:
            from kiro_knbase.models.category import Tag
            tag = db.query(Tag).filter(Tag.id == tag_id).first()
            if tag:
                tags.append(tag.name)

    result = {
        "id": db_document.id,
        "title": db_document.title,
        "content": db_document.content,
        "html_content": db_document.html_content,
        "author_id": db_document.author_id,
        "author_name": author_name,
        "category_id": db_document.category_id,
        "category_name": category_name,
        "permission": db_document.permission,
        "view_count": db_document.view_count,
        "like_count": db_document.like_count,
        "comment_count": db_document.comment_count,
        "is_deleted": db_document.is_deleted,
        "deleted_at": db_document.deleted_at,
        "created_at": db_document.created_at,
        "updated_at": db_document.updated_at,
        "tags": tags
    }

    return result


@router.put("/{document_id}", response_model=DocumentResponse)
def update_document(document_id: int, document_update: DocumentUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="文档不存在")

    # 检查编辑权限
    if not check_document_edit_permission(db, document_id, current_user.id):
        raise HTTPException(status_code=403, detail="无权限编辑该文档")

    update_data = document_update.model_dump(exclude_unset=True, exclude={"tag_ids"})
    
    # 检查是否更新了内容或标题
    content_updated = "content" in update_data or "title" in update_data
    
    for key, value in update_data.items():
        setattr(document, key, value)

    if document_update.tag_ids is not None:
        db.query(DocumentTag).filter(DocumentTag.document_id == document_id).delete()
        for tag_id in document_update.tag_ids:
            doc_tag = DocumentTag(document_id=document_id, tag_id=tag_id)
            db.add(doc_tag)

    db.commit()
    db.refresh(document)
    
    # 如果内容或标题更新了，异步重新生成索引
    if content_updated:
        document.status = "draft"
        db.commit()
        from kiro_knbase.services.async_task_service import async_task_service
        async_task_service.create_document_index(document_id)

    author_name = None
    if document.author_id:
        author = db.query(User).filter(User.id == document.author_id).first()
        author_name = author.username if author else None

    category_name = None
    if document.category_id:
        from kiro_knbase.models.category import Category
        category = db.query(Category).filter(Category.id == document.category_id).first()
        category_name = category.name if category else None

    tags = []
    document_tags = db.query(DocumentTag).filter(DocumentTag.document_id == document.id).all()
    for doc_tag in document_tags:
        from kiro_knbase.models.category import Tag
        tag = db.query(Tag).filter(Tag.id == doc_tag.tag_id).first()
        if tag:
            tags.append(tag.name)

    result = {
        "id": document.id,
        "title": document.title,
        "content": document.content,
        "author_id": document.author_id,
        "author_name": author_name,
        "category_id": document.category_id,
        "category_name": category_name,
        "permission": document.permission,
        "view_count": document.view_count,
        "like_count": document.like_count,
        "comment_count": document.comment_count,
        "is_deleted": document.is_deleted,
        "deleted_at": document.deleted_at,
        "created_at": document.created_at,
        "updated_at": document.updated_at,
        "tags": tags
    }

    return result


@router.delete("/{document_id}")
def delete_document(document_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="文档不存在")

    # 检查删除权限
    if not check_document_delete_permission(db, document_id, current_user.id):
        raise HTTPException(status_code=403, detail="无权限删除该文档")

    document.is_deleted = True
    from kiro_platform.core.timezone_utils import get_beijing_time
    document.deleted_at = get_beijing_time()
    document.deleted_by = current_user.id  # 记录删除者
    db.commit()
    return {"message": "文档已移入回收站"}


@router.post("/{document_id}/restore")
def restore_document(document_id: int, db: Session = Depends(get_db)):
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="文档不存在")

    document.is_deleted = False
    document.deleted_at = None
    db.commit()
    return {"message": "文档已恢复"}


@router.get("/{document_id}/versions", response_model=List[DocumentVersionResponse])
def list_versions(document_id: int, db: Session = Depends(get_db)):
    versions = db.query(DocumentVersion).filter(
        DocumentVersion.document_id == document_id
    ).order_by(DocumentVersion.version_number.desc()).all()
    return versions


@router.get("/{document_id}/versions/{version_number}", response_model=DocumentVersionResponse)
def get_version(document_id: int, version_number: int, db: Session = Depends(get_db)):
    version = db.query(DocumentVersion).filter(
        DocumentVersion.document_id == document_id,
        DocumentVersion.version_number == version_number
    ).first()
    if not version:
        raise HTTPException(status_code=404, detail="版本不存在")
    return version


@router.post("/{document_id}/favorite")
def toggle_favorite(document_id: int, db: Session = Depends(get_db)):
    existing = db.query(UserFavorite).filter(
        UserFavorite.document_id == document_id
    ).first()

    if existing:
        db.delete(existing)
        db.commit()
        return {"message": "已取消收藏", "is_favorited": False}
    else:
        favorite = UserFavorite(document_id=document_id, user_id=1)
        db.add(favorite)
        db.commit()
        return {"message": "已收藏", "is_favorited": True}


@router.post("/{document_id}/like")
def toggle_like(document_id: int, db: Session = Depends(get_db)):
    existing = db.query(DocumentLike).filter(
        DocumentLike.document_id == document_id
    ).first()

    if existing:
        db.delete(existing)
        document = db.query(Document).filter(Document.id == document_id).first()
        document.like_count = max(0, document.like_count - 1)
        db.commit()
        return {"message": "已取消点赞", "is_liked": False}
    else:
        like = DocumentLike(document_id=document_id, user_id=1)
        db.add(like)
        document = db.query(Document).filter(Document.id == document_id).first()
        document.like_count += 1
        db.commit()
        return {"message": "已点赞", "is_liked": True}


@router.post("/{document_id}/share", response_model=dict)
def share_document(document_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    import uuid
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="文档不存在")

    share = DocumentShare(
        document_id=document_id,
        share_token=str(uuid.uuid4()),
        created_by=current_user.id
    )
    db.add(share)
    db.commit()
    db.refresh(share)

    share_url = f"http://localhost:5120/share/{share.share_token}"
    return {"share_token": share.share_token, "share_url": share_url}


@router.get("/share/{share_token}")
def get_shared_document(share_token: str, db: Session = Depends(get_db)):
    share = db.query(DocumentShare).filter(DocumentShare.share_token == share_token).first()
    if not share:
        raise HTTPException(status_code=404, detail="分享不存在")

    share.view_count += 1
    db.commit()

    return share.document


@router.get("/{document_id}/download")
def download_document(
    document_id: int,
    format: str = Query("markdown", enum=["markdown", "html", "text"]),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    from fastapi.responses import StreamingResponse
    import io
    
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="文档不存在")

    if document.permission == "private" and document.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="没有权限下载此文档")

    if format == "markdown":
        content = f"# {document.title}\n\n{document.content}"
        content_type = "text/markdown"
        filename = f"{document.title}.md"
    elif format == "html":
        import markdown
        md = markdown.Markdown(extensions=['extra', 'codehilite'])
        html_content = md.convert(document.content)
        content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>{document.title}</title>
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }}
        h1 {{ color: #333; }}
        pre {{ background: #f5f5f5; padding: 10px; border-radius: 5px; overflow-x: auto; }}
        code {{ background: #f5f5f5; padding: 2px 4px; border-radius: 3px; }}
    </style>
</head>
<body>
    <h1>{document.title}</h1>
    {html_content}
</body>
</html>"""
        content_type = "text/html"
        filename = f"{document.title}.html"
    else:
        content = f"{document.title}\n\n{document.content}"
        content_type = "text/plain"
        filename = f"{document.title}.txt"

    file_like = io.BytesIO(content.encode('utf-8'))
    headers = {
        "Content-Disposition": f"attachment; filename={filename}",
        "Content-Type": content_type
    }
    return StreamingResponse(file_like, headers=headers)


@router.post("/batch/delete")
def batch_delete_documents(
    document_ids: List[int] = Body(..., embed=True),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """批量删除文档（移入回收站）"""
    from kiro_platform.core.timezone_utils import get_beijing_time
    
    documents = db.query(Document).filter(Document.id.in_(document_ids)).all()
    deleted_count = 0
    
    for doc in documents:
        if doc.is_deleted:
            continue
        doc.is_deleted = True
        doc.deleted_at = get_beijing_time()
        deleted_count += 1
    
    db.commit()
    return {"message": f"成功删除 {deleted_count} 个文档", "deleted_count": deleted_count}


@router.post("/batch/category")
def batch_update_category(
    document_ids: List[int] = Body(..., embed=True),
    category_id: Optional[int] = Body(None, embed=True),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """批量更新文档分类"""
    documents = db.query(Document).filter(Document.id.in_(document_ids)).all()
    updated_count = 0
    
    for doc in documents:
        doc.category_id = category_id
        updated_count += 1
    
    db.commit()
    return {"message": f"成功更新 {updated_count} 个文档的分类", "updated_count": updated_count}


@router.post("/batch/permission")
def batch_update_permission(
    document_ids: List[int] = Body(..., embed=True),
    permission: str = Body(..., embed=True),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """批量更新文档权限"""
    valid_permissions = ["public", "private"]
    if permission not in valid_permissions:
        raise HTTPException(status_code=400, detail=f"无效的权限值，有效值: {valid_permissions}")
    
    documents = db.query(Document).filter(Document.id.in_(document_ids)).all()
    updated_count = 0
    
    for doc in documents:
        doc.permission = permission
        updated_count += 1
    
    db.commit()
    return {"message": f"成功更新 {updated_count} 个文档的权限", "updated_count": updated_count}


@router.post("/batch/restore")
def batch_restore_documents(
    document_ids: List[int] = Body(..., embed=True),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """批量恢复文档（从回收站恢复）"""
    documents = db.query(Document).filter(Document.id.in_(document_ids)).all()
    restored_count = 0
    
    for doc in documents:
        if not doc.is_deleted:
            continue
        doc.is_deleted = False
        doc.deleted_at = None
        restored_count += 1
    
    db.commit()
    return {"message": f"成功恢复 {restored_count} 个文档", "restored_count": restored_count}


@router.delete("/batch/permanent")
def batch_permanent_delete(
    document_ids: List[int] = Body(..., embed=True),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """批量永久删除文档"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="只有管理员可以永久删除文档")
    
    documents = db.query(Document).filter(Document.id.in_(document_ids)).all()
    deleted_count = 0
    
    for doc in documents:
        db.delete(doc)
        deleted_count += 1
    
    db.commit()
    return {"message": f"成功永久删除 {deleted_count} 个文档", "deleted_count": deleted_count}


@router.get("/{document_id}/index-status", response_model=DocumentIndexStatusResponse)
def get_document_index_status(document_id: int):
    """获取文档索引生成状态"""
    from kiro_knbase.services.async_task_service import async_task_service
    
    status = async_task_service.get_index_status(document_id)
    
    if status is None:
        raise HTTPException(status_code=404, detail="文档不存在或状态未知")
    
    return {
        "document_id": document_id,
        **status
    }


@router.post("/{document_id}/reindex")
def reindex_document(document_id: int, db: Session = Depends(get_db)):
    """重新生成文档索引"""
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="文档不存在")
    
    # 设置状态为draft
    document.status = "draft"
    db.commit()
    
    # 异步创建索引
    from kiro_knbase.services.async_task_service import async_task_service
    async_task_service.create_document_index(document_id)
    
    return {"message": "索引重新生成任务已启动"}


@router.get("/{document_id}/chunks")
def get_document_chunks(document_id: int, db: Session = Depends(get_db)):
    """获取文档索引chunks"""
    from kiro_knbase.models.ai_models import DocumentVector
    
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="文档不存在")
    
    # 从数据库获取文档的chunks
    chunks = db.query(DocumentVector).filter(
        DocumentVector.document_id == document_id
    ).order_by(DocumentVector.chunk_index).all()
    
    result = []
    for chunk in chunks:
        result.append({
            "id": chunk.id,
            "document_id": chunk.document_id,
            "chunk_index": chunk.chunk_index,
            "chunk_content": chunk.chunk_content,
            "created_at": chunk.created_at
        })
    
    return {
        "document_id": document_id,
        "chunks": result
    }
