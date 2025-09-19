#!/usr/bin/env python3
"""
测试视频Base64编码功能

验证视频文件的Base64编码和ffmpeg压缩功能是否正常工作。
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent))

from app.utils.video_base64 import video_base64_encoder
from app.core.logging import api_logger

def test_base64_encoding():
    """测试Base64编码功能"""
    print("=== 测试视频Base64编码功能 ===")
    
    # 查找测试视频文件
    uploads_dir = Path("uploads/videos")
    
    if not uploads_dir.exists():
        print("❌ uploads/videos 目录不存在")
        return False
    
    video_files = list(uploads_dir.glob("*.mp4"))
    
    if not video_files:
        print("❌ 没有找到视频文件")
        return False
    
    print(f"✅ 找到 {len(video_files)} 个视频文件")
    
    # 测试第一个视频文件
    test_file = video_files[0]
    print(f"\n🎬 测试文件: {test_file.name}")
    print(f"📁 文件路径: {test_file}")
    
    file_size_mb = test_file.stat().st_size / (1024 * 1024)
    print(f"📊 文件大小: {file_size_mb:.2f} MB")
    
    # 检查ffmpeg可用性
    print("\n🔧 检查ffmpeg可用性...")
    ffmpeg_available = video_base64_encoder.check_ffmpeg_available()
    if ffmpeg_available:
        print("✅ FFmpeg可用")
    else:
        print("❌ FFmpeg不可用，将无法压缩视频")
    
    # 检查文件是否适合Base64编码
    print("\n📋 检查文件适用性...")
    suitable, reason = video_base64_encoder.is_suitable_for_base64(str(test_file))
    print(f"适合Base64编码: {suitable}")
    print(f"原因: {reason}")
    
    if not suitable and not ffmpeg_available:
        print("❌ 文件过大且无法压缩，跳过编码测试")
        return False
    
    # 尝试Base64编码
    print("\n🔄 开始Base64编码...")
    try:
        base64_data = video_base64_encoder.encode_video_to_base64(
            str(test_file), 
            compress=True
        )
        
        if base64_data:
            print(f"✅ Base64编码成功")
            print(f"📏 编码长度: {len(base64_data):,} 字符")
            print(f"💾 估计大小: {len(base64_data) * 3 / 4 / (1024 * 1024):.2f} MB")
            
            # 显示前100个字符作为示例
            print(f"🔍 编码示例: {base64_data[:100]}...")
            
            return True
        else:
            print("❌ Base64编码失败")
            return False
            
    except Exception as e:
        print(f"❌ Base64编码异常: {e}")
        return False

def test_compression():
    """测试视频压缩功能"""
    print("\n=== 测试视频压缩功能 ===")
    
    # 查找测试视频文件
    uploads_dir = Path("uploads/videos")
    video_files = list(uploads_dir.glob("*.mp4"))
    
    if not video_files:
        print("❌ 没有找到视频文件")
        return False
    
    test_file = video_files[0]
    original_size_mb = test_file.stat().st_size / (1024 * 1024)
    
    print(f"🎬 测试文件: {test_file.name}")
    print(f"📊 原始大小: {original_size_mb:.2f} MB")
    
    if not video_base64_encoder.check_ffmpeg_available():
        print("❌ FFmpeg不可用，无法测试压缩")
        return False
    
    # 尝试压缩
    print("\n🔄 开始压缩视频...")
    try:
        compressed_path = video_base64_encoder.compress_video(
            str(test_file),
            target_size_mb=5.0
        )
        
        if compressed_path and compressed_path != str(test_file):
            compressed_size_mb = os.path.getsize(compressed_path) / (1024 * 1024)
            compression_ratio = compressed_size_mb / original_size_mb
            
            print(f"✅ 压缩成功")
            print(f"📁 压缩文件: {compressed_path}")
            print(f"📊 压缩后大小: {compressed_size_mb:.2f} MB")
            print(f"📉 压缩比例: {compression_ratio:.2%}")
            
            # 清理临时文件
            try:
                os.remove(compressed_path)
                print(f"🗑️ 已清理临时文件")
            except Exception as e:
                print(f"⚠️ 清理临时文件失败: {e}")
            
            return True
        else:
            print("❌ 压缩失败或文件已经足够小")
            return False
            
    except Exception as e:
        print(f"❌ 压缩异常: {e}")
        return False

def main():
    """主函数"""
    print("🚀 开始测试视频Base64编码功能\n")
    
    # 测试Base64编码
    encoding_success = test_base64_encoding()
    
    # 测试压缩功能
    compression_success = test_compression()
    
    # 总结
    print("\n" + "="*50)
    print("📊 测试结果总结:")
    print(f"Base64编码: {'✅ 成功' if encoding_success else '❌ 失败'}")
    print(f"视频压缩: {'✅ 成功' if compression_success else '❌ 失败'}")
    
    if encoding_success:
        print("\n🎉 Base64编码功能可以正常使用！")
        print("💡 建议：")
        print("  - 小文件（<5MB）直接使用Base64编码")
        print("  - 大文件先压缩再编码")
        print("  - 超大文件（>20MB）建议使用其他传输方式")
    else:
        print("\n⚠️ Base64编码功能存在问题，请检查：")
        print("  - FFmpeg是否正确安装")
        print("  - 视频文件是否存在且可读")
        print("  - 系统资源是否充足")
    
    return encoding_success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)