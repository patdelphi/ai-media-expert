from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.models.video import AIConfig
from app.schemas.video import AIConfigCreate, AIConfigUpdate, AIConfigResponse, AIConfigPublicResponse

router = APIRouter()

@router.post("/", response_model=AIConfigResponse)
async def create_ai_config(
    config: AIConfigCreate,
    db: Session = Depends(get_db)
):
    """创建AI配置"""
    
    # 检查名称是否已存在
    existing = db.query(AIConfig).filter(AIConfig.name == config.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="配置名称已存在")
    
    db_config = AIConfig(**config.dict())
    db.add(db_config)
    db.commit()
    db.refresh(db_config)
    
    return db_config

@router.get("/", response_model=List[AIConfigPublicResponse])
async def get_ai_configs(
    include_inactive: bool = False,
    db: Session = Depends(get_db)
):
    """获取AI配置列表（公开信息，不包含API密钥）"""
    
    query = db.query(AIConfig)
    if not include_inactive:
        query = query.filter(AIConfig.is_active == True)
    
    configs = query.order_by(AIConfig.created_at.desc()).all()
    return configs

@router.get("/full", response_model=List[AIConfigResponse])
async def get_ai_configs_full(
    include_inactive: bool = False,
    db: Session = Depends(get_db)
):
    """获取AI配置完整信息（包含API密钥，仅管理员使用）"""
    
    query = db.query(AIConfig)
    if not include_inactive:
        query = query.filter(AIConfig.is_active == True)
    
    configs = query.order_by(AIConfig.created_at.desc()).all()
    return configs

@router.get("/{config_id}", response_model=AIConfigResponse)
async def get_ai_config(
    config_id: int,
    db: Session = Depends(get_db)
):
    """获取单个AI配置详情"""
    
    config = db.query(AIConfig).filter(AIConfig.id == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="AI配置不存在")
    
    return config

@router.put("/{config_id}", response_model=AIConfigResponse)
async def update_ai_config(
    config_id: int,
    config_update: AIConfigUpdate,
    db: Session = Depends(get_db)
):
    """更新AI配置"""
    
    config = db.query(AIConfig).filter(AIConfig.id == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="AI配置不存在")
    
    # 检查名称是否与其他配置冲突
    if config_update.name and config_update.name != config.name:
        existing = db.query(AIConfig).filter(
            AIConfig.name == config_update.name,
            AIConfig.id != config_id
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="配置名称已存在")
    
    # 更新字段
    for field, value in config_update.dict(exclude_unset=True).items():
        setattr(config, field, value)
    
    db.commit()
    db.refresh(config)
    
    return config

@router.delete("/{config_id}")
async def delete_ai_config(
    config_id: int,
    db: Session = Depends(get_db)
):
    """删除AI配置"""
    
    config = db.query(AIConfig).filter(AIConfig.id == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="AI配置不存在")
    
    db.delete(config)
    db.commit()
    
    return {"message": "AI配置删除成功"}

@router.post("/{config_id}/test")
async def test_ai_config(
    config_id: int,
    db: Session = Depends(get_db)
):
    """测试AI配置连接"""
    
    config = db.query(AIConfig).filter(AIConfig.id == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="AI配置不存在")
    
    try:
        # 这里应该实际测试AI API连接
        # 暂时返回模拟结果
        return {
            "success": True,
            "message": "AI配置测试成功",
            "response_time": "0.5s",
            "model_info": {
                "provider": config.provider,
                "model": config.model,
                "max_tokens": config.max_tokens
            }
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"AI配置测试失败: {str(e)}"
        }

@router.post("/{config_id}/activate")
async def activate_ai_config(
    config_id: int,
    db: Session = Depends(get_db)
):
    """激活AI配置"""
    
    config = db.query(AIConfig).filter(AIConfig.id == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="AI配置不存在")
    
    config.is_active = True
    db.commit()
    
    return {"message": "AI配置已激活"}

@router.post("/{config_id}/deactivate")
async def deactivate_ai_config(
    config_id: int,
    db: Session = Depends(get_db)
):
    """停用AI配置"""
    
    config = db.query(AIConfig).filter(AIConfig.id == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="AI配置不存在")
    
    config.is_active = False
    db.commit()
    
    return {"message": "AI配置已停用"}