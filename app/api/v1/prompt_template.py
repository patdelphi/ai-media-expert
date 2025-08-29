"""提示词模板API接口

提供提示词模板的CRUD操作接口。
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.models.prompt_template import PromptTemplate
from app.schemas.prompt_template import PromptTemplateCreate, PromptTemplateUpdate, PromptTemplateResponse
from app.schemas.common import ResponseModel

router = APIRouter()


@router.post("/", response_model=ResponseModel[PromptTemplateResponse])
async def create_prompt_template(
    template: PromptTemplateCreate,
    db: Session = Depends(get_db)
):
    """创建提示词模板"""
    
    # 检查标题是否已存在
    existing = db.query(PromptTemplate).filter(PromptTemplate.title == template.title).first()
    if existing:
        raise HTTPException(status_code=400, detail="模板标题已存在")
    
    db_template = PromptTemplate(**template.dict())
    db.add(db_template)
    db.commit()
    db.refresh(db_template)
    
    return ResponseModel(
        code=200,
        message="提示词模板创建成功",
        data=db_template
    )


@router.get("/", response_model=ResponseModel[List[PromptTemplateResponse]])
async def get_prompt_templates(
    include_inactive: bool = False,
    db: Session = Depends(get_db)
):
    """获取提示词模板列表"""
    
    query = db.query(PromptTemplate)
    if not include_inactive:
        query = query.filter(PromptTemplate.is_active == True)
    
    templates = query.order_by(PromptTemplate.created_at.desc()).all()
    return ResponseModel(
        code=200,
        message="提示词模板列表获取成功",
        data=templates
    )


@router.get("/{template_id}", response_model=ResponseModel[PromptTemplateResponse])
async def get_prompt_template(
    template_id: int,
    db: Session = Depends(get_db)
):
    """获取单个提示词模板详情"""
    
    template = db.query(PromptTemplate).filter(PromptTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="提示词模板不存在")
    
    return ResponseModel(
        code=200,
        message="提示词模板获取成功",
        data=template
    )


@router.put("/{template_id}", response_model=ResponseModel[PromptTemplateResponse])
async def update_prompt_template(
    template_id: int,
    template_update: PromptTemplateUpdate,
    db: Session = Depends(get_db)
):
    """更新提示词模板"""
    
    template = db.query(PromptTemplate).filter(PromptTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="提示词模板不存在")
    
    # 检查标题是否与其他模板冲突
    if template_update.title and template_update.title != template.title:
        existing = db.query(PromptTemplate).filter(
            PromptTemplate.title == template_update.title,
            PromptTemplate.id != template_id
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="模板标题已存在")
    
    # 更新字段
    for field, value in template_update.dict(exclude_unset=True).items():
        setattr(template, field, value)
    
    db.commit()
    db.refresh(template)
    
    return ResponseModel(
        code=200,
        message="提示词模板更新成功",
        data=template
    )


@router.delete("/{template_id}", response_model=ResponseModel)
async def delete_prompt_template(
    template_id: int,
    db: Session = Depends(get_db)
):
    """删除提示词模板"""
    
    template = db.query(PromptTemplate).filter(PromptTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="提示词模板不存在")
    
    db.delete(template)
    db.commit()
    
    return ResponseModel(
        code=200,
        message="提示词模板删除成功",
        data=None
    )


@router.post("/{template_id}/use", response_model=ResponseModel)
async def use_prompt_template(
    template_id: int,
    db: Session = Depends(get_db)
):
    """使用提示词模板（增加使用次数）"""
    
    template = db.query(PromptTemplate).filter(PromptTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="提示词模板不存在")
    
    template.usage_count += 1
    db.commit()
    
    return ResponseModel(
        code=200,
        message="模板使用次数已更新",
        data=None
    )