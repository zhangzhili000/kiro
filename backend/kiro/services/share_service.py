from typing import Optional
import io
import markdown
from datetime import datetime, timedelta
from kiro.core.timezone_utils import get_beijing_time

from kiro.core.database import SessionLocal
from kiro.core.exceptions import NotFoundError, PermissionError
from kiro.models.document import Document, DocumentShare


def export_document_as_markdown(db, document_id: int, user_id: int) -> bytes:
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise NotFoundError("Document not found")
    
    if document.permission == 'private' and document.author_id != user_id:
        raise PermissionError("You don't have permission to download this document")
    
    content = f"# {document.title}\n\n{document.content}"
    return content.encode('utf-8')


def export_document_as_html(db, document_id: int, user_id: int) -> bytes:
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise NotFoundError("Document not found")
    
    if document.permission == 'private' and document.author_id != user_id:
        raise PermissionError("You don't have permission to download this document")
    
    md = markdown.Markdown(extensions=['extra', 'codehilite'])
    html_content = md.convert(document.content)
    
    full_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>{document.title}</title>
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }}
        h1 {{ color: #333; }}
        pre {{ background: #f5f5f5; padding: 10px; border-radius: 5px; }}
    </style>
</head>
<body>
    <h1>{document.title}</h1>
    {html_content}
</body>
</html>"""
    
    return full_html.encode('utf-8')


def export_document_as_text(db, document_id: int, user_id: int) -> bytes:
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise NotFoundError("Document not found")
    
    if document.permission == 'private' and document.author_id != user_id:
        raise PermissionError("You don't have permission to download this document")
    
    content = f"{document.title}\n\n{document.content}"
    return content.encode('utf-8')


def generate_share_link(db, document_id: int, user_id: int, expires_in_days: int = 7) -> str:
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise NotFoundError("Document not found")
    
    if document.author_id != user_id:
        raise PermissionError("Only the author can share this document")
    
    share = DocumentShare(
        document_id=document_id,
        share_token=f"share_{document_id}_{get_beijing_time().timestamp()}",
        expires_at=get_beijing_time() + timedelta(days=expires_in_days),
        created_by=user_id
    )
    db.add(share)
    db.commit()
    db.refresh(share)
    
    return share.share_token


def get_shared_document(db, share_token: str) -> Optional[Document]:
    share = db.query(DocumentShare).filter(DocumentShare.share_token == share_token).first()
    if not share:
        raise NotFoundError("Share link not found")
    
    if share.expires_at and share.expires_at < get_beijing_time():
        raise PermissionError("Share link has expired")
    
    return share.document
