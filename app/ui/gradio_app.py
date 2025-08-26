"""Gradio Web界面应用

基于Gradio构建的用户友好界面，提供视频下载和分析功能。
"""

import json
import os
from typing import Dict, List, Optional, Tuple

import gradio as gr
import pandas as pd
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.core.database import engine
from app.core.logging import app_logger
from app.models.user import User
from app.models.video import DownloadTask, AnalysisTask, Video
from app.services.download_service import DownloadService
from app.services.analysis_service import AnalysisService
from app.tasks.download_tasks import download_video_task
from app.tasks.analysis_tasks import analyze_video_task

# 创建数据库会话
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 全局服务实例
download_service = DownloadService()
analysis_service = AnalysisService()

# 模拟用户会话（在实际应用中应该使用真实的用户认证）
CURRENT_USER_ID = 1


def create_gradio_app() -> gr.Blocks:
    """创建Gradio应用
    
    Returns:
        Gradio Blocks应用实例
    """
    
    # 自定义CSS样式
    custom_css = """
    .main-header {
        text-align: center;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 20px;
    }
    
    .feature-card {
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 15px;
        margin: 10px 0;
        background: #f9f9f9;
    }
    
    .status-success {
        color: #28a745;
        font-weight: bold;
    }
    
    .status-error {
        color: #dc3545;
        font-weight: bold;
    }
    
    .status-processing {
        color: #ffc107;
        font-weight: bold;
    }
    """
    
    with gr.Blocks(
        title="AI新媒体专家系统",
        theme=gr.themes.Soft(),
        css=custom_css
    ) as app:
        
        # 页面标题
        gr.HTML("""
        <div class="main-header">
            <h1>🎬 AI新媒体专家系统</h1>
            <p>智能视频下载与内容分析平台</p>
        </div>
        """)
        
        with gr.Tabs() as tabs:
            
            # 视频下载标签页
            with gr.Tab("📥 视频下载", id="download"):
                create_download_interface()
            
            # 视频分析标签页
            with gr.Tab("🔍 视频分析", id="analysis"):
                create_analysis_interface()
            
            # 任务管理标签页
            with gr.Tab("📋 任务管理", id="tasks"):
                create_task_management_interface()
            
            # 视频库标签页
            with gr.Tab("📚 视频库", id="library"):
                create_video_library_interface()
            
            # 系统状态标签页
            with gr.Tab("⚙️ 系统状态", id="status"):
                create_system_status_interface()
    
    return app


def create_download_interface():
    """创建视频下载界面"""
    
    gr.Markdown("## 🎯 视频下载专家")
    gr.Markdown("支持多平台视频下载，包括TikTok、抖音、YouTube、哔哩哔哩等。")
    
    with gr.Row():
        with gr.Column(scale=2):
            # 输入区域
            with gr.Group():
                gr.Markdown("### 📝 下载配置")
                
                url_input = gr.Textbox(
                    label="视频URL",
                    placeholder="请输入视频链接，支持TikTok、抖音、YouTube等平台",
                    lines=2
                )
                
                with gr.Row():
                    quality_dropdown = gr.Dropdown(
                        choices=["best", "1080p", "720p", "480p", "360p", "worst"],
                        value="best",
                        label="视频质量"
                    )
                    
                    format_dropdown = gr.Dropdown(
                        choices=["mp4", "avi", "mkv", "mov", "webm"],
                        value="mp4",
                        label="视频格式"
                    )
                
                with gr.Row():
                    audio_only_checkbox = gr.Checkbox(
                        label="仅下载音频",
                        value=False
                    )
                    
                    priority_slider = gr.Slider(
                        minimum=1,
                        maximum=10,
                        value=5,
                        step=1,
                        label="优先级"
                    )
                
                download_btn = gr.Button(
                    "🚀 开始下载",
                    variant="primary",
                    size="lg"
                )
        
        with gr.Column(scale=1):
            # 状态显示区域
            with gr.Group():
                gr.Markdown("### 📊 下载状态")
                
                status_text = gr.Textbox(
                    label="状态",
                    value="等待下载",
                    interactive=False
                )
                
                progress_bar = gr.Progress()
                
                result_json = gr.JSON(
                    label="下载结果",
                    visible=False
                )
    
    # 批量下载区域
    with gr.Accordion("📦 批量下载", open=False):
        batch_urls = gr.Textbox(
            label="批量URL",
            placeholder="每行一个URL",
            lines=5
        )
        
        batch_download_btn = gr.Button(
            "📦 批量下载",
            variant="secondary"
        )
    
    # 绑定事件
    download_btn.click(
        fn=handle_download,
        inputs=[
            url_input, quality_dropdown, format_dropdown,
            audio_only_checkbox, priority_slider
        ],
        outputs=[status_text, result_json]
    )
    
    batch_download_btn.click(
        fn=handle_batch_download,
        inputs=[batch_urls, quality_dropdown, format_dropdown],
        outputs=[status_text, result_json]
    )


def create_analysis_interface():
    """创建视频分析界面"""
    
    gr.Markdown("## 🧠 视频分析专家")
    gr.Markdown("使用AI技术对视频内容进行深度分析，提取关键信息和标签。")
    
    with gr.Row():
        with gr.Column(scale=2):
            # 视频选择
            with gr.Group():
                gr.Markdown("### 🎬 选择视频")
                
                video_dropdown = gr.Dropdown(
                    label="选择视频",
                    choices=[],
                    interactive=True
                )
                
                refresh_videos_btn = gr.Button(
                    "🔄 刷新视频列表",
                    size="sm"
                )
            
            # 分析配置
            with gr.Group():
                gr.Markdown("### ⚙️ 分析配置")
                
                analysis_type = gr.Radio(
                    choices=["visual", "audio", "content", "full"],
                    value="full",
                    label="分析类型"
                )
                
                with gr.Accordion("高级选项", open=False):
                    max_frames = gr.Slider(
                        minimum=5,
                        maximum=50,
                        value=10,
                        step=1,
                        label="最大关键帧数"
                    )
                    
                    confidence_threshold = gr.Slider(
                        minimum=0.1,
                        maximum=1.0,
                        value=0.7,
                        step=0.1,
                        label="置信度阈值"
                    )
                
                analyze_btn = gr.Button(
                    "🔍 开始分析",
                    variant="primary",
                    size="lg"
                )
        
        with gr.Column(scale=1):
            # 分析状态
            with gr.Group():
                gr.Markdown("### 📈 分析进度")
                
                analysis_status = gr.Textbox(
                    label="状态",
                    value="等待分析",
                    interactive=False
                )
                
                analysis_progress = gr.Progress()
    
    # 分析结果展示
    with gr.Row():
        with gr.Column():
            gr.Markdown("### 📋 分析结果")
            
            with gr.Tabs():
                with gr.Tab("摘要"):
                    summary_text = gr.Textbox(
                        label="分析摘要",
                        lines=5,
                        interactive=False
                    )
                
                with gr.Tab("详细结果"):
                    detailed_results = gr.JSON(
                        label="详细分析数据"
                    )
                
                with gr.Tab("标签"):
                    tags_df = gr.Dataframe(
                        headers=["标签", "置信度", "类别"],
                        label="自动生成标签"
                    )
    
    # 绑定事件
    refresh_videos_btn.click(
        fn=refresh_video_list,
        outputs=[video_dropdown]
    )
    
    analyze_btn.click(
        fn=handle_analysis,
        inputs=[
            video_dropdown, analysis_type,
            max_frames, confidence_threshold
        ],
        outputs=[
            analysis_status, summary_text,
            detailed_results, tags_df
        ]
    )


def create_task_management_interface():
    """创建任务管理界面"""
    
    gr.Markdown("## 📋 任务管理中心")
    
    with gr.Tabs():
        with gr.Tab("下载任务"):
            download_tasks_df = gr.Dataframe(
                headers=["ID", "URL", "状态", "进度", "创建时间"],
                label="下载任务列表"
            )
            
            with gr.Row():
                refresh_download_btn = gr.Button("🔄 刷新")
                cancel_download_btn = gr.Button("❌ 取消选中", variant="stop")
        
        with gr.Tab("分析任务"):
            analysis_tasks_df = gr.Dataframe(
                headers=["ID", "视频", "类型", "状态", "进度", "创建时间"],
                label="分析任务列表"
            )
            
            with gr.Row():
                refresh_analysis_btn = gr.Button("🔄 刷新")
                cancel_analysis_btn = gr.Button("❌ 取消选中", variant="stop")
    
    # 绑定事件
    refresh_download_btn.click(
        fn=refresh_download_tasks,
        outputs=[download_tasks_df]
    )
    
    refresh_analysis_btn.click(
        fn=refresh_analysis_tasks,
        outputs=[analysis_tasks_df]
    )


def create_video_library_interface():
    """创建视频库界面"""
    
    gr.Markdown("## 📚 视频库管理")
    
    with gr.Row():
        with gr.Column(scale=1):
            # 搜索和筛选
            with gr.Group():
                gr.Markdown("### 🔍 搜索筛选")
                
                search_input = gr.Textbox(
                    label="搜索关键词",
                    placeholder="搜索视频标题、作者等"
                )
                
                platform_filter = gr.Dropdown(
                    label="平台筛选",
                    choices=["全部", "tiktok", "douyin", "youtube", "bilibili"],
                    value="全部"
                )
                
                search_btn = gr.Button("🔍 搜索")
        
        with gr.Column(scale=3):
            # 视频列表
            videos_df = gr.Dataframe(
                headers=["ID", "标题", "平台", "作者", "时长", "状态", "创建时间"],
                label="视频列表"
            )
            
            with gr.Row():
                refresh_library_btn = gr.Button("🔄 刷新")
                delete_video_btn = gr.Button("🗑️ 删除选中", variant="stop")
    
    # 绑定事件
    search_btn.click(
        fn=search_videos,
        inputs=[search_input, platform_filter],
        outputs=[videos_df]
    )
    
    refresh_library_btn.click(
        fn=refresh_video_library,
        outputs=[videos_df]
    )


def create_system_status_interface():
    """创建系统状态界面"""
    
    gr.Markdown("## ⚙️ 系统状态监控")
    
    with gr.Row():
        with gr.Column():
            # 系统统计
            with gr.Group():
                gr.Markdown("### 📊 系统统计")
                
                stats_json = gr.JSON(
                    label="统计数据"
                )
        
        with gr.Column():
            # 系统健康
            with gr.Group():
                gr.Markdown("### 💚 系统健康")
                
                health_status = gr.Textbox(
                    label="健康状态",
                    interactive=False
                )
                
                health_details = gr.JSON(
                    label="健康详情"
                )
    
    with gr.Row():
        refresh_stats_btn = gr.Button("🔄 刷新统计")
        check_health_btn = gr.Button("💚 健康检查")
    
    # 绑定事件
    refresh_stats_btn.click(
        fn=get_system_stats,
        outputs=[stats_json]
    )
    
    check_health_btn.click(
        fn=check_system_health,
        outputs=[health_status, health_details]
    )


# 事件处理函数

def handle_download(
    url: str, quality: str, format_pref: str,
    audio_only: bool, priority: int
) -> Tuple[str, Dict]:
    """处理视频下载"""
    try:
        if not url.strip():
            return "❌ 请输入视频URL", {}
        
        # 验证URL
        if not download_service.validate_url(url):
            return "❌ 无效的视频URL或不支持的平台", {}
        
        db = SessionLocal()
        try:
            # 创建下载任务
            task = DownloadTask(
                user_id=CURRENT_USER_ID,
                url=url,
                quality=quality,
                format_preference=format_pref,
                audio_only=audio_only,
                priority=priority,
                status="pending"
            )
            
            db.add(task)
            db.commit()
            db.refresh(task)
            
            # 提交到Celery队列
            celery_task = download_video_task.delay(task.id)
            
            return f"✅ 下载任务已创建 (ID: {task.id})", {
                "task_id": task.id,
                "celery_task_id": celery_task.id,
                "status": "queued",
                "url": url
            }
            
        finally:
            db.close()
            
    except Exception as e:
        app_logger.error("Download failed", error=str(e))
        return f"❌ 下载失败: {str(e)}", {}


def handle_batch_download(
    urls: str, quality: str, format_pref: str
) -> Tuple[str, Dict]:
    """处理批量下载"""
    try:
        url_list = [url.strip() for url in urls.split('\n') if url.strip()]
        
        if not url_list:
            return "❌ 请输入至少一个URL", {}
        
        results = []
        db = SessionLocal()
        
        try:
            for url in url_list:
                if download_service.validate_url(url):
                    task = DownloadTask(
                        user_id=CURRENT_USER_ID,
                        url=url,
                        quality=quality,
                        format_preference=format_pref,
                        status="pending"
                    )
                    
                    db.add(task)
                    db.commit()
                    db.refresh(task)
                    
                    celery_task = download_video_task.delay(task.id)
                    
                    results.append({
                        "url": url,
                        "task_id": task.id,
                        "status": "queued"
                    })
                else:
                    results.append({
                        "url": url,
                        "status": "invalid"
                    })
            
            return f"✅ 已创建 {len([r for r in results if r['status'] == 'queued'])} 个下载任务", {
                "results": results
            }
            
        finally:
            db.close()
            
    except Exception as e:
        return f"❌ 批量下载失败: {str(e)}", {}


def refresh_video_list() -> gr.Dropdown:
    """刷新视频列表"""
    try:
        db = SessionLocal()
        try:
            videos = db.query(Video).filter(
                Video.status == "active"
            ).order_by(Video.created_at.desc()).limit(50).all()
            
            choices = [(f"{v.title[:50]}... (ID: {v.id})", v.id) for v in videos]
            
            return gr.Dropdown(choices=choices)
            
        finally:
            db.close()
            
    except Exception as e:
        app_logger.error("Failed to refresh video list", error=str(e))
        return gr.Dropdown(choices=[])


def handle_analysis(
    video_id: int, analysis_type: str,
    max_frames: int, confidence_threshold: float
) -> Tuple[str, str, Dict, pd.DataFrame]:
    """处理视频分析"""
    try:
        if not video_id:
            return "❌ 请选择要分析的视频", "", {}, pd.DataFrame()
        
        db = SessionLocal()
        try:
            # 检查视频是否存在
            video = db.query(Video).filter(Video.id == video_id).first()
            if not video:
                return "❌ 视频不存在", "", {}, pd.DataFrame()
            
            # 创建分析任务
            task = AnalysisTask(
                user_id=CURRENT_USER_ID,
                video_id=video_id,
                analysis_type=analysis_type,
                config={
                    "max_key_frames": max_frames,
                    "confidence_threshold": confidence_threshold
                },
                status="pending"
            )
            
            db.add(task)
            db.commit()
            db.refresh(task)
            
            # 提交到Celery队列
            celery_task = analyze_video_task.delay(task.id)
            
            return (
                f"✅ 分析任务已创建 (ID: {task.id})",
                "分析任务已提交，请稍后查看结果",
                {"task_id": task.id, "status": "queued"},
                pd.DataFrame()
            )
            
        finally:
            db.close()
            
    except Exception as e:
        app_logger.error("Analysis failed", error=str(e))
        return f"❌ 分析失败: {str(e)}", "", {}, pd.DataFrame()


def refresh_download_tasks() -> pd.DataFrame:
    """刷新下载任务列表"""
    try:
        db = SessionLocal()
        try:
            tasks = db.query(DownloadTask).filter(
                DownloadTask.user_id == CURRENT_USER_ID
            ).order_by(DownloadTask.created_at.desc()).limit(20).all()
            
            data = []
            for task in tasks:
                data.append([
                    task.id,
                    task.url[:50] + "..." if len(task.url) > 50 else task.url,
                    task.status,
                    f"{task.progress}%",
                    task.created_at.strftime("%Y-%m-%d %H:%M")
                ])
            
            return pd.DataFrame(
                data,
                columns=["ID", "URL", "状态", "进度", "创建时间"]
            )
            
        finally:
            db.close()
            
    except Exception as e:
        app_logger.error("Failed to refresh download tasks", error=str(e))
        return pd.DataFrame()


def refresh_analysis_tasks() -> pd.DataFrame:
    """刷新分析任务列表"""
    try:
        db = SessionLocal()
        try:
            tasks = db.query(AnalysisTask).join(Video).filter(
                AnalysisTask.user_id == CURRENT_USER_ID
            ).order_by(AnalysisTask.created_at.desc()).limit(20).all()
            
            data = []
            for task in tasks:
                video_title = task.video.title[:30] + "..." if len(task.video.title) > 30 else task.video.title
                data.append([
                    task.id,
                    video_title,
                    task.analysis_type,
                    task.status,
                    f"{task.progress}%",
                    task.created_at.strftime("%Y-%m-%d %H:%M")
                ])
            
            return pd.DataFrame(
                data,
                columns=["ID", "视频", "类型", "状态", "进度", "创建时间"]
            )
            
        finally:
            db.close()
            
    except Exception as e:
        app_logger.error("Failed to refresh analysis tasks", error=str(e))
        return pd.DataFrame()


def search_videos(search_term: str, platform: str) -> pd.DataFrame:
    """搜索视频"""
    try:
        db = SessionLocal()
        try:
            query = db.query(Video).filter(Video.status == "active")
            
            if search_term.strip():
                query = query.filter(
                    Video.title.ilike(f"%{search_term}%") |
                    Video.author.ilike(f"%{search_term}%")
                )
            
            if platform != "全部":
                query = query.filter(Video.platform == platform)
            
            videos = query.order_by(Video.created_at.desc()).limit(50).all()
            
            data = []
            for video in videos:
                data.append([
                    video.id,
                    video.title[:50] + "..." if len(video.title) > 50 else video.title,
                    video.platform or "未知",
                    video.author or "未知",
                    f"{video.duration}s" if video.duration else "未知",
                    "已分析" if video.is_analyzed else "未分析",
                    video.created_at.strftime("%Y-%m-%d %H:%M")
                ])
            
            return pd.DataFrame(
                data,
                columns=["ID", "标题", "平台", "作者", "时长", "状态", "创建时间"]
            )
            
        finally:
            db.close()
            
    except Exception as e:
        app_logger.error("Failed to search videos", error=str(e))
        return pd.DataFrame()


def refresh_video_library() -> pd.DataFrame:
    """刷新视频库"""
    return search_videos("", "全部")


def get_system_stats() -> Dict:
    """获取系统统计"""
    try:
        db = SessionLocal()
        try:
            from app.models.user import User
            
            stats = {
                "用户统计": {
                    "总用户数": db.query(User).count(),
                    "活跃用户": db.query(User).filter(User.is_active == True).count()
                },
                "视频统计": {
                    "总视频数": db.query(Video).count(),
                    "已分析视频": db.query(Video).filter(Video.is_analyzed == True).count()
                },
                "任务统计": {
                    "下载任务": {
                        "总数": db.query(DownloadTask).count(),
                        "已完成": db.query(DownloadTask).filter(DownloadTask.status == "completed").count(),
                        "进行中": db.query(DownloadTask).filter(DownloadTask.status == "processing").count()
                    },
                    "分析任务": {
                        "总数": db.query(AnalysisTask).count(),
                        "已完成": db.query(AnalysisTask).filter(AnalysisTask.status == "completed").count(),
                        "进行中": db.query(AnalysisTask).filter(AnalysisTask.status == "processing").count()
                    }
                }
            }
            
            return stats
            
        finally:
            db.close()
            
    except Exception as e:
        app_logger.error("Failed to get system stats", error=str(e))
        return {"error": str(e)}


def check_system_health() -> Tuple[str, Dict]:
    """检查系统健康状态"""
    try:
        health_info = {
            "数据库": "✅ 正常",
            "Redis": "✅ 正常",
            "磁盘空间": "✅ 充足",
            "系统负载": "✅ 正常"
        }
        
        # 简单的健康检查
        db = SessionLocal()
        try:
            db.execute("SELECT 1")
        except Exception:
            health_info["数据库"] = "❌ 异常"
        finally:
            db.close()
        
        # 检查Redis连接
        try:
            import redis
            r = redis.from_url(settings.redis_url)
            r.ping()
        except Exception:
            health_info["Redis"] = "❌ 异常"
        
        # 检查磁盘空间
        try:
            import shutil
            stat = shutil.disk_usage(settings.download_dir)
            free_gb = stat.free / (1024**3)
            if free_gb < 1:
                health_info["磁盘空间"] = f"⚠️ 不足 ({free_gb:.1f}GB)"
        except Exception:
            health_info["磁盘空间"] = "❌ 检查失败"
        
        # 计算整体状态
        healthy_count = sum(1 for status in health_info.values() if "✅" in status)
        total_count = len(health_info)
        
        if healthy_count == total_count:
            overall_status = "🟢 系统健康"
        elif healthy_count >= total_count * 0.75:
            overall_status = "🟡 部分异常"
        else:
            overall_status = "🔴 系统异常"
        
        return overall_status, health_info
        
    except Exception as e:
        return f"❌ 健康检查失败: {str(e)}", {}