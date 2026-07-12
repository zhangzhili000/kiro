from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import os
import uuid

from kiro_platform.core.database import get_db
from kiro_platform.api.v1.users import get_current_user
from kiro_platform.models.user import User
from kiro_knbase.models.attachment import Attachment
from kiro_knbase.models.document import Document
from kiro_knbase.schemas.attachment import AttachmentResponse

router = APIRouter(prefix="/attachments", tags=["附件管理"])

UPLOAD_DIR = "uploads"

@router.post("/{document_id}/upload")
async def upload_attachment(
    document_id: int,
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """上传文档附件"""
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="文档不存在")
    
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    uploaded_files = []
    
    for file in files:
        file_extension = os.path.splitext(file.filename)[1]
        new_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = os.path.join(UPLOAD_DIR, new_filename)
        
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        attachment = Attachment(
            document_id=document_id,
            stored_filename=new_filename,
            original_filename=file.filename,
            file_size=len(content),
            content_type=file.content_type,
            uploaded_by=current_user.id
        )
        db.add(attachment)
        uploaded_files.append(attachment)
    
    db.commit()
    
    return {"message": f"成功上传 {len(uploaded_files)} 个附件", "files": [
        {"id": att.id, "filename": att.original_filename} for att in uploaded_files
    ]}


@router.get("/{document_id}", response_model=List[AttachmentResponse])
def list_attachments(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取文档附件列表"""
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="文档不存在")
    
    attachments = db.query(Attachment).filter(
        Attachment.document_id == document_id
    ).all()
    
    return attachments


@router.delete("/{attachment_id}")
def delete_attachment(
    attachment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除附件"""
    attachment = db.query(Attachment).filter(Attachment.id == attachment_id).first()
    if not attachment:
        raise HTTPException(status_code=404, detail="附件不存在")
    
    file_path = os.path.join(UPLOAD_DIR, attachment.stored_filename)
    if os.path.exists(file_path):
        os.remove(file_path)
    
    db.delete(attachment)
    db.commit()
    
    return {"message": "附件已删除"}


@router.get("/{attachment_id}/download")
def download_attachment(
    attachment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """下载附件"""
    from fastapi.responses import FileResponse
    
    attachment = db.query(Attachment).filter(Attachment.id == attachment_id).first()
    if not attachment:
        raise HTTPException(status_code=404, detail="附件不存在")
    
    file_path = os.path.join(UPLOAD_DIR, attachment.stored_filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="文件不存在")
    
    return FileResponse(
        path=file_path,
        filename=attachment.original_filename,
        media_type=attachment.content_type
    )