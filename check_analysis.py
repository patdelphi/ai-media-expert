#!/usr/bin/env python3
"""
检查视频分析记录和关联的视频文件
"""

from app.core.database import SessionLocal
from app.models.video_analysis import VideoAnalysis
from app.models.uploaded_file import UploadedFile
import os

def check_analysis(analysis_id):
    db = SessionLocal()
    try:
        analysis = db.query(VideoAnalysis).filter(VideoAnalysis.id == analysis_id).first()
        
        if not analysis:
            print(f"Analysis {analysis_id} not found")
            return
        
        print(f"=== Analysis {analysis_id} ===")
        print(f"Status: {analysis.status}")
        print(f"Error: {analysis.error_message}")
        print(f"Error Code: {analysis.error_code}")
        print(f"Video file ID: {analysis.video_file_id}")
        print(f"Video file path: {analysis.video_file_path}")
        print(f"Video URL: {analysis.video_url}")
        print(f"Transmission method: {analysis.transmission_method}")
        
        # 检查关联的视频文件记录
        video_file = db.query(UploadedFile).filter(UploadedFile.id == analysis.video_file_id).first()
        if video_file:
            print(f"\n=== Video File Record ===")
            print(f"ID: {video_file.id}")
            print(f"Original filename: {video_file.original_filename}")
            print(f"File path: {video_file.file_path}")
            print(f"File size: {video_file.file_size}")
            
            # 检查文件是否存在
            if video_file.file_path:
                exists = os.path.exists(video_file.file_path)
                print(f"File exists: {exists}")
                if exists:
                    actual_size = os.path.getsize(video_file.file_path)
                    print(f"Actual file size: {actual_size} bytes ({actual_size/1024/1024:.2f} MB)")
                else:
                    print(f"File not found at: {video_file.file_path}")
            else:
                print("File path is None in database")
        else:
            print(f"\nVideo file record {analysis.video_file_id} not found in database")
        
    finally:
        db.close()

if __name__ == "__main__":
    check_analysis(66)