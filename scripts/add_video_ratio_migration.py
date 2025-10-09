#!/usr/bin/env python3
"""添加视频比例字段的数据库迁移脚本

为uploaded_files表添加video_ratio字段，用于存储标准视频比例（如9:16, 16:9等）。
"""

import sqlite3
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def add_video_ratio_field():
    """添加video_ratio字段到uploaded_files表"""
    db_path = project_root / "ai_media_expert.db"
    
    if not db_path.exists():
        print(f"❌ 数据库文件不存在: {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 检查字段是否已存在
        cursor.execute("PRAGMA table_info(uploaded_files)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'video_ratio' in columns:
            print("✅ video_ratio字段已存在，无需添加")
            return True
        
        # 添加video_ratio字段
        cursor.execute("""
            ALTER TABLE uploaded_files 
            ADD COLUMN video_ratio VARCHAR(20)
        """)
        
        conn.commit()
        print("✅ 成功添加video_ratio字段")
        
        # 验证字段添加成功
        cursor.execute("PRAGMA table_info(uploaded_files)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'video_ratio' in columns:
            print("✅ 字段验证成功")
            return True
        else:
            print("❌ 字段验证失败")
            return False
            
    except sqlite3.Error as e:
        print(f"❌ 数据库操作失败: {e}")
        return False
    finally:
        if conn:
            conn.close()

def update_existing_records():
    """更新现有记录的video_ratio字段"""
    db_path = project_root / "ai_media_expert.db"
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 查询有宽高信息但没有video_ratio的记录
        cursor.execute("""
            SELECT id, width, height 
            FROM uploaded_files 
            WHERE width IS NOT NULL AND height IS NOT NULL 
            AND (video_ratio IS NULL OR video_ratio = '')
        """)
        
        records = cursor.fetchall()
        print(f"📊 找到 {len(records)} 条需要更新的记录")
        
        updated_count = 0
        for record_id, width, height in records:
            if width and height:
                # 计算标准比例
                def gcd(a, b):
                    while b:
                        a, b = b, a % b
                    return a
                
                # 简化比例
                common_divisor = gcd(width, height)
                simplified_width = width // common_divisor
                simplified_height = height // common_divisor
                
                # 如果比例过大，尝试找到最接近的标准比例
                if simplified_width > 50 or simplified_height > 50:
                    standard_ratios = [
                        (16, 9), (9, 16), (4, 3), (3, 4), (1, 1),
                        (21, 9), (9, 21), (5, 4), (4, 5)
                    ]
                    
                    current_ratio = width / height
                    best_match = None
                    min_diff = float('inf')
                    
                    for w, h in standard_ratios:
                        ratio = w / h
                        diff = abs(current_ratio - ratio)
                        if diff < min_diff:
                            min_diff = diff
                            best_match = (w, h)
                    
                    if best_match and min_diff < 0.1:  # 允许10%的误差
                        simplified_width, simplified_height = best_match
                
                video_ratio = f"{simplified_width}:{simplified_height}"
                
                # 更新记录
                cursor.execute("""
                    UPDATE uploaded_files 
                    SET video_ratio = ? 
                    WHERE id = ?
                """, (video_ratio, record_id))
                
                updated_count += 1
                print(f"✅ 更新记录 {record_id}: {width}×{height} → {video_ratio}")
        
        conn.commit()
        print(f"✅ 成功更新 {updated_count} 条记录")
        
    except sqlite3.Error as e:
        print(f"❌ 更新记录失败: {e}")
        return False
    finally:
        if conn:
            conn.close()
    
    return True

def main():
    """主函数"""
    print("=== 添加视频比例字段迁移 ===")
    
    # 添加字段
    if not add_video_ratio_field():
        print("❌ 迁移失败")
        return
    
    # 更新现有记录
    if not update_existing_records():
        print("❌ 更新现有记录失败")
        return
    
    print("✅ 迁移完成！")

if __name__ == "__main__":
    main()