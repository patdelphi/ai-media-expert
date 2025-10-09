#!/usr/bin/env python3
"""检查数据库中的视频比例数据

验证video_ratio字段是否正确存储和显示。
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.database import get_db
from app.models.uploaded_file import UploadedFile
from sqlalchemy.orm import Session

def check_video_ratio_data():
    """检查视频比例数据"""
    print("=== 检查视频比例数据 ===")
    
    # 获取数据库会话
    db = next(get_db())
    
    try:
        # 查询最新的5个文件
        files = db.query(UploadedFile).order_by(UploadedFile.created_at.desc()).limit(5).all()
        
        if not files:
            print("❌ 数据库中没有文件")
            return
        
        print(f"✅ 找到 {len(files)} 个文件:\n")
        
        for i, file in enumerate(files, 1):
            print(f"📁 文件 #{i}:")
            print(f"  原始文件名: {file.original_filename}")
            print(f"  文件大小: {file.file_size} bytes ({file.file_size / 1024 / 1024:.2f} MB)")
            
            # 基本视频信息
            if file.duration:
                minutes = int(file.duration // 60)
                seconds = int(file.duration % 60)
                print(f"  时长: {minutes}:{seconds:02d}")
            
            if file.width and file.height:
                print(f"  分辨率: {file.width}×{file.height}")
            
            if file.format_name:
                print(f"  格式: {file.format_name.upper()}")
            
            # 宽高比和视频比例
            if file.aspect_ratio:
                print(f"  宽高比: {file.aspect_ratio}")
            
            if file.video_ratio:
                print(f"  视频比例: {file.video_ratio}")
            else:
                print(f"  ⚠️  视频比例: 未设置")
            
            # 帧率和比特率
            if file.frame_rate:
                print(f"  帧率: {file.frame_rate}")
            
            if file.bit_rate:
                mbps = file.bit_rate / 1000000
                print(f"  比特率: {mbps:.1f} Mbps")
            
            # 音频信息
            if file.channels:
                print(f"  音频: {file.channels}声道")
            
            if file.sample_rate:
                khz = file.sample_rate / 1000
                print(f"  采样率: {khz:.1f}kHz")
            
            # 时间信息
            if file.file_created_at:
                print(f"  文件创建时间: {file.file_created_at.strftime('%Y/%m/%d %H:%M:%S')}")
            
            print(f"  文件上传时间: {file.created_at.strftime('%Y/%m/%d %H:%M:%S')}")
            
            print("-" * 60)
        
        # 统计video_ratio字段的情况
        total_files = db.query(UploadedFile).count()
        files_with_ratio = db.query(UploadedFile).filter(UploadedFile.video_ratio.isnot(None)).count()
        files_without_ratio = total_files - files_with_ratio
        
        print(f"\n📊 统计信息:")
        print(f"  总文件数: {total_files}")
        print(f"  有视频比例: {files_with_ratio}")
        print(f"  无视频比例: {files_without_ratio}")
        
        if files_without_ratio > 0:
            print(f"\n⚠️  建议运行迁移脚本更新缺失的视频比例数据")
        
    except Exception as e:
        print(f"❌ 检查失败: {e}")
    finally:
        db.close()

def main():
    """主函数"""
    check_video_ratio_data()

if __name__ == "__main__":
    main()