from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.api.deps import get_current_user, require_admin
from app.core.database import get_db
from app.core.security import decrypt_value, encrypt_value
from app.models.video import AIConfig
from app.schemas.video import AIConfigCreate, AIConfigUpdate, AIConfigResponse, AIConfigPublicResponse
from app.schemas.common import ResponseModel
from app.models.user import User

router = APIRouter()

def _encrypt_api_key(api_key: str) -> str:
    if not api_key:
        return api_key
    if api_key.startswith("enc:"):
        return api_key
    return "enc:" + encrypt_value(api_key)


def _decrypt_api_key(stored: str) -> str:
    if not stored:
        return stored
    if stored.startswith("enc:"):
        return decrypt_value(stored[4:])
    return stored


def _mask_api_key(stored: str) -> str:
    try:
        plain = _decrypt_api_key(stored)
    except Exception:
        return "****"
    if not plain:
        return ""
    if len(plain) <= 8:
        return "****"
    return f"{plain[:3]}****{plain[-4:]}"


def _apply_masked_keys(resp: AIConfigResponse, config: AIConfig) -> AIConfigResponse:
    """统一处理响应中的敏感密钥脱敏。"""
    resp.api_key = _mask_api_key(config.api_key)
    resp.upload_api_key = _mask_api_key(config.upload_api_key) if config.upload_api_key else ""
    return resp


@router.post("/", response_model=ResponseModel[AIConfigResponse])
async def create_ai_config(
    config: AIConfigCreate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """创建AI配置"""
    
    # 检查名称是否已存在
    existing = db.query(AIConfig).filter(AIConfig.name == config.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="配置名称已存在")
    
    config_dict = config.model_dump()
    config_dict["api_key"] = _encrypt_api_key(config_dict["api_key"])
    if config_dict.get("upload_api_key"):
        config_dict["upload_api_key"] = _encrypt_api_key(config_dict["upload_api_key"])
    db_config = AIConfig(**config_dict)
    db.add(db_config)
    db.commit()
    db.refresh(db_config)

    resp = _apply_masked_keys(AIConfigResponse.model_validate(db_config), db_config)
    return ResponseModel(
        code=200,
        message="AI配置创建成功",
        data=resp
    )

@router.get("/", response_model=ResponseModel[List[AIConfigPublicResponse]])
async def get_ai_configs(
    include_inactive: bool = False,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取AI配置列表（公开信息，不包含API密钥）"""
    
    query = db.query(AIConfig)
    if include_inactive and current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
    if not include_inactive:
        query = query.filter(AIConfig.is_active == True)
    
    configs = query.order_by(AIConfig.created_at.desc()).all()
    return ResponseModel(
        code=200,
        message="AI配置列表获取成功",
        data=[AIConfigPublicResponse.model_validate(config) for config in configs]
    )

@router.get("/full", response_model=ResponseModel[List[AIConfigResponse]])
async def get_ai_configs_full(
    include_inactive: bool = False,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """获取AI配置完整信息（包含API密钥，仅管理员使用）"""
    
    query = db.query(AIConfig)
    if not include_inactive:
        query = query.filter(AIConfig.is_active == True)
    
    configs = query.order_by(AIConfig.created_at.desc()).all()
    data: List[AIConfigResponse] = []
    for config in configs:
        resp = _apply_masked_keys(AIConfigResponse.model_validate(config), config)
        data.append(resp)
    return ResponseModel(
        code=200,
        message="AI配置完整信息获取成功",
        data=data
    )

@router.get("/{config_id}", response_model=ResponseModel[AIConfigResponse])
async def get_ai_config(
    config_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """获取单个AI配置详情"""
    
    config = db.query(AIConfig).filter(AIConfig.id == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="AI配置不存在")
    
    resp = _apply_masked_keys(AIConfigResponse.model_validate(config), config)
    return ResponseModel(
        code=200,
        message="AI配置获取成功",
        data=resp
    )

@router.put("/{config_id}", response_model=ResponseModel[AIConfigResponse])
async def update_ai_config(
    config_id: int,
    config_update: AIConfigUpdate,
    current_user: User = Depends(require_admin),
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
    update_data = config_update.model_dump(exclude_unset=True)
    if "api_key" in update_data:
        if update_data["api_key"]:
            update_data["api_key"] = _encrypt_api_key(update_data["api_key"])
        else:
            update_data.pop("api_key")
    if "upload_api_key" in update_data:
        if update_data["upload_api_key"]:
            update_data["upload_api_key"] = _encrypt_api_key(update_data["upload_api_key"])
        else:
            update_data.pop("upload_api_key")
    for field, value in update_data.items():
        setattr(config, field, value)
    
    db.commit()
    db.refresh(config)
    
    resp = _apply_masked_keys(AIConfigResponse.model_validate(config), config)
    return ResponseModel(
        code=200,
        message="AI配置更新成功",
        data=resp
    )

@router.delete("/{config_id}", response_model=ResponseModel)
async def delete_ai_config(
    config_id: int,
    current_user: User = Depends(require_admin),
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
    current_user: User = Depends(require_admin),
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
        try:
            api_key = _decrypt_api_key(config.api_key)
        except ValueError:
            test_result = {
                "success": False,
                "message": "API Key 无法解密，请在系统配置中编辑该 AI 配置并重新填写 API Key（可能是 SECRET_KEY 变更导致历史加密数据不可解密）",
            }
            return ResponseModel(
                code=200,
                message="AI配置测试完成",
                data=test_result,
            )
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        api_base = config.api_base or ""

        # 根据不同provider构建不同的测试请求
        if config.provider.lower() == "openai" or "chat/completions" in api_base:
            test_data = {
                "model": config.model,
                "messages": [{"role": "user", "content": "Hello"}],
                "max_tokens": min(config.max_tokens or 10, 10),
                "temperature": config.temperature or 0.7
            }
            test_url = api_base or "https://api.openai.com/v1/chat/completions"
        else:
            # 对于其他provider，使用通用测试
            test_data = {
                "model": config.model,
                "prompt": "Hello",
                "max_tokens": min(config.max_tokens or 10, 10),
                "temperature": config.temperature or 0.7
            }
            test_url = api_base or "https://api.openai.com/v1/completions"
        
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
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """激活AI配置"""
    try:
        config = db.query(AIConfig).filter(AIConfig.id == config_id).first()
        if not config:
            raise HTTPException(status_code=404, detail="AI配置不存在")

        config.is_active = True
        db.commit()
        db.refresh(config)

        return ResponseModel(
            code=200,
            message="AI配置已激活",
            data=None
        )
    except HTTPException:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI配置激活失败: {str(exc)}",
        )

@router.post("/{config_id}/deactivate", response_model=ResponseModel)
async def deactivate_ai_config(
    config_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """停用AI配置"""
    try:
        config = db.query(AIConfig).filter(AIConfig.id == config_id).first()
        if not config:
            raise HTTPException(status_code=404, detail="AI配置不存在")

        config.is_active = False
        db.commit()
        db.refresh(config)

        return ResponseModel(
            code=200,
            message="AI配置已停用",
            data=None
        )
    except HTTPException:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI配置停用失败: {str(exc)}",
        )
