"""上传文件模型

存储上传文件的元数据信息，包括原始文件名和实际存储文件名的映射。
"""

<<<<<<< HEAD
from sqlalchemy import Column, Integer, String, DateTime, BigInteger, ForeignKey
from sqlalchemy.orm import relationship
=======
from sqlalchemy import Column, Integer, String, DateTime, BigInteger
>>>>>>> ad3f17f (feat: 完善视频上传功能 - 修复时长格式化、上传时间显示、移除时间编辑按钮)
from sqlalchemy.sql import func
from app.core.database import Base


class UploadedFile(Base):
    """上传文件模型"""
    __tablename__ = "uploaded_files"

    id = Column(Integer, primary_key=True, index=True)
<<<<<<< HEAD
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
=======
>>>>>>> ad3f17f (feat: 完善视频上传功能 - 修复时长格式化、上传时间显示、移除时间编辑按钮)
    original_filename = Column(String(255), nullable=False, comment="原始文件名")
    saved_filename = Column(String(255), nullable=False, unique=True, comment="保存的文件名")
    file_size = Column(BigInteger, nullable=False, comment="文件大小（字节）")
    content_type = Column(String(100), comment="文件MIME类型")
    title = Column(String(255), comment="文件标题")
    description = Column(String(500), comment="文件描述")
    file_path = Column(String(500), nullable=False, comment="文件存储路径")
    
    # 基本视频信息
    duration = Column(Integer, comment="视频时长（秒）")
    format_name = Column(String(100), comment="格式名称")
    format_long_name = Column(String(255), comment="格式详细名称")
    bit_rate = Column(BigInteger, comment="总比特率")
    
    # 视频流信息
    width = Column(Integer, comment="视频宽度")
    height = Column(Integer, comment="视频高度")
    video_codec = Column(String(50), comment="视频编码")
    video_codec_long = Column(String(255), comment="视频编码详细名称")
    frame_rate = Column(String(20), comment="帧率")
    avg_frame_rate = Column(String(20), comment="平均帧率")
    aspect_ratio = Column(String(20), comment="宽高比")
    video_ratio = Column(String(20), comment="视频比例")
    pixel_format = Column(String(50), comment="像素格式")
    video_bit_rate = Column(BigInteger, comment="视频比特率")
    nb_frames = Column(BigInteger, comment="总帧数")
    
    # 音频流信息
    audio_codec = Column(String(50), comment="音频编码")
    audio_codec_long = Column(String(255), comment="音频编码详细名称")
    sample_rate = Column(Integer, comment="采样率")
    channels = Column(Integer, comment="声道数")
    channel_layout = Column(String(50), comment="声道布局")
    audio_bit_rate = Column(BigInteger, comment="音频比特率")
    
    # 颜色和质量信息
    color_space = Column(String(50), comment="颜色空间")
    color_range = Column(String(50), comment="颜色范围")
    color_transfer = Column(String(50), comment="颜色传输")
    color_primaries = Column(String(50), comment="颜色原色")
    profile = Column(String(100), comment="编码配置文件")
    level = Column(String(20), comment="编码级别")
    
    # 元数据
    encoder = Column(String(255), comment="编码器信息")
    creation_time = Column(DateTime(timezone=True), comment="视频原始创建时间")
    
    # 系统时间戳
    file_created_at = Column(DateTime(timezone=True), comment="文件原始生成时间")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="上传时间")
<<<<<<< HEAD
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="记录更新时间")
    
    # 关联关系
    user = relationship("User", back_populates="uploaded_files")
    video_analyses = relationship("VideoAnalysis", back_populates="video_file", cascade="all, delete-orphan", lazy="dynamic")
=======
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="记录更新时间")
>>>>>>> ad3f17f (feat: 完善视频上传功能 - 修复时长格式化、上传时间显示、移除时间编辑按钮)
