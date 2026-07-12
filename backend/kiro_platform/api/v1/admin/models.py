from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from kiro_platform.core.database import get_db
from kiro_platform.api.v1.users import get_current_user
from kiro_platform.models.user import User
from kiro_knbase.models.ai_models import ModelConfig
from kiro_platform.core.timezone_utils import get_beijing_time
from typing import List

router = APIRouter(prefix="/admin/models", tags=["管理员-模型管理"])


def get_current_admin(current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="无管理员权限")
    return current_user


@router.get("/")
@router.get("")
async def get_models(
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """获取所有模型配置"""
    
    models = db.query(ModelConfig).all()
    
    result = []
    for model in models:
        result.append({
            "id": model.id,
            "type": model.type,
            "api_type": model.api_type,
            "model_id": model.model_id,
            "api_key": model.api_key,
            "api_base": model.api_base,
            "description": model.description,
            "status": model.status,
            "created_at": model.created_at.isoformat() if model.created_at else None,
            "updated_at": model.updated_at.isoformat() if model.updated_at else None
        })
    
    return result


@router.post("/")
@router.post("")
async def create_model(
    data: dict,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """创建新的模型配置"""
    
    required_fields = ["type", "api_type", "model_id", "api_key"]
    for field in required_fields:
        if field not in data:
            raise HTTPException(status_code=400, detail=f"缺少必填字段: {field}")
    
    new_model = ModelConfig(
        type=data["type"],
        api_type=data["api_type"],
        model_id=data["model_id"],
        api_key=data["api_key"],
        api_base=data.get("api_base"),
        description=data.get("description"),
        status=data.get("status", "active"),
        created_at=get_beijing_time(),
        updated_at=get_beijing_time()
    )
    
    db.add(new_model)
    db.commit()
    db.refresh(new_model)
    
    return {
        "id": new_model.id,
        "type": new_model.type,
        "api_type": new_model.api_type,
        "model_id": new_model.model_id,
        "api_key": new_model.api_key,
        "api_base": new_model.api_base,
        "description": new_model.description,
        "status": new_model.status,
        "created_at": new_model.created_at.isoformat(),
        "updated_at": new_model.updated_at.isoformat()
    }


@router.put("/{model_id}", response_model=dict)
async def update_model(
    model_id: int,
    data: dict,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """更新模型配置"""
    
    model = db.query(ModelConfig).filter(ModelConfig.id == model_id).first()
    if not model:
        raise HTTPException(status_code=404, detail="模型配置不存在")
    
    if "type" in data:
        model.type = data["type"]
    if "api_type" in data:
        model.api_type = data["api_type"]
    if "model_id" in data:
        model.model_id = data["model_id"]
    if "api_key" in data:
        model.api_key = data["api_key"]
    if "api_base" in data:
        model.api_base = data["api_base"]
    if "description" in data:
        model.description = data["description"]
    if "status" in data:
        model.status = data["status"]
    
    model.updated_at = get_beijing_time()
    
    db.commit()
    db.refresh(model)
    
    return {
        "id": model.id,
        "type": model.type,
        "api_type": model.api_type,
        "model_id": model.model_id,
        "api_key": model.api_key,
        "api_base": model.api_base,
        "description": model.description,
        "status": model.status,
        "created_at": model.created_at.isoformat(),
        "updated_at": model.updated_at.isoformat()
    }


@router.delete("/{model_id}", response_model=dict)
async def delete_model(
    model_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """删除模型配置"""
    
    model = db.query(ModelConfig).filter(ModelConfig.id == model_id).first()
    if not model:
        raise HTTPException(status_code=404, detail="模型配置不存在")
    
    db.delete(model)
    db.commit()
    
    return {"success": True, "message": "模型配置已删除"}


@router.patch("/{model_id}/status", response_model=dict)
async def update_model_status(
    model_id: int,
    data: dict,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """更新模型状态"""
    
    if "status" not in data:
        raise HTTPException(status_code=400, detail="缺少status字段")
    
    model = db.query(ModelConfig).filter(ModelConfig.id == model_id).first()
    if not model:
        raise HTTPException(status_code=404, detail="模型配置不存在")
    
    model.status = data["status"]
    model.updated_at = get_beijing_time()
    
    db.commit()
    db.refresh(model)
    
    return {
        "id": model.id,
        "status": model.status
    }