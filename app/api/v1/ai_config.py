from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.models.video import AIConfig
from app.schemas.video import AIConfigCreate, AIConfigUpdate, AIConfigResponse, AIConfigPublicResponse
from app.schemas.common import ResponseModel

router = APIRouter()

@router.post("/", response_model=ResponseModel[AIConfigResponse])
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
    
    return ResponseModel(
        code=200,
        message="AI配置创建成功",
        data=db_config
    )

@router.get("/", response_model=ResponseModel[List[AIConfigPublicResponse]])
async def get_ai_configs(
    include_inactive: bool = False,
    db: Session = Depends(get_db)
):
    """获取AI配置列表（公开信息，不包含API密钥）"""
    
    query = db.query(AIConfig)
    if not include_inactive:
        query = query.filter(AIConfig.is_active == True)
    
    configs = query.order_by(AIConfig.created_at.desc()).all()
    return ResponseModel(
        code=200,
        message="AI配置列表获取成功",
        data=configs
    )

@router.get("/full", response_model=ResponseModel[List[AIConfigResponse]])
async def get_ai_configs_full(
    include_inactive: bool = False,
    db: Session = Depends(get_db)
):
    """获取AI配置完整信息（包含API密钥，仅管理员使用）"""
    
    query = db.query(AIConfig)
    if not include_inactive:
        query = query.filter(AIConfig.is_active == True)
    
    configs = query.order_by(AIConfig.created_at.desc()).all()
    return ResponseModel(
        code=200,
        message="AI配置完整信息获取成功",
        data=configs
    )

@router.get("/{config_id}", response_model=ResponseModel[AIConfigResponse])
async def get_ai_config(
    config_id: int,
    db: Session = Depends(get_db)
):
    """获取单个AI配置详情"""
    
    config = db.query(AIConfig).filter(AIConfig.id == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="AI配置不存在")
    
    return ResponseModel(
        code=200,
        message="AI配置获取成功",
        data=config
    )

@router.put("/{config_id}", response_model=ResponseModel[AIConfigResponse])
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
    
    return ResponseModel(
        code=200,
        message="AI配置更新成功",
        data=config
    )

@router.delete("/{config_id}", response_model=ResponseModel)
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
    
    return ResponseModel(
        code=200,
        message="AI配置删除成功",
        data=None
    )

@router.post("/{config_id}/test", response_model=ResponseModel)
async def test_ai_config(
    config_id: int,
    db: Session = Depends(get_db)
):
    """测试AI配置连接"""
    
    config = db.query(AIConfig).filter(AIConfig.id == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="AI配置不存在")
    
    try:
        # 实际测试AI API连接
        import httpx
        import time
        
        start_time = time.time()
        
        # 构建测试请求
        headers = {
            "Authorization": f"Bearer {config.api_key}",
            "Content-Type": "application/json"
        }
        
        # 根据不同provider构建不同的测试请求
        if config.provider.lower() == "openai" or "chat/completions" in config.api_base:
            test_data = {
                "model": config.model,
                "messages": [{"role": "user", "content": "Hello"}],
                "max_tokens": min(config.max_tokens or 10, 10),
                "temperature": config.temperature or 0.7
            }
            # 如果api_base已经包含完整路径，直接使用
            if config.api_base.endswith('/chat/completions'):
                test_url = config.api_base
            else:
                test_url = f"{config.api_base.rstrip('/')}/chat/completions"
        else:
            # 对于其他provider，使用通用测试
            test_data = {
                "model": config.model,
                "prompt": "Hello",
                "max_tokens": min(config.max_tokens or 10, 10),
                "temperature": config.temperature or 0.7
            }
            # 如果api_base已经包含完整路径，直接使用
            if config.api_base.endswith('/completions'):
                test_url = config.api_base
            else:
                test_url = f"{config.api_base.rstrip('/')}/completions"
        
        # 发送测试请求
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(test_url, json=test_data, headers=headers)
            
        response_time = round(time.time() - start_time, 2)
        
        if response.status_code == 200:
            test_result = {
                "success": True,
                "message": "AI配置测试成功",
                "response_time": f"{response_time}s",
                "status_code": response.status_code,
                "model_info": {
                    "provider": config.provider,
                    "model": config.model,
                    "max_tokens": config.max_tokens
                }
            }
        else:
            test_result = {
                "success": False,
                "message": f"API返回错误: {response.status_code} - {response.text[:200]}",
                "response_time": f"{response_time}s",
                "status_code": response.status_code
            }
            
        return ResponseModel(
            code=200,
            message="AI配置测试完成",
            data=test_result
        )
        
    except httpx.TimeoutException:
        test_result = {
            "success": False,
            "message": "请求超时，请检查网络连接和API地址"
        }
        return ResponseModel(
            code=200,
            message="AI配置测试完成",
            data=test_result
        )
    except httpx.RequestError as e:
        test_result = {
            "success": False,
            "message": f"网络请求失败: {str(e)}"
        }
        return ResponseModel(
            code=200,
            message="AI配置测试完成",
            data=test_result
        )
    except Exception as e:
        test_result = {
            "success": False,
            "message": f"测试失败: {str(e)}"
        }
        return ResponseModel(
            code=200,
            message="AI配置测试完成",
            data=test_result
        )

@router.post("/{config_id}/activate", response_model=ResponseModel)
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
    db.refresh(config)
    
    return ResponseModel(
        code=200,
        message="AI配置已激活",
        data=config
    )

@router.post("/{config_id}/deactivate", response_model=ResponseModel)
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
    db.refresh(config)
    
    return ResponseModel(
        code=200,
        message="AI配置已停用",
        data=config
    )