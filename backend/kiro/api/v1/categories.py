from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from ...core.database import get_db
from ...schemas.category import CategoryCreate, CategoryUpdate, CategoryResponse, CategoryTreeResponse
from ...models import Category

router = APIRouter(prefix="/categories", tags=["分类"])


@router.get("", response_model=List[CategoryResponse])
def list_categories(db: Session = Depends(get_db)):
    return db.query(Category).order_by(Category.sort_order).all()


@router.get("/tree", response_model=List[CategoryTreeResponse])
def get_category_tree(db: Session = Depends(get_db)):
    root_categories = db.query(Category).filter(Category.parent_id == None).order_by(Category.sort_order).all()
    return root_categories


@router.post("", response_model=CategoryResponse)
def create_category(category: CategoryCreate, db: Session = Depends(get_db)):
    db_category = Category(**category.model_dump())
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category


@router.put("/{category_id}", response_model=CategoryResponse)
def update_category(category_id: int, category_update: CategoryUpdate, db: Session = Depends(get_db)):
    db_category = db.query(Category).filter(Category.id == category_id).first()
    if not db_category:
        raise HTTPException(status_code=404, detail="分类不存在")

    for key, value in category_update.model_dump(exclude_unset=True).items():
        setattr(db_category, key, value)
    db.commit()
    db.refresh(db_category)
    return db_category


@router.delete("/{category_id}")
def delete_category(category_id: int, db: Session = Depends(get_db)):
    db_category = db.query(Category).filter(Category.id == category_id).first()
    if not db_category:
        raise HTTPException(status_code=404, detail="分类不存在")

    db.delete(db_category)
    db.commit()
    return {"message": "删除成功"}
