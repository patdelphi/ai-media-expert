#!/usr/bin/env python3
"""检查数据库中的视频信息数据

检查上传的视频文件是否正确存储了ffprobe解析的信息。
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text
from app.core.database import engine

def check_video_data():
    """检查数据库中的视频数据"""
    print("=== 检查数据库中的视频信息 ===")
    
    try:
        with engine.connect() as conn:
            # 查询最近5个上传的文件
            result = conn.execute(text("""
                SELECT 
                    original_filename,
                    saved_filename,
                    file_size,
                    duration,
                    width,
                    height,
                    video_codec,
                    audio_codec,
                    bit_rate,
                    frame_rate,
                    format_name,
                    created_at
                FROM uploaded_files 
                ORDER BY created_at DESC 
                LIMIT 5
            """))
            
            files = result.fetchall()
            
            if not files:
                print("❌ 数据库中没有找到上传的文件")
                return
            
            print(f"✅ 找到 {len(files)} 个文件:")
            print()
            
            for i, file in enumerate(files, 1):
                print(f"📁 文件 #{i}:")
                print(f"  原始文件名: {file.original_filename}")
                print(f"  存储文件名: {file.saved_filename}")
                print(f"  文件大小: {file.file_size} bytes")
                print(f"  时长: {file.duration} 秒")
                print(f"  分辨率: {file.width}×{file.height}")
                print(f"  视频编码: {file.video_codec}")
                print(f"  音频编码: {file.audio_codec}")
                print(f"  比特率: {file.bit_rate}")
                print(f"  帧率: {file.frame_rate}")
                print(f"  格式: {file.format_name}")
                print(f"  上传时间: {file.created_at}")
                print()
                
                # 检查视频信息是否完整
                missing_fields = []
                if not file.duration:
                    missing_fields.append('duration')
                if not file.width or not file.height:
                    missing_fields.append('resolution')
                if not file.video_codec:
                    missing_fields.append('video_codec')
                if not file.audio_codec:
                    missing_fields.append('audio_codec')
                    
                if missing_fields:
                    print(f"  ⚠️  缺少字段: {', '.join(missing_fields)}")
                else:
                    print(f"  ✅ 视频信息完整")
                print("-" * 50)
                
    except Exception as e:
        print(f"❌ 查询数据库失败: {e}")

if __name__ == "__main__":
    check_video_data()