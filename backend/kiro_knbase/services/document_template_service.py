from sqlalchemy.orm import Session
from typing import List, Optional

from kiro_knbase.models.document_template import DocumentTemplate
from kiro_knbase.schemas.document_template import DocumentTemplateCreate, DocumentTemplateUpdate


def get_templates(db: Session, category_id: Optional[int] = None, is_public: Optional[bool] = None) -> List[DocumentTemplate]:
    query = db.query(DocumentTemplate).filter(DocumentTemplate.is_active == True)
    
    if category_id:
        query = query.filter(DocumentTemplate.category_id == category_id)
    if is_public is not None:
        query = query.filter(DocumentTemplate.is_public == is_public)
    
    return query.order_by(DocumentTemplate.sort_order).all()


def get_template(db: Session, template_id: int) -> Optional[DocumentTemplate]:
    return db.query(DocumentTemplate).filter(
        DocumentTemplate.id == template_id,
        DocumentTemplate.is_active == True
    ).first()


def create_template(db: Session, template: DocumentTemplateCreate, user_id: int) -> DocumentTemplate:
    db_template = DocumentTemplate(
        name=template.name,
        description=template.description,
        content=template.content,
        category_id=template.category_id,
        is_public=template.is_public,
        created_by=user_id
    )
    db.add(db_template)
    db.commit()
    db.refresh(db_template)
    return db_template


def update_template(db: Session, template_id: int, template_update: DocumentTemplateUpdate) -> Optional[DocumentTemplate]:
    db_template = get_template(db, template_id)
    if not db_template:
        return None
    
    update_data = template_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_template, key, value)
    
    db.commit()
    db.refresh(db_template)
    return db_template


def delete_template(db: Session, template_id: int) -> bool:
    db_template = get_template(db, template_id)
    if not db_template:
        return False
    
    db_template.is_active = False
    db.commit()
    return True