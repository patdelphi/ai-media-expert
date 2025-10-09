#!/usr/bin/env python3
"""视频解析功能数据库迁移脚本

创建video_analyses表，用于存储视频解析任务信息。
"""

import sys
import os
from pathlib import Path
from datetime import datetime

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine, text
from app.core.config import settings
from app.core.database import get_db
from app.models.video_analysis import VideoAnalysis
from app.models.video import AIConfig
from app.models.prompt_template import PromptTemplate
from app.models.tag_group import TagGroup
from app.models.uploaded_file import UploadedFile


def create_video_analysis_table():
    """创建video_analyses表"""
    
    # 创建数据库引擎
    engine = create_engine(settings.database_url)
    
    print("开始创建video_analyses表...")
    
    # 创建表的SQL语句
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS video_analyses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        video_file_id INTEGER NOT NULL,
        template_id INTEGER,
        tag_group_ids JSON,
        prompt_content TEXT NOT NULL,
        ai_config_id INTEGER NOT NULL,
        status VARCHAR(20) DEFAULT 'pending' NOT NULL,
        progress INTEGER DEFAULT 0 NOT NULL,
        analysis_result TEXT,
        result_summary TEXT,
        result_metadata JSON,
        confidence_score FLOAT,
        quality_score FLOAT,
        processing_time FLOAT,
        token_usage JSON,
        cost_estimate FLOAT,
        error_message TEXT,
        error_code VARCHAR(50),
        error_details JSON,
        started_at DATETIME,
        completed_at DATETIME,
        is_active BOOLEAN DEFAULT 1 NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        
        FOREIGN KEY (video_file_id) REFERENCES uploaded_files (id),
        FOREIGN KEY (template_id) REFERENCES prompt_templates (id),
        FOREIGN KEY (ai_config_id) REFERENCES ai_configs (id)
    );
    """
    
    # 创建索引的SQL语句
    create_indexes_sql = [
        "CREATE INDEX IF NOT EXISTS idx_video_analyses_video_file_id ON video_analyses (video_file_id);",
        "CREATE INDEX IF NOT EXISTS idx_video_analyses_template_id ON video_analyses (template_id);",
        "CREATE INDEX IF NOT EXISTS idx_video_analyses_ai_config_id ON video_analyses (ai_config_id);",
        "CREATE INDEX IF NOT EXISTS idx_video_analyses_status ON video_analyses (status);",
        "CREATE INDEX IF NOT EXISTS idx_video_analyses_created_at ON video_analyses (created_at);",
        "CREATE INDEX IF NOT EXISTS idx_video_analyses_completed_at ON video_analyses (completed_at);"
    ]
    
    try:
        with engine.connect() as conn:
            # 创建表
            conn.execute(text(create_table_sql))
            print("✅ video_analyses表创建成功")
            
            # 创建索引
            for index_sql in create_indexes_sql:
                conn.execute(text(index_sql))
            print("✅ 索引创建成功")
            
            # 提交事务
            conn.commit()
            
    except Exception as e:
        print(f"❌ 创建表失败: {e}")
        return False
    
    return True


def check_dependencies():
    """检查依赖表是否存在"""
    
    engine = create_engine(settings.database_url)
    
    required_tables = [
        'uploaded_files',
        'prompt_templates', 
        'ai_configs',
        'tag_groups'
    ]
    
    print("检查依赖表...")
    
    try:
        with engine.connect() as conn:
            for table in required_tables:
                result = conn.execute(text(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name=:table_name"
                ), {"table_name": table})
                
                if not result.fetchone():
                    print(f"❌ 依赖表 {table} 不存在")
                    return False
                else:
                    print(f"✅ 依赖表 {table} 存在")
    
    except Exception as e:
        print(f"❌ 检查依赖表失败: {e}")
        return False
    
    return True


def create_sample_data():
    """创建示例数据"""
    
    engine = create_engine(settings.database_url)
    
    print("创建示例数据...")
    
    # 示例提示词模板
    sample_templates = [
        {
            "title": "视频内容分析模板",
            "content": "请分析这个视频的内容，包括：\n1. 视觉元素描述\n2. 音频内容分析\n3. 整体风格评价\n4. 适用场景建议"
        },
        {
            "title": "技术质量评估模板", 
            "content": "请从技术角度评估这个视频：\n1. 画面质量\n2. 音频质量\n3. 编码效率\n4. 兼容性分析\n5. 优化建议"
        },
        {
            "title": "营销价值分析模板",
            "content": "请分析这个视频的营销价值：\n1. 目标受众\n2. 传播潜力\n3. 情感共鸣点\n4. 改进建议\n5. 平台适配性"
        }
    ]
    
    # 示例标签组
    sample_tag_groups = [
        {
            "name": "视频类型",
            "description": "视频内容类型分类",
            "tags": [
                {"name": "教育", "color": "#3B82F6"},
                {"name": "娱乐", "color": "#EF4444"},
                {"name": "商业", "color": "#10B981"},
                {"name": "新闻", "color": "#F59E0B"}
            ]
        },
        {
            "name": "技术特征",
            "description": "视频技术特征标签",
            "tags": [
                {"name": "高清", "color": "#8B5CF6"},
                {"name": "4K", "color": "#EC4899"},
                {"name": "HDR", "color": "#06B6D4"},
                {"name": "慢动作", "color": "#84CC16"}
            ]
        },
        {
            "name": "内容风格",
            "description": "视频内容风格分类",
            "tags": [
                {"name": "正式", "color": "#6B7280"},
                {"name": "轻松", "color": "#F97316"},
                {"name": "专业", "color": "#1F2937"},
                {"name": "创意", "color": "#7C3AED"}
            ]
        }
    ]
    
    try:
        with engine.connect() as conn:
            # 插入示例模板
            for template in sample_templates:
                conn.execute(text("""
                    INSERT OR IGNORE INTO prompt_templates (title, content, is_active, usage_count)
                    VALUES (:title, :content, 1, 0)
                """), template)
            
            print(f"✅ 创建了 {len(sample_templates)} 个示例模板")
            
            # 插入示例标签组
            for tag_group in sample_tag_groups:
                # 插入标签组
                result = conn.execute(text("""
                    INSERT OR IGNORE INTO tag_groups (name, description, is_active)
                    VALUES (:name, :description, 1)
                """), {
                    "name": tag_group["name"],
                    "description": tag_group["description"]
                })
                
                # 获取标签组ID
                tag_group_id = conn.execute(text("""
                    SELECT id FROM tag_groups WHERE name = :name
                """), {"name": tag_group["name"]}).fetchone()
                
                if tag_group_id:
                    tag_group_id = tag_group_id[0]
                    
                    # 插入标签
                    for tag in tag_group["tags"]:
                        conn.execute(text("""
                            INSERT OR IGNORE INTO tag_group_tags (name, color, tag_group_id, is_active)
                            VALUES (:name, :color, :tag_group_id, 1)
                        """), {
                            "name": tag["name"],
                            "color": tag["color"],
                            "tag_group_id": tag_group_id
                        })
            
            print(f"✅ 创建了 {len(sample_tag_groups)} 个示例标签组")
            
            # 提交事务
            conn.commit()
            
    except Exception as e:
        print(f"❌ 创建示例数据失败: {e}")
        return False
    
    return True


def verify_migration():
    """验证迁移结果"""
    
    engine = create_engine(settings.database_url)
    
    print("验证迁移结果...")
    
    try:
        with engine.connect() as conn:
            # 检查表是否存在
            result = conn.execute(text(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='video_analyses'"
            ))
            
            if not result.fetchone():
                print("❌ video_analyses表不存在")
                return False
            
            # 检查表结构
            columns = conn.execute(text("PRAGMA table_info(video_analyses)")).fetchall()
            column_names = [col[1] for col in columns]
            
            required_columns = [
                'id', 'video_file_id', 'template_id', 'tag_group_ids',
                'prompt_content', 'ai_config_id', 'status', 'progress',
                'analysis_result', 'result_summary', 'confidence_score',
                'processing_time', 'error_message', 'created_at', 'updated_at'
            ]
            
            missing_columns = [col for col in required_columns if col not in column_names]
            if missing_columns:
                print(f"❌ 缺少字段: {missing_columns}")
                return False
            
            # 检查索引
            indexes = conn.execute(text("PRAGMA index_list(video_analyses)")).fetchall()
            index_names = [idx[1] for idx in indexes]
            
            required_indexes = [
                'idx_video_analyses_video_file_id',
                'idx_video_analyses_status',
                'idx_video_analyses_created_at'
            ]
            
            missing_indexes = [idx for idx in required_indexes if idx not in index_names]
            if missing_indexes:
                print(f"⚠️  缺少索引: {missing_indexes}")
            
            # 检查示例数据
            template_count = conn.execute(text("SELECT COUNT(*) FROM prompt_templates")).fetchone()[0]
            tag_group_count = conn.execute(text("SELECT COUNT(*) FROM tag_groups")).fetchone()[0]
            
            print(f"✅ 表结构验证通过")
            print(f"✅ 提示词模板数量: {template_count}")
            print(f"✅ 标签组数量: {tag_group_count}")
            
    except Exception as e:
        print(f"❌ 验证失败: {e}")
        return False
    
    return True


def main():
    """主函数"""
    print("=" * 60)
    print("视频解析功能数据库迁移")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # 检查依赖表
    if not check_dependencies():
        print("\n❌ 依赖表检查失败，请先运行基础表迁移")
        return False
    
    # 创建video_analyses表
    if not create_video_analysis_table():
        print("\n❌ 创建video_analyses表失败")
        return False
    
    # 创建示例数据
    if not create_sample_data():
        print("\n⚠️  创建示例数据失败，但表结构已创建")
    
    # 验证迁移结果
    if not verify_migration():
        print("\n❌ 迁移验证失败")
        return False
    
    print("\n" + "=" * 60)
    print("✅ 视频解析功能数据库迁移完成！")
    print("\n📋 已创建:")
    print("  - video_analyses 表")
    print("  - 相关索引")
    print("  - 示例提示词模板")
    print("  - 示例标签组")
    print("\n🚀 现在可以使用视频解析功能了！")
    print("=" * 60)
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)