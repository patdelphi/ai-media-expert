"""标签组管理API端点

提供标签组和标签的CRUD操作接口。
"""

from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.api.deps import get_current_user, get_db, require_admin
from app.models.user import User
from app.models.tag_group import TagGroup, TagGroupTag
from app.schemas.tag_group import (
    TagGroupCreate, TagGroupUpdate, TagGroupResponse, TagGroupListResponse,
    TagCreate, TagUpdate, TagResponse, BatchTagOperation, TagGroupSearchParams
)
from app.schemas.common import ResponseModel, PaginatedResponse
from app.core.app_logging import api_logger

router = APIRouter()


@router.get("/", response_model=ResponseModel[List[TagGroupResponse]])
def get_tag_groups(
    search: Optional[str] = Query(None, description="搜索关键词"),
    is_active: Optional[bool] = Query(None, description="是否激活"),
    include_tags: bool = Query(True, description="是否包含标签列表"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """获取标签组列表
    
    获取所有标签组，支持搜索和筛选。
    """
    query = db.query(TagGroup)
    
    # 搜索条件
    if search:
        query = query.filter(
            or_(
                TagGroup.name.ilike(f"%{search}%"),
                TagGroup.description.ilike(f"%{search}%")
            )
        )
    
    # 状态筛选
    if is_active is not None:
        query = query.filter(TagGroup.is_active == is_active)
    
    # 按创建时间排序
    tag_groups = query.order_by(TagGroup.created_at.desc()).all()
    
    # 转换为响应模型
    if include_tags:
        result = [TagGroupResponse.model_validate(group) for group in tag_groups]
    else:
        result = []
        for group in tag_groups:
            group_data = TagGroupListResponse.model_validate(group)
            group_data.tag_count = len(group.tags)
            result.append(group_data)
    
    api_logger.info(
        "Tag groups retrieved",
        user_id=current_user.id,
        count=len(result),
        search=search,
        is_active=is_active
    )
    
    return ResponseModel(
        code=200,
        message="Tag groups retrieved successfully",
        data=result
    )


@router.get("/{group_id}", response_model=ResponseModel[TagGroupResponse])
def get_tag_group(
    group_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """获取标签组详情
    
    根据ID获取标签组的详细信息。
    """
    tag_group = db.query(TagGroup).filter(TagGroup.id == group_id).first()
    if not tag_group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tag group not found"
        )
    
    return ResponseModel(
        code=200,
        message="Tag group retrieved successfully",
        data=TagGroupResponse.model_validate(tag_group)
    )


@router.post("/", response_model=ResponseModel[TagGroupResponse])
def create_tag_group(
    tag_group_data: TagGroupCreate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
) -> Any:
    """创建标签组
    
    创建新的标签组，可以同时创建标签。
    """
    # 检查标签组名称是否已存在
    existing_group = db.query(TagGroup).filter(TagGroup.name == tag_group_data.name).first()
    if existing_group:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tag group name already exists"
        )
    
    # 创建标签组
    tag_group = TagGroup(
        name=tag_group_data.name,
        description=tag_group_data.description,
        is_active=tag_group_data.is_active
    )
    db.add(tag_group)
    db.flush()  # 获取ID
    
    # 创建标签
    for tag_data in tag_group_data.tags:
        tag = TagGroupTag(
            name=tag_data.name,
            color=tag_data.color,
            tag_group_id=tag_group.id,
            is_active=tag_data.is_active
        )
        db.add(tag)
    
    db.commit()
    db.refresh(tag_group)
    
    api_logger.info(
        "Tag group created",
        admin_user_id=current_user.id,
        tag_group_id=tag_group.id,
        tag_group_name=tag_group.name,
        tag_count=len(tag_group_data.tags)
    )
    
    return ResponseModel(
        code=200,
        message="Tag group created successfully",
        data=TagGroupResponse.model_validate(tag_group)
    )


@router.put("/{group_id}", response_model=ResponseModel[TagGroupResponse])
def update_tag_group(
    group_id: int,
    tag_group_data: TagGroupUpdate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
) -> Any:
    """更新标签组
    
    更新标签组的基本信息。
    """
    tag_group = db.query(TagGroup).filter(TagGroup.id == group_id).first()
    if not tag_group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tag group not found"
        )
    
    # 检查名称是否与其他标签组冲突
    if tag_group_data.name and tag_group_data.name != tag_group.name:
        existing_group = db.query(TagGroup).filter(
            TagGroup.name == tag_group_data.name,
            TagGroup.id != group_id
        ).first()
        if existing_group:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tag group name already exists"
            )
    
    # 更新标签组信息
    update_data = tag_group_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(tag_group, field, value)
    
    db.commit()
    db.refresh(tag_group)
    
    api_logger.info(
        "Tag group updated",
        admin_user_id=current_user.id,
        tag_group_id=tag_group.id,
        updated_fields=list(update_data.keys())
    )
    
    return ResponseModel(
        code=200,
        message="Tag group updated successfully",
        data=TagGroupResponse.model_validate(tag_group)
    )


@router.delete("/{group_id}", response_model=ResponseModel[dict])
def delete_tag_group(
    group_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
) -> Any:
    """删除标签组
    
    删除标签组及其所有标签。
    """
    tag_group = db.query(TagGroup).filter(TagGroup.id == group_id).first()
    if not tag_group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tag group not found"
        )
    
    tag_group_name = tag_group.name
    tag_count = len(tag_group.tags)
    
    db.delete(tag_group)
    db.commit()
    
    api_logger.info(
        "Tag group deleted",
        admin_user_id=current_user.id,
        tag_group_id=group_id,
        tag_group_name=tag_group_name,
        deleted_tag_count=tag_count
    )
    
    return ResponseModel(
        code=200,
        message="Tag group deleted successfully",
        data={"message": f"Tag group '{tag_group_name}' and {tag_count} tags deleted"}
    )


# 标签相关接口

@router.post("/{group_id}/tags", response_model=ResponseModel[TagResponse])
def create_tag(
    group_id: int,
    tag_data: TagCreate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
) -> Any:
    """在标签组中创建标签
    
    在指定的标签组中创建新标签。
    """
    # 检查标签组是否存在
    tag_group = db.query(TagGroup).filter(TagGroup.id == group_id).first()
    if not tag_group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tag group not found"
        )
    
    # 检查标签名称在该组中是否已存在
    existing_tag = db.query(TagGroupTag).filter(
        TagGroupTag.tag_group_id == group_id,
        TagGroupTag.name == tag_data.name
    ).first()
    if existing_tag:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tag name already exists in this group"
        )
    
    # 创建标签
    tag = TagGroupTag(
        name=tag_data.name,
        color=tag_data.color,
        tag_group_id=group_id,
        is_active=tag_data.is_active
    )
    db.add(tag)
    db.commit()
    db.refresh(tag)
    
    api_logger.info(
        "Tag created",
        admin_user_id=current_user.id,
        tag_id=tag.id,
        tag_name=tag.name,
        tag_group_id=group_id
    )
    
    return ResponseModel(
        code=200,
        message="Tag created successfully",
        data=TagResponse.model_validate(tag)
    )


@router.put("/tags/{tag_id}", response_model=ResponseModel[TagResponse])
def update_tag(
    tag_id: int,
    tag_data: TagUpdate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
) -> Any:
    """更新标签
    
    更新指定标签的信息。
    """
    tag = db.query(TagGroupTag).filter(TagGroupTag.id == tag_id).first()
    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tag not found"
        )
    
    # 检查名称是否与同组其他标签冲突
    if tag_data.name and tag_data.name != tag.name:
        existing_tag = db.query(TagGroupTag).filter(
            TagGroupTag.tag_group_id == tag.tag_group_id,
            TagGroupTag.name == tag_data.name,
            TagGroupTag.id != tag_id
        ).first()
        if existing_tag:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tag name already exists in this group"
            )
    
    # 更新标签信息
    update_data = tag_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(tag, field, value)
    
    db.commit()
    db.refresh(tag)
    
    api_logger.info(
        "Tag updated",
        admin_user_id=current_user.id,
        tag_id=tag.id,
        updated_fields=list(update_data.keys())
    )
    
    return ResponseModel(
        code=200,
        message="Tag updated successfully",
        data=TagResponse.model_validate(tag)
    )


@router.delete("/tags/{tag_id}", response_model=ResponseModel[dict])
def delete_tag(
    tag_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
) -> Any:
    """删除标签
    
    删除指定的标签。
    """
    tag = db.query(TagGroupTag).filter(TagGroupTag.id == tag_id).first()
    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tag not found"
        )
    
    tag_name = tag.name
    tag_group_id = tag.tag_group_id
    
    db.delete(tag)
    db.commit()
    
    api_logger.info(
        "Tag deleted",
        admin_user_id=current_user.id,
        tag_id=tag_id,
        tag_name=tag_name,
        tag_group_id=tag_group_id
    )
    
    return ResponseModel(
        code=200,
        message="Tag deleted successfully",
        data={"message": f"Tag '{tag_name}' deleted"}
    )


@router.post("/{group_id}/tags/batch", response_model=ResponseModel[List[TagResponse]])
def batch_create_tags(
    group_id: int,
    batch_data: BatchTagOperation,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
) -> Any:
    """批量创建标签
    
    在指定标签组中批量创建标签。
    """
    # 检查标签组是否存在
    tag_group = db.query(TagGroup).filter(TagGroup.id == group_id).first()
    if not tag_group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tag group not found"
        )
    
    # 获取已存在的标签名称
    existing_tags = db.query(TagGroupTag.name).filter(TagGroupTag.tag_group_id == group_id).all()
    existing_names = {tag.name for tag in existing_tags}
    
    # 创建新标签
    new_tags = []
    for tag_name in batch_data.tags:
        if tag_name not in existing_names:
            tag = TagGroupTag(
                name=tag_name,
                tag_group_id=group_id,
                is_active=True
            )
            db.add(tag)
            new_tags.append(tag)
    
    db.commit()
    
    # 刷新所有新标签
    for tag in new_tags:
        db.refresh(tag)
    
    api_logger.info(
        "Tags batch created",
        admin_user_id=current_user.id,
        tag_group_id=group_id,
        created_count=len(new_tags),
        skipped_count=len(batch_data.tags) - len(new_tags)
    )
    
    return ResponseModel(
        code=200,
        message=f"Created {len(new_tags)} tags, skipped {len(batch_data.tags) - len(new_tags)} duplicates",
        data=[TagResponse.model_validate(tag) for tag in new_tags]
    )