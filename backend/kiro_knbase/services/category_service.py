from typing import List, Optional

from kiro_platform.core.database import SessionLocal
from kiro_platform.core.exceptions import NotFoundError
from kiro_knbase.models.category import Category
from kiro_knbase.schemas.category import CategoryCreate, CategoryUpdate, CategoryResponse


def get_category(db, category_id: int) -> Optional[Category]:
    return db.query(Category).filter(Category.id == category_id).first()


def get_categories(db, skip: int = 0, limit: int = 100, parent_id: Optional[int] = None) -> List[Category]:
    query = db.query(Category)
    if parent_id is not None:
        query = query.filter(Category.parent_id == parent_id)
    return query.offset(skip).limit(limit).all()


def create_category(db, category_create: CategoryCreate) -> Category:
    category = Category(
        name=category_create.name,
        description=category_create.description,
        parent_id=category_create.parent_id,
        sort_order=category_create.sort_order or 0
    )
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


def update_category(db, category_id: int, category_update: CategoryUpdate) -> Category:
    category = get_category(db, category_id)
    if not category:
        raise NotFoundError("Category not found")
    
    if category_update.name:
        category.name = category_update.name
    if category_update.description:
        category.description = category_update.description
    if category_update.parent_id is not None:
        category.parent_id = category_update.parent_id
    if category_update.sort_order is not None:
        category.sort_order = category_update.sort_order
    
    db.commit()
    db.refresh(category)
    return category


def delete_category(db, category_id: int) -> None:
    category = get_category(db, category_id)
    if not category:
        raise NotFoundError("Category not found")
    
    db.delete(category)
    db.commit()


def build_category_tree(categories: List[Category]) -> List[dict]:
    category_map = {cat.id: cat for cat in categories}
    tree = []
    
    for cat in categories:
        if cat.parent_id:
            parent = category_map.get(cat.parent_id)
            if parent:
                if not hasattr(parent, 'children'):
                    parent.children = []
                parent.children.append(cat)
        else:
            tree.append(cat)
    
    return tree


def get_category_response(category: Category) -> CategoryResponse:
    return CategoryResponse(
        id=category.id,
        name=category.name,
        description=category.description,
        parent_id=category.parent_id,
        sort_order=category.sort_order,
        created_at=category.created_at,
        updated_at=category.updated_at
    )
