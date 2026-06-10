from typing import List, Optional

from kiro.core.database import SessionLocal
from kiro.core.exceptions import NotFoundError
from kiro.models.department import Department
from kiro.schemas.department import DepartmentCreate, DepartmentUpdate, DepartmentResponse


def get_department(db, department_id: int) -> Optional[Department]:
    return db.query(Department).filter(Department.id == department_id).first()


def get_departments(db, skip: int = 0, limit: int = 100) -> List[Department]:
    return db.query(Department).offset(skip).limit(limit).all()


def create_department(db, department_create: DepartmentCreate) -> Department:
    department = Department(
        name=department_create.name,
        description=department_create.description,
        parent_id=department_create.parent_id
    )
    db.add(department)
    db.commit()
    db.refresh(department)
    return department


def update_department(db, department_id: int, department_update: DepartmentUpdate) -> Department:
    department = get_department(db, department_id)
    if not department:
        raise NotFoundError("Department not found")
    
    if department_update.name:
        department.name = department_update.name
    if department_update.description:
        department.description = department_update.description
    if department_update.parent_id is not None:
        department.parent_id = department_update.parent_id
    
    db.commit()
    db.refresh(department)
    return department


def delete_department(db, department_id: int) -> None:
    department = get_department(db, department_id)
    if not department:
        raise NotFoundError("Department not found")
    
    db.delete(department)
    db.commit()


def build_department_tree(departments: List[Department]) -> List[dict]:
    department_map = {dept.id: dept for dept in departments}
    tree = []
    
    for dept in departments:
        if dept.parent_id:
            parent = department_map.get(dept.parent_id)
            if parent:
                if not hasattr(parent, 'children'):
                    parent.children = []
                parent.children.append(dept)
        else:
            tree.append(dept)
    
    return tree


def get_department_response(department: Department) -> DepartmentResponse:
    return DepartmentResponse(
        id=department.id,
        name=department.name,
        description=department.description,
        parent_id=department.parent_id,
        created_at=department.created_at,
        updated_at=department.updated_at
    )
