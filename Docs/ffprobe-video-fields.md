# FFprobe 视频信息字段参考

## 概述

FFprobe 是 FFmpeg 套件中的媒体信息分析工具，可以获取视频文件的详细元数据信息。以下是可以获取的主要字段类型和具体字段。

## 📁 文件格式信息 (format)

### 基本信息
- `filename` - 文件名
- `nb_streams` - 流的数量
- `nb_programs` - 程序数量
- `format_name` - 格式名称 (如: mov,mp4,m4a,3gp,3g2,mj2)
- `format_long_name` - 格式详细名称 (如: QuickTime / MOV)
- `start_time` - 开始时间
- `duration` - 总时长（秒）
- `size` - 文件大小（字节）
- `bit_rate` - 总比特率
- `probe_score` - 探测分数

### 标签信息 (tags)
- `major_brand` - 主要品牌
- `minor_version` - 次要版本
- `compatible_brands` - 兼容品牌
- `encoder` - 编码器信息
- `creation_time` - 创建时间
- `title` - 标题
- `artist` - 艺术家
- `album` - 专辑
- `date` - 日期
- `comment` - 注释

## 🎬 视频流信息 (video streams)

### 编码信息
- `codec_name` - 编码器名称 (如: h264, hevc, vp9)
- `codec_long_name` - 编码器详细名称
- `profile` - 编码配置文件
- `codec_type` - 编解码器类型 (video)
- `codec_tag_string` - 编解码器标签字符串
- `codec_tag` - 编解码器标签

### 视频参数
- `width` - 视频宽度（像素）
- `height` - 视频高度（像素）
- `coded_width` - 编码宽度
- `coded_height` - 编码高度
- `closed_captions` - 是否有隐藏字幕
- `film_grain` - 胶片颗粒
- `has_b_frames` - 是否有B帧
- `sample_aspect_ratio` - 样本宽高比
- `display_aspect_ratio` - 显示宽高比
- `pix_fmt` - 像素格式 (如: yuv420p, yuv444p)
- `level` - 编码级别
- `color_range` - 颜色范围
- `color_space` - 颜色空间
- `color_transfer` - 颜色传输
- `color_primaries` - 颜色原色
- `chroma_location` - 色度位置
- `field_order` - 场序
- `refs` - 参考帧数

### 时间和帧率
- `time_base` - 时间基准
- `start_pts` - 开始PTS
- `start_time` - 开始时间
- `duration_ts` - 时长时间戳
- `duration` - 时长（秒）
- `bit_rate` - 比特率
- `max_bit_rate` - 最大比特率
- `bits_per_raw_sample` - 每个原始样本的位数
- `nb_frames` - 总帧数
- `r_frame_rate` - 实际帧率
- `avg_frame_rate` - 平均帧率
- `time_base` - 时间基准

## 🔊 音频流信息 (audio streams)

### 编码信息
- `codec_name` - 音频编码器 (如: aac, mp3, opus)
- `codec_long_name` - 编码器详细名称
- `profile` - 编码配置文件
- `codec_type` - 编解码器类型 (audio)
- `codec_tag_string` - 编解码器标签字符串
- `codec_tag` - 编解码器标签

### 音频参数
- `sample_fmt` - 采样格式
- `sample_rate` - 采样率 (如: 44100, 48000)
- `channels` - 声道数
- `channel_layout` - 声道布局 (如: stereo, 5.1)
- `bits_per_sample` - 每样本位数
- `initial_padding` - 初始填充

### 时间和比特率
- `time_base` - 时间基准
- `start_pts` - 开始PTS
- `start_time` - 开始时间
- `duration_ts` - 时长时间戳
- `duration` - 时长（秒）
- `bit_rate` - 音频比特率
- `max_bit_rate` - 最大比特率
- `nb_frames` - 音频帧数

## 📖 章节信息 (chapters)

- `id` - 章节ID
- `time_base` - 时间基准
- `start` - 开始时间
- `start_time` - 开始时间（秒）
- `end` - 结束时间
- `end_time` - 结束时间（秒）
- `tags` - 章节标签（标题等）

## 🎯 推荐存储的字段

### 高优先级（用户最关心）
1. **基本信息**
   - `duration` - 视频时长 ⭐⭐⭐
   - `size` - 文件大小 ⭐⭐⭐
   - `format_name` - 文件格式 ⭐⭐⭐
   - `bit_rate` - 总比特率 ⭐⭐

2. **视频质量**
   - `width` - 视频宽度 ⭐⭐⭐
   - `height` - 视频高度 ⭐⭐⭐
   - `video_codec` - 视频编码 ⭐⭐⭐
   - `frame_rate` - 帧率 ⭐⭐
   - `aspect_ratio` - 宽高比 ⭐⭐

3. **音频信息**
   - `audio_codec` - 音频编码 ⭐⭐
   - `sample_rate` - 采样率 ⭐⭐
   - `channels` - 声道数 ⭐⭐

### 中等优先级（技术用户关心）
4. **技术细节**
   - `pixel_format` - 像素格式 ⭐
   - `color_space` - 颜色空间 ⭐
   - `profile` - 编码配置 ⭐
   - `level` - 编码级别 ⭐

5. **元数据**
   - `creation_time` - 创建时间 ⭐
   - `encoder` - 编码器信息 ⭐
   - `title` - 视频标题 ⭐

### 低优先级（专业用户）
6. **高级信息**
   - `nb_frames` - 总帧数
   - `has_b_frames` - B帧信息
   - `refs` - 参考帧数
   - `max_bit_rate` - 最大比特率

## 💡 实现建议

### 数据库字段设计
```sql
-- 推荐添加到 uploaded_files 表的字段
ALTER TABLE uploaded_files ADD COLUMN width INTEGER;
ALTER TABLE uploaded_files ADD COLUMN height INTEGER;
ALTER TABLE uploaded_files ADD COLUMN video_codec VARCHAR(50);
ALTER TABLE uploaded_files ADD COLUMN audio_codec VARCHAR(50);
ALTER TABLE uploaded_files ADD COLUMN frame_rate VARCHAR(20);
ALTER TABLE uploaded_files ADD COLUMN bit_rate BIGINT;
ALTER TABLE uploaded_files ADD COLUMN sample_rate INTEGER;
ALTER TABLE uploaded_files ADD COLUMN channels INTEGER;
ALTER TABLE uploaded_files ADD COLUMN format_name VARCHAR(100);
ALTER TABLE uploaded_files ADD COLUMN aspect_ratio VARCHAR(20);
```

### 前端显示建议
```javascript
// 用户友好的显示格式
const formatVideoInfo = (file) => {
  const resolution = file.width && file.height ? `${file.width}×${file.height}` : '未知';
  const quality = getQualityLabel(file.width, file.height); // HD, FHD, 4K等
  const codec = `${file.video_codec || '未知'}/${file.audio_codec || '未知'}`;
  const frameRate = file.frame_rate ? `${file.frame_rate}fps` : '';
  
  return {
    resolution,
    quality,
    codec,
    frameRate,
    duration: formatDuration(file.duration),
    size: formatFileSize(file.file_size),
    bitrate: formatBitrate(file.bit_rate)
  };
};
```

## 📋 使用说明

1. **安装 FFmpeg**：确保系统已安装 FFmpeg 套件
2. **选择字段**：根据用户需求选择要存储的字段
3. **更新模型**：修改数据库模型添加新字段
4. **更新API**：修改上传接口获取并保存这些信息
5. **更新前端**：在文件列表中显示这些信息

请根据您的需求选择要实现的字段！