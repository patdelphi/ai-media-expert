"""提示词模板API接口

提供提示词模板的 CRUD、权限控制和使用统计接口。
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_admin
from app.core.database import get_db
from app.models.prompt_template import PromptTemplate
from app.models.user import User
from app.schemas.common import ResponseModel
from app.schemas.prompt_template import (
    PromptTemplateCreate,
    PromptTemplateResponse,
    PromptTemplateUpdate,
)

router = APIRouter()


def _is_admin(user: User) -> bool:
    return user.is_superuser or user.role == "admin"


def _get_prompt_template_for_user(
    db: Session,
    template_id: int,
    current_user: User,
) -> PromptTemplate:
    template = db.query(PromptTemplate).filter(PromptTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="提示词模板不存在")
    if not _is_admin(current_user) and not template.is_active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="提示词模板不存在")
    return template


@router.post("/", response_model=ResponseModel[PromptTemplateResponse])
async def create_prompt_template(
    template: PromptTemplateCreate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """创建提示词模板"""
    try:
        existing = db.query(PromptTemplate).filter(PromptTemplate.title == template.title).first()
        if existing:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="模板标题已存在")

        db_template = PromptTemplate(**template.model_dump())
        db.add(db_template)
        db.commit()
        db.refresh(db_template)

        return ResponseModel(
            code=200,
            message="提示词模板创建成功",
            data=db_template
        )
    except HTTPException:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"提示词模板创建失败: {str(exc)}",
        )


@router.get("/", response_model=ResponseModel[List[PromptTemplateResponse]])
async def get_prompt_templates(
    include_inactive: bool = False,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取提示词模板列表"""
    query = db.query(PromptTemplate)
    if include_inactive and not _is_admin(current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="权限不足")
    if not include_inactive or not _is_admin(current_user):
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
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取单个提示词模板详情"""
    template = _get_prompt_template_for_user(db, template_id, current_user)

    return ResponseModel(
        code=200,
        message="提示词模板获取成功",
        data=template
    )


@router.put("/{template_id}", response_model=ResponseModel[PromptTemplateResponse])
async def update_prompt_template(
    template_id: int,
    template_update: PromptTemplateUpdate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """更新提示词模板"""
    try:
        template = db.query(PromptTemplate).filter(PromptTemplate.id == template_id).first()
        if not template:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="提示词模板不存在")

        if template_update.title and template_update.title != template.title:
            existing = db.query(PromptTemplate).filter(
                PromptTemplate.title == template_update.title,
                PromptTemplate.id != template_id
            ).first()
            if existing:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="模板标题已存在")

        for field, value in template_update.model_dump(exclude_unset=True).items():
            setattr(template, field, value)

        db.commit()
        db.refresh(template)

        return ResponseModel(
            code=200,
            message="提示词模板更新成功",
            data=template
        )
    except HTTPException:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"提示词模板更新失败: {str(exc)}",
        )


@router.delete("/{template_id}", response_model=ResponseModel)
async def delete_prompt_template(
    template_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """删除提示词模板"""
    try:
        template = db.query(PromptTemplate).filter(PromptTemplate.id == template_id).first()
        if not template:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="提示词模板不存在")

        db.delete(template)
        db.commit()

        return ResponseModel(
            code=200,
            message="提示词模板删除成功",
            data=None
        )
    except HTTPException:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"提示词模板删除失败: {str(exc)}",
        )


@router.post("/{template_id}/use", response_model=ResponseModel)
async def use_prompt_template(
    template_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """使用提示词模板（增加使用次数）"""
    try:
        template = _get_prompt_template_for_user(db, template_id, current_user)
        template.usage_count += 1
        db.commit()

        return ResponseModel(
            code=200,
            message="模板使用次数已更新",
            data=None
        )
    except HTTPException:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"模板使用次数更新失败: {str(exc)}",
        )
