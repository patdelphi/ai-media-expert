#!/usr/bin/env python3
"""添加视频下载配置项的数据库迁移脚本

为system_config表添加视频下载相关的配置项，包括：
- 平台cookie配置
- 下载路径设置
- 并发数限制
- 其他下载相关配置
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.core.database import get_db
from app.models.system_config import SystemConfig
from app.core.app_logging import download_logger as logger


def add_download_configs():
    """添加视频下载相关的系统配置项"""
    
    # 视频下载配置项列表
    download_configs = [
        {
            'key': 'download.default_path',
            'value': '~/Downloads/ai-media-expert',
            'description': '默认下载路径',
            'category': 'download',
            'data_type': 'string',
            'is_public': False
        },
        {
            'key': 'download.max_concurrent',
            'value': '3',
            'description': '最大并发下载数',
            'category': 'download',
            'data_type': 'integer',
            'is_public': False
        },
        {
            'key': 'download.timeout',
            'value': '300',
            'description': '下载超时时间（秒）',
            'category': 'download',
            'data_type': 'integer',
            'is_public': False
        },
        {
            'key': 'download.retry_count',
            'value': '3',
            'description': '下载失败重试次数',
            'category': 'download',
            'data_type': 'integer',
            'is_public': False
        },
        {
            'key': 'download.auto_cleanup',
            'value': 'true',
            'description': '是否自动清理失败的下载文件',
            'category': 'download',
            'data_type': 'boolean',
            'is_public': False
        },
        {
            'key': 'download.cleanup_days',
            'value': '7',
            'description': '下载文件保留天数（0表示永久保留）',
            'category': 'download',
            'data_type': 'integer',
            'is_public': False
        },
        # 平台Cookie配置
        {
            'key': 'platform.douyin.cookie',
            'value': '',
            'description': '抖音平台Cookie（用于绕过反爬限制）',
            'category': 'platform',
            'data_type': 'text',
            'is_public': False
        },
        {
            'key': 'platform.tiktok.cookie',
            'value': '',
            'description': 'TikTok平台Cookie',
            'category': 'platform',
            'data_type': 'text',
            'is_public': False
        },
        {
            'key': 'platform.bilibili.cookie',
            'value': '',
            'description': 'B站平台Cookie',
            'category': 'platform',
            'data_type': 'text',
            'is_public': False
        },
        {
            'key': 'platform.xiaohongshu.cookie',
            'value': '',
            'description': '小红书平台Cookie',
            'category': 'platform',
            'data_type': 'text',
            'is_public': False
        },
        {
            'key': 'platform.kuaishou.cookie',
            'value': '',
            'description': '快手平台Cookie',
            'category': 'platform',
            'data_type': 'text',
            'is_public': False
        },
        {
            'key': 'platform.weixin.cookie',
            'value': '',
            'description': '微信视频号Cookie',
            'category': 'platform',
            'data_type': 'text',
            'is_public': False
        },
        # 平台启用状态
        {
            'key': 'platform.douyin.enabled',
            'value': 'true',
            'description': '是否启用抖音平台解析',
            'category': 'platform',
            'data_type': 'boolean',
            'is_public': True
        },
        {
            'key': 'platform.tiktok.enabled',
            'value': 'true',
            'description': '是否启用TikTok平台解析',
            'category': 'platform',
            'data_type': 'boolean',
            'is_public': True
        },
        {
            'key': 'platform.bilibili.enabled',
            'value': 'true',
            'description': '是否启用B站平台解析',
            'category': 'platform',
            'data_type': 'boolean',
            'is_public': True
        },
        {
            'key': 'platform.xiaohongshu.enabled',
            'value': 'true',
            'description': '是否启用小红书平台解析',
            'category': 'platform',
            'data_type': 'boolean',
            'is_public': True
        },
        {
            'key': 'platform.kuaishou.enabled',
            'value': 'true',
            'description': '是否启用快手平台解析',
            'category': 'platform',
            'data_type': 'boolean',
            'is_public': True
        },
        {
            'key': 'platform.weixin.enabled',
            'value': 'true',
            'description': '是否启用微信视频号解析',
            'category': 'platform',
            'data_type': 'boolean',
            'is_public': True
        },
        # 下载质量和格式配置
        {
            'key': 'download.default_format',
            'value': 'mp4',
            'description': '默认下载格式',
            'category': 'download',
            'data_type': 'string',
            'is_public': True
        },
        {
            'key': 'download.default_quality',
            'value': '1080p',
            'description': '默认下载质量',
            'category': 'download',
            'data_type': 'string',
            'is_public': True
        },
        {
            'key': 'download.supported_formats',
            'value': 'mp4,webm,mkv,avi,mov',
            'description': '支持的下载格式列表',
            'category': 'download',
            'data_type': 'string',
            'is_public': True
        },
        {
            'key': 'download.supported_qualities',
            'value': '144p,240p,360p,480p,720p,1080p,2K,4K',
            'description': '支持的下载质量列表',
            'category': 'download',
            'data_type': 'string',
            'is_public': True
        },
        # 用户代理配置
        {
            'key': 'download.user_agent',
            'value': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'description': '下载时使用的User-Agent',
            'category': 'download',
            'data_type': 'text',
            'is_public': False
        },
        # 代理配置
        {
            'key': 'download.proxy.enabled',
            'value': 'false',
            'description': '是否启用代理',
            'category': 'download',
            'data_type': 'boolean',
            'is_public': False
        },
        {
            'key': 'download.proxy.url',
            'value': '',
            'description': '代理服务器URL',
            'category': 'download',
            'data_type': 'string',
            'is_public': False
        },
        # 通知配置
        {
            'key': 'download.notifications.enabled',
            'value': 'true',
            'description': '是否启用下载完成通知',
            'category': 'download',
            'data_type': 'boolean',
            'is_public': True
        }
    ]
    
    try:
        # 获取数据库会话
        db = next(get_db())
        
        logger.info("开始添加视频下载配置项")
        
        added_count = 0
        updated_count = 0
        
        for config_data in download_configs:
            # 检查配置项是否已存在
            existing_config = db.query(SystemConfig).filter(
                SystemConfig.key == config_data['key']
            ).first()
            
            if existing_config:
                # 更新现有配置项的描述和类别
                existing_config.description = config_data['description']
                existing_config.category = config_data['category']
                existing_config.data_type = config_data['data_type']
                existing_config.is_public = config_data['is_public']
                updated_count += 1
                logger.info(f"更新配置项: {config_data['key']}")
            else:
                # 创建新的配置项
                new_config = SystemConfig(
                    key=config_data['key'],
                    value=config_data['value'],
                    description=config_data['description'],
                    category=config_data['category'],
                    data_type=config_data['data_type'],
                    is_public=config_data['is_public']
                )
                db.add(new_config)
                added_count += 1
                logger.info(f"添加配置项: {config_data['key']}")
        
        # 提交更改
        db.commit()
        
        logger.info(
            f"视频下载配置项添加完成: 新增 {added_count} 项，更新 {updated_count} 项"
        )
        
        return True
        
    except Exception as e:
        logger.error(f"添加视频下载配置项失败: {str(e)}")
        db.rollback()
        return False
    
    finally:
        db.close()


def main():
    """主函数"""
    print("开始添加视频下载配置项...")
    
    success = add_download_configs()
    
    if success:
        print("✅ 视频下载配置项添加成功！")
        print("\n已添加的配置类别:")
        print("- download: 下载相关配置")
        print("- platform: 平台相关配置")
        print("\n主要配置项:")
        print("- 下载路径、并发数、超时时间")
        print("- 各平台Cookie和启用状态")
        print("- 默认格式和质量设置")
        print("- 代理和通知配置")
    else:
        print("❌ 视频下载配置项添加失败！")
        sys.exit(1)


if __name__ == "__main__":
    main()