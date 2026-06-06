from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from ...core.database import get_db
from ...schemas.department import DepartmentCreate, DepartmentUpdate, DepartmentResponse, DepartmentTreeResponse
from ...models import Department

router = APIRouter(prefix="/departments", tags=["部门"])


@router.get("", response_model=List[DepartmentResponse])
def list_departments(db: Session = Depends(get_db)):
    return db.query(Department).all()


@router.get("/tree", response_model=List[DepartmentTreeResponse])
def get_department_tree(db: Session = Depends(get_db)):
    root_departments = db.query(Department).filter(Department.parent_id == None).all()
    return root_departments


@router.post("", response_model=DepartmentResponse)
def create_department(department: DepartmentCreate, db: Session = Depends(get_db)):
    db_department = Department(**department.model_dump())
    db.add(db_department)
    db.commit()
    db.refresh(db_department)
    return db_department


@router.put("/{department_id}", response_model=DepartmentResponse)
def update_department(department_id: int, department_update: DepartmentUpdate, db: Session = Depends(get_db)):
    db_department = db.query(Department).filter(Department.id == department_id).first()
    if not db_department:
        raise HTTPException(status_code=404, detail="部门不存在")

    for key, value in department_update.model_dump(exclude_unset=True).items():
        setattr(db_department, key, value)
    db.commit()
    db.refresh(db_department)
    return db_department


@router.delete("/{department_id}")
def delete_department(department_id: int, db: Session = Depends(get_db)):
    db_department = db.query(Department).filter(Department.id == department_id).first()
    if not db_department:
        raise HTTPException(status_code=404, detail="部门不存在")

    db.delete(db_department)
    db.commit()
    return {"message": "删除成功"}
