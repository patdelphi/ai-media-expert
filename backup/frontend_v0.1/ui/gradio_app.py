"""Gradio Web界面

创建AI新媒体专家系统的Web用户界面。
"""

import gradio as gr
import requests
import json
from typing import List, Optional, Tuple

# 响应式CSS样式
responsive_css = """
/* 移动端适配 */
@media (max-width: 768px) {
    .gradio-container {
        padding: 0.5rem !important;
    }
    
    .tab-nav {
        font-size: 0.8rem !important;
    }
    
    .gr-button {
        font-size: 0.7rem !important;
        padding: 0.2rem 0.4rem !important;
    }
    
    .gr-form {
        gap: 0.3rem !important;
    }
}

/* 紧凑布局 */
.gr-block {
    margin: 0.1rem 0 !important;
}

.gr-form {
    gap: 0.2rem !important;
}

/* 统一组件高度 */
.gr-button, .gr-textbox input, .gr-dropdown select, .gr-number input {
    height: 36px !important;
    min-height: 36px !important;
}

/* 紧凑的行间距 */
.gr-row {
    gap: 0.4rem !important;
}

/* 优化分页控制栏 */
.pagination-row {
    align-items: center !important;
    gap: 0.3rem !important;
}

/* 分页按钮适中样式 */
.gr-button[size='sm'] {
    font-size: 0.8rem !important;
    padding: 0.3rem 0.6rem !important;
    height: 32px !important;
    margin: 0 !important;
}

/* 下拉框适中样式 */
.gr-dropdown {
    min-width: 70px !important;
}

/* 数字输入框适中样式 */
.gr-number {
    min-width: 60px !important;
}

/* HTML组件紧凑样式 */
.gr-html {
    margin: 0 !important;
    padding: 0 !important;
}

/* 减少组件间距 */
.gr-group {
    padding: 0.3rem !important;
    margin: 0.2rem 0 !important;
}

/* 强制单行显示 */
.gr-row {
    flex-wrap: nowrap !important;
    overflow-x: auto !important;
}

/* 列组件紧凑 */
.gr-column {
    min-width: auto !important;
    flex-shrink: 0 !important;
}
"""

def create_gradio_app():
    """创建Gradio应用"""
    
    # 添加JavaScript代码处理表格按钮事件
    js_code = """
    <script>
    function viewDetails(videoId) {
        alert('查看视频详情 ID: ' + videoId + '\n功能开发中...');
    }
    
    function viewAnalysis(videoId) {
        alert('查看分析结果 ID: ' + videoId + '\n功能开发中...');
    }
    
    function editVideo(videoId) {
        var newTitle = prompt('请输入新的视频标题:');
        if (newTitle && newTitle.trim()) {
            alert('编辑视频 ID: ' + videoId + '\n新标题: ' + newTitle + '\n功能开发中...');
        }
    }
    
    function deleteVideo(videoId) {
        if (confirm('确定要删除这个视频吗？\n视频ID: ' + videoId)) {
            // 发送删除请求
            fetch('/api/v1/videos/' + videoId, {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json'
                }
            })
            .then(response => {
                if (response.ok) {
                    alert('视频删除成功！');
                    // 刷新页面数据
                    location.reload();
                } else {
                    alert('删除失败，请重试');
                }
            })
            .catch(error => {
                console.error('删除错误:', error);
                alert('删除失败: ' + error.message);
            });
        }
    }
    </script>
    """
    
    with gr.Blocks(
        theme=gr.themes.Soft(),
        css=responsive_css,
        title="AI新媒体专家系统",
        head=js_code
    ) as app:
        
        # 页面标题
        gr.HTML(
            "<h1 style='text-align: center; color: #666; font-size: 0.9rem; padding: 0.2rem; margin: 0.3rem;'>AI新媒体专家系统</h1>"
        )
        
        # 主要功能标签页
        with gr.Tabs():
            with gr.Tab("视频采集"):
                create_download_interface()
            
            with gr.Tab("视频分析"):
                create_analysis_interface()
            
            with gr.Tab("视频库"):
                create_video_library_interface()
            
            with gr.Tab("任务管理"):
                create_task_management_interface()
            
            with gr.Tab("系统设置"):
                create_system_settings_interface()
    
    return app

def create_download_interface():
    """创建视频下载界面"""
    
    with gr.Tabs():
        with gr.Tab("本地上传"):
            create_simple_upload_tab()
        
        with gr.Tab("在线下载"):
            create_online_download_tab()

def create_online_download_tab():
    """创建在线下载标签页"""
    
    with gr.Row():
        with gr.Column(scale=2):
            video_url = gr.Textbox(
                label="视频链接",
                placeholder="输入TikTok、YouTube、抖音、B站等平台的视频链接"
            )
            
            with gr.Row():
                video_quality = gr.Dropdown(
                    label="视频质量",
                    choices=["最高质量", "高质量", "标准质量", "低质量"],
                    value="高质量"
                )
                
                video_format = gr.Dropdown(
                    label="视频格式",
                    choices=["mp4", "avi", "mov", "mkv"],
                    value="mp4"
                )
            
            with gr.Row():
                audio_only = gr.Checkbox(label="仅下载音频")
                priority = gr.Slider(
                    label="优先级",
                    minimum=1,
                    maximum=5,
                    value=3,
                    step=1
                )
            
            download_btn = gr.Button(
                "开始下载",
                variant="primary"
            )
        
        with gr.Column(scale=1):
            download_status = gr.Textbox(
                label="下载状态",
                value="等待下载",
                interactive=False
            )
            
            download_progress = gr.Textbox(
                label="下载进度",
                value="0%",
                interactive=False
            )
    
    # 批量下载
    with gr.Accordion("批量下载", open=False):
        batch_urls = gr.Textbox(
            label="批量链接",
            lines=5,
            placeholder="每行一个视频链接"
        )
        
        batch_download_btn = gr.Button(
            "批量下载",
            variant="secondary"
        )
    
    # 绑定事件
    download_btn.click(
        fn=handle_download,
        inputs=[video_url, video_quality, video_format, audio_only, priority],
        outputs=[download_status, download_progress]
    )
    
    batch_download_btn.click(
        fn=handle_batch_download,
        inputs=[batch_urls, video_quality, video_format],
        outputs=[download_status, download_progress]
    )

def create_simple_upload_tab():
    """创建简化的上传标签页"""
    
    file_upload = gr.File(
        label="选择视频文件",
        file_count="multiple",
        file_types=[".mp4", ".avi", ".mov", ".mkv", ".wmv", ".flv", ".webm"]
    )
    
    # 上传模式选择
    upload_mode = gr.Radio(
        choices=[("统一设置", "unified"), ("单独设置", "individual")],
        value="unified",
        label="设置模式"
    )
    
    # 统一设置区域
    with gr.Group(visible=True) as unified_group:
        gr.Markdown("#### 统一设置")
        with gr.Row():
            default_title = gr.Textbox(
                label="默认标题前缀",
                placeholder="可选，将作为所有文件标题的前缀",
                value=""
            )
            
            auto_analyze = gr.Checkbox(
                label="上传后自动分析",
                value=False
            )
        
        default_description = gr.Textbox(
            label="默认描述",
            placeholder="可选，将应用到所有上传的文件",
            lines=2
        )
    
    # 单独设置区域
    with gr.Group(visible=False) as individual_group:
        gr.Markdown("#### 单独设置")
        file_details = gr.HTML("<p>请先选择文件</p>")
        gr.HTML("<p><strong>注意：</strong>单独设置模式下，每个文件将使用其原始文件名作为标题。如需自定义标题，请使用统一设置模式。</p>")
        individual_auto_analyze = gr.Checkbox(
            label="上传后自动分析",
            value=False
        )
    
    upload_btn = gr.Button(
        "上传视频",
        variant="primary"
    )
    
    upload_status = gr.Textbox(
        label="状态",
        value="等待选择文件",
        interactive=False
    )
    
    # 模式切换事件
    def toggle_mode(mode):
        if mode == "unified":
            return gr.update(visible=True), gr.update(visible=False)
        else:
            return gr.update(visible=False), gr.update(visible=True)
    
    upload_mode.change(
        fn=toggle_mode,
        inputs=[upload_mode],
        outputs=[unified_group, individual_group]
    )
    
    # 文件选择变化事件（单独设置模式）
    def update_individual_inputs(files, mode):
        if mode != "individual" or not files:
            return gr.update(value="<p>请先选择文件</p>")
        
        file_count = len(files)
        details_html = f"<p>已选择 {file_count} 个文件，将使用原始文件名作为标题。</p>"
        
        return gr.update(value=details_html)
    
    file_upload.change(
        fn=update_individual_inputs,
        inputs=[file_upload, upload_mode],
        outputs=[file_details]
    )
    
    # 绑定上传事件
    upload_btn.click(
        fn=handle_flexible_upload,
        inputs=[file_upload, upload_mode, default_title, default_description, auto_analyze, individual_auto_analyze],
        outputs=[upload_status]
    )

def create_analysis_interface():
    """创建视频分析界面"""
    
    create_quick_analysis_tab()

def create_quick_analysis_tab():
    """创建快速分析标签页"""
    
    with gr.Row():
        with gr.Column(scale=2):
            # 最近上传视频下拉选择
            recent_videos_dropdown = gr.Dropdown(
                label="选择最近上传视频",
                choices=get_recent_videos_choices(),
                interactive=True,
                info="显示最近10个上传的视频"
            )
            
            # 分析模版选择与显示（分两列）
            with gr.Row():
                with gr.Column(scale=1):
                    analysis_template = gr.Dropdown(
                        label="分析模版",
                        choices=get_analysis_templates(),
                        interactive=True
                    )
                
                with gr.Column(scale=2):
                    # 模版内容编辑器（纯文本，带滚动条）
                    template_content = gr.Textbox(
                        label="模版内容（可编辑）",
                        lines=8,
                        interactive=True,
                        value="请选择分析模版",
                        max_lines=20
                    )
            
            # 标签规则选择
            tag_rule = gr.Dropdown(
                label="标签规则",
                choices=[
                    ("仅指定标签集", "specified_only"),
                    ("指定标签集+开放生成", "specified_plus_open"),
                    ("开放生成标签", "open_generation")
                ],
                value="specified_only",
                interactive=True
            )
            
            # 指定标签集选择与标签显示（分两列）
            with gr.Row():
                with gr.Column(scale=1):
                    tag_set_selector = gr.Dropdown(
                        label="指定标签集",
                        choices=get_tag_sets(),
                        interactive=True,
                        visible=True
                    )
                
                with gr.Column(scale=2):
                    # 标签显示区域
                    tag_display = gr.Textbox(
                        label="标签集内容",
                        lines=4,
                        interactive=False,
                        placeholder="选择标签集后显示其中的标签"
                    )
            
            # AI配置选择
            ai_config_selector = gr.Dropdown(
                label="AI配置",
                choices=get_ai_configs(),
                interactive=True
            )
            
            # 生成的提示词编辑器（纯文本，带滚动条）
            generated_prompt = gr.Textbox(
                label="生成的提示词（可编辑）",
                lines=10,
                interactive=True,
                value="选择模版和标签规则后自动生成提示词",
                max_lines=25
            )
            
            # 开始分析按钮
            start_analysis_btn = gr.Button(
                "开始分析",
                variant="primary",
                size="lg"
            )
        
        with gr.Column(scale=1):
            # 分析状态
            analysis_status = gr.Textbox(
                label="分析状态",
                value="等待开始",
                interactive=False
            )
            
            analysis_progress = gr.Textbox(
                label="分析进度",
                value="0%",
                interactive=False
            )
            
            # AI接口信息显示
            ai_response_info = gr.Textbox(
                label="AI接口信息",
                value="暂无信息",
                interactive=False,
                lines=3
            )
    
    # 分析结果显示
    with gr.Row():
        with gr.Column():
            # AI分析结果（Markdown渲染）
            analysis_results_md = gr.Markdown(
                label="AI分析结果",
                value="等待分析结果..."
            )
            
            # 原始JSON结果（可折叠）
            with gr.Accordion("原始分析数据", open=False):
                analysis_results_json = gr.JSON(
                    label="JSON格式结果",
                    value={}
                )
    
    # 事件绑定
    def on_template_change(template_key):
        """模版选择变化时更新内容"""
        if template_key:
            content = get_template_content(template_key)
            return content
        return "请选择一个分析模版"
    
    def on_tag_rule_change(tag_rule):
        """标签规则变化时控制标签集选择器可见性"""
        if tag_rule in ["specified_only", "specified_plus_open"]:
            return gr.Dropdown.update(visible=True)
        else:
            return gr.Dropdown.update(visible=False)
    
    def generate_prompt(template_content, tag_rule, tag_set_key):
        """生成分析提示词"""
        if not template_content:
            return "请先选择分析模版"
        
        prompt = f"## 分析任务\n{template_content}\n\n"
        
        # 添加标签规则
        if tag_rule == "specified_only":
            if tag_set_key:
                tags = get_tag_set_content(tag_set_key)
                prompt += f"## 标签要求\n请从以下标签中选择合适的标签：{', '.join(tags)}\n\n"
            else:
                prompt += "## 标签要求\n请先选择标签集\n\n"
        elif tag_rule == "specified_plus_open":
            if tag_set_key:
                tags = get_tag_set_content(tag_set_key)
                prompt += f"## 标签要求\n优先使用以下标签：{', '.join(tags)}\n如果不够用，可以生成其他相关标签\n\n"
            else:
                prompt += "## 标签要求\n请先选择标签集\n\n"
        else:  # open_generation
            prompt += "## 标签要求\n请根据视频内容自由生成相关标签\n\n"
        
        prompt += "## 输出格式\n请以Markdown格式输出分析结果，包含清晰的标题和结构化内容。"
        
        return prompt
    
    def start_video_analysis(video_id, template_content, generated_prompt, ai_config_key):
        """开始视频分析"""
        if not video_id:
            return "请输入视频ID", "0%", "参数错误", "等待分析结果...", {}
        
        if not template_content or not generated_prompt:
            return "请选择分析模版并生成提示词", "0%", "参数错误", "等待分析结果...", {}
        
        if not ai_config_key:
            return "请选择AI配置", "0%", "参数错误", "等待分析结果...", {}
        
        try:
            # 模拟AI分析过程
            import time
            import json
            
            # 更新状态
            yield "正在连接AI服务...", "10%", f"使用配置: {ai_config_key}", "等待分析结果...", {}
            time.sleep(1)
            
            yield "正在提取视频帧...", "30%", "提取关键帧用于分析", "等待分析结果...", {}
            time.sleep(1)
            
            yield "正在调用AI接口...", "50%", "发送分析请求", "等待分析结果...", {}
            time.sleep(2)
            
            yield "正在处理AI响应...", "80%", "解析分析结果", "等待分析结果...", {}
            time.sleep(1)
            
            # 模拟分析结果
            mock_result = {
                "video_id": int(video_id),
                "analysis_type": "AI视频分析",
                "ai_config": ai_config_key,
                "prompt_used": generated_prompt,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "status": "completed"
            }
            
            # 模拟Markdown格式的分析结果
            markdown_result = f"""# 视频分析报告

## 基本信息
- **视频ID**: {video_id}
- **分析时间**: {time.strftime("%Y-%m-%d %H:%M:%S")}
- **AI配置**: {ai_config_key}

## 分析结果

### 主要内容
这是一个示例分析结果。在实际实现中，这里会显示AI对视频的详细分析。

### 关键标签
- 示例标签1
- 示例标签2
- 示例标签3

### 质量评估
- **整体质量**: 良好
- **内容价值**: 中等
- **技术水平**: 标准

### 建议
1. 可以改进音频质量
2. 增加更多互动元素
3. 优化内容结构

---
*注意：这是演示结果，实际使用时会调用真实的AI接口进行分析。*
"""
            
            yield "分析完成", "100%", "分析成功完成", markdown_result, mock_result
             
        except Exception as e:
            error_msg = f"分析失败: {str(e)}"
            yield "分析失败", "0%", error_msg, f"## 错误\n{error_msg}", {"error": str(e)}
    
    # 绑定事件
    analysis_template.change(
        fn=on_template_change,
        inputs=[analysis_template],
        outputs=[template_content]
    )
    
    tag_rule.change(
        fn=on_tag_rule_change,
        inputs=[tag_rule],
        outputs=[tag_set_selector]
    )
    
    # 标签集选择变化时显示标签内容
    def on_tag_set_change(tag_set_key):
        """标签集选择变化时显示标签内容"""
        if tag_set_key:
            tags = get_tag_set_content(tag_set_key)
            return ", ".join(tags) if tags else "该标签集暂无内容"
        return "请选择标签集"
    
    tag_set_selector.change(
        fn=on_tag_set_change,
        inputs=[tag_set_selector],
        outputs=[tag_display]
    )
    
    # 自动生成提示词
    def auto_generate_prompt(template_content, tag_rule, tag_set_key):
        return generate_prompt(template_content, tag_rule, tag_set_key)
    
    for component in [template_content, tag_rule, tag_set_selector]:
        component.change(
            fn=auto_generate_prompt,
            inputs=[template_content, tag_rule, tag_set_selector],
            outputs=[generated_prompt]
        )
    
    start_analysis_btn.click(
        fn=start_video_analysis,
        inputs=[recent_videos_dropdown, template_content, generated_prompt, ai_config_selector],
        outputs=[analysis_status, analysis_progress, ai_response_info, analysis_results_md, analysis_results_json]
    )

def create_video_library_interface():
    """创建视频库界面"""
    
    create_video_browser_tab()

def create_video_browser_tab():
    """创建视频浏览标签页"""
    
    # 搜索和筛选栏
    with gr.Row():
        search_input = gr.Textbox(
            placeholder="搜索视频标题、作者...",
            scale=3,
            show_label=False,
            container=False
        )
        
        platform_filter = gr.Dropdown(
            choices=["全部", "本地", "TikTok", "YouTube", "抖音", "B站"],
            value="全部",
            scale=1,
            show_label=False,
            container=False
        )
        
        search_btn = gr.Button("搜索", scale=0)
    
    # 视频列表
    videos_df = gr.Dataframe(
        headers=["选择", "ID", "源文件名", "标题", "大小", "标签", "状态", "日期"],
        value=load_videos_data_enhanced(0, 20),  # 使用增强的数据加载函数
        interactive=False,  # 禁用编辑功能，只显示数据
        wrap=True  # 允许内容换行
    )
    
    # 操作区域
    with gr.Row():
        with gr.Column(scale=2):
            selected_video_id = gr.Number(
                label="选中视频ID",
                placeholder="请输入要操作的视频ID",
                precision=0
            )
        
        with gr.Column(scale=3):
            with gr.Row():
                view_detail_btn = gr.Button("查看详情", size="sm", scale=1)
                view_analysis_btn = gr.Button("查看分析", size="sm", scale=1)
                edit_video_btn = gr.Button("编辑视频", size="sm", scale=1)
                delete_video_btn = gr.Button("删除视频", variant="stop", size="sm", scale=1)
    
    # 操作状态显示
    operation_status = gr.Textbox(
        label="操作状态",
        value="请选择视频ID并点击操作按钮",
        interactive=False
    )
     
    # 超紧凑的分页控制和操作按钮
    with gr.Row(elem_classes=["pagination-row"]):
        # 每页数量下拉框
        page_size_dropdown = gr.Dropdown(
            choices=["10", "20", "50"],
            value="20",
            label="每页",
            scale=0,
            min_width=70,
            container=False
        )
        
        # 分页导航按钮组
        first_page_btn = gr.Button("首页", size="sm", scale=0, min_width=45)
        prev_page_btn = gr.Button("上页", size="sm", scale=0, min_width=45)
        
        # 页码输入框
        current_page = gr.Number(
            value=1, 
            show_label=False, 
            scale=0, 
            minimum=1,
            container=False,
            min_width=50
        )
        
        # 总页数显示
        with gr.Column(scale=0, min_width=35):
            total_pages_text = gr.HTML(
                "<div style='display: flex; align-items: center; height: 32px; padding: 0 6px; font-size: 0.8rem; color: #666; white-space: nowrap;'>/ 1</div>"
            )
        
        next_page_btn = gr.Button("下页", size="sm", scale=0, min_width=45)
        last_page_btn = gr.Button("末页", size="sm", scale=0, min_width=45)
        
        # 操作按钮组
        refresh_btn = gr.Button("刷新", size="sm", scale=0, min_width=45)
        analyze_btn = gr.Button("分析", variant="primary", size="sm", scale=0, min_width=45)
        export_btn = gr.Button("导出", variant="secondary", size="sm", scale=0, min_width=45)
        delete_btn = gr.Button("删除", variant="stop", size="sm", scale=0, min_width=45)
        
        # 页面信息（右对齐）
        with gr.Column(scale=1, min_width=120):
            page_info = gr.HTML(
                value=update_page_info(1, 20, get_total_videos_count())
            )
    
    # 绑定事件
    def search_and_update_info(search_term: str, platform: str):
        """搜索并更新分页信息"""
        data = load_videos_data_enhanced(0, 20, search_term, platform)
        total = get_total_videos_count()
        info = update_page_info(1, len(data), total)
        return data, info
    
    def refresh_and_update_info():
        """刷新并更新分页信息"""
        data = load_videos_data_enhanced(0, 20)
        total = get_total_videos_count()
        info = update_page_info(1, len(data), total)
        return data, info
    
    def handle_view_detail(video_id):
        """查看视频详情"""
        if not video_id:
            return "请先输入视频ID"
        return f"查看视频详情功能开发中... 视频ID: {int(video_id)}"
    
    def handle_view_analysis(video_id):
        """查看分析结果"""
        if not video_id:
            return "请先输入视频ID"
        return f"查看分析结果功能开发中... 视频ID: {int(video_id)}"
    
    def handle_edit_video(video_id):
        """编辑视频"""
        if not video_id:
            return "请先输入视频ID"
        return f"编辑视频功能开发中... 视频ID: {int(video_id)}"
    
    def handle_delete_video_new(video_id):
        """删除视频"""
        if not video_id:
            return "请先输入视频ID"
        
        try:
            from app.core.database import SessionLocal
            from app.models.video import Video
            db = SessionLocal()
            
            video = db.query(Video).filter(Video.id == int(video_id)).first()
            if not video:
                db.close()
                return f"视频ID {int(video_id)} 不存在"
            
            # 逻辑删除
            video.status = "deleted"
            db.commit()
            db.close()
            
            return f"视频 '{video.title}' 已删除成功"
            
        except Exception as e:
            return f"删除失败: {str(e)}"
    
    search_btn.click(
        fn=search_and_update_info,
        inputs=[search_input, platform_filter],
        outputs=[videos_df, page_info]
    )
    
    # 刷新按钮事件
    refresh_btn.click(
        fn=refresh_and_update_info,
        outputs=[videos_df, page_info]
    )
    
    # 新操作按钮事件
    view_detail_btn.click(
        fn=handle_view_detail,
        inputs=[selected_video_id],
        outputs=[operation_status]
    )
    
    view_analysis_btn.click(
        fn=handle_view_analysis,
        inputs=[selected_video_id],
        outputs=[operation_status]
    )
    
    edit_video_btn.click(
        fn=handle_edit_video,
        inputs=[selected_video_id],
        outputs=[operation_status]
    )
    
    delete_video_btn.click(
        fn=handle_delete_video_new,
        inputs=[selected_video_id],
        outputs=[operation_status]
    )
    
    # 旧删除按钮事件（保留兼容性）
    delete_btn.click(
        fn=lambda: "请使用上方的删除视频按钮",
        outputs=[operation_status]
    )
    
    # 页面大小变化事件
    page_size_dropdown.change(
        fn=lambda size: load_videos_data_enhanced(0, int(size)),
        inputs=[page_size_dropdown],
        outputs=[videos_df]
    )

def create_task_management_interface():
    """创建任务管理界面"""
    
    with gr.Tabs():
        with gr.Tab("下载任务"):
            download_tasks_df = gr.Dataframe(
                headers=["任务", "状态", "进度", "时间"],
                value=[
                    ["TikTok视频下载", "完成", "100%", "14:30"],
                    ["YouTube视频下载", "进行中", "65%", "14:25"],
                    ["抖音视频下载", "等待中", "0%", "14:20"]
                ]
            )
            
            with gr.Row():
                gr.Button("刷新", size="sm")
                gr.Button("取消", variant="stop", size="sm")
        
        with gr.Tab("分析任务"):
            analysis_tasks_df = gr.Dataframe(
                headers=["视频", "类型", "状态", "时间"],
                value=[
                    ["AI讲解视频", "全面分析", "完成", "14:35"],
                    ["产品展示", "内容分析", "进行中", "14:28"],
                    ["教学视频", "视觉分析", "等待中", "14:15"]
                ]
            )
            
            with gr.Row():
                gr.Button("刷新", size="sm")
                gr.Button("取消", variant="stop", size="sm")

def create_system_settings_interface():
    """创建系统设置界面"""
    
    with gr.Tabs():
        with gr.Tab("基础设置"):
            create_basic_settings_tab()
        
        with gr.Tab("下载设置"):
            create_download_settings_tab()
        
        with gr.Tab("分析设置"):
            create_analysis_settings_tab()
        
        with gr.Tab("系统监控"):
            create_system_monitor_tab()

def create_basic_settings_tab():
    """创建基础设置标签页"""
    pass

def create_download_settings_tab():
    """创建下载设置标签页"""
    pass

def create_analysis_settings_tab():
    """创建分析设置标签页"""
    
    with gr.Tabs():
        with gr.Tab("AI配置管理"):
            create_ai_config_management()
        
        with gr.Tab("提示词模版管理"):
            create_template_management()
        
        with gr.Tab("标签管理"):
            create_tag_management()

def create_ai_config_management():
    """创建AI配置管理界面"""
    # AI配置管理
    with gr.Row():
        with gr.Column():
            gr.Markdown("#### AI配置管理")
            
            # 配置列表
            ai_configs_df = gr.Dataframe(
                headers=["ID", "名称", "提供商", "模型", "状态"],
                value=[],
                interactive=True
            )
            
            with gr.Row():
                refresh_configs_btn = gr.Button("刷新配置", size="sm")
                test_config_btn = gr.Button("测试选中", size="sm")
                delete_config_btn = gr.Button("删除选中", variant="stop", size="sm")
        
        with gr.Column():
            gr.Markdown("#### 添加新配置")
            
            config_name = gr.Textbox(
                label="配置名称",
                placeholder="例如：GPT-4配置"
            )
            
            config_provider = gr.Dropdown(
                label="AI提供商",
                choices=["openai", "claude", "gemini", "qwen", "baidu"],
                value="openai"
            )
            
            config_model = gr.Textbox(
                label="模型名称",
                placeholder="例如：gpt-4-turbo"
            )
            
            config_api_key = gr.Textbox(
                label="API密钥",
                placeholder="输入API密钥",
                type="password"
            )
            
            config_api_base = gr.Textbox(
                label="API基础URL（可选）",
                placeholder="例如：https://api.openai.com/v1"
            )
            
            with gr.Row():
                config_max_tokens = gr.Number(
                    label="最大Token数",
                    value=4000,
                    minimum=100,
                    maximum=32000
                )
                
                config_temperature = gr.Slider(
                    label="温度参数",
                    minimum=0.0,
                    maximum=2.0,
                    value=0.7,
                    step=0.1
                )
            
            config_is_active = gr.Checkbox(
                label="启用此配置",
                value=True
            )
            
            add_config_btn = gr.Button(
                "添加配置",
                variant="primary"
            )
            
            config_status = gr.Textbox(
                label="操作状态",
                interactive=False
            )

def create_template_management():
    """创建提示词模版管理界面"""
    
    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("#### 模版列表")
            
            # 模版列表
            templates_df = gr.Dataframe(
                headers=["ID", "模版名称", "类型", "创建时间", "状态"],
                value=load_templates_data(),
                interactive=False
            )
            
            with gr.Row():
                refresh_templates_btn = gr.Button("刷新列表", size="sm")
                edit_template_btn = gr.Button("编辑选中", size="sm")
                delete_template_btn = gr.Button("删除选中", variant="stop", size="sm")
        
        with gr.Column(scale=2):
            gr.Markdown("#### 模版编辑")
            
            template_id = gr.Number(
                label="模版ID（编辑时自动填充）",
                value=0,
                visible=False
            )
            
            template_name = gr.Textbox(
                label="模版名称",
                placeholder="例如：内容分析模版"
            )
            
            template_type = gr.Dropdown(
                label="模版类型",
                choices=[
                    ("内容分析", "content_analysis"),
                    ("视觉质量评估", "visual_quality"),
                    ("营销效果分析", "marketing_analysis"),
                    ("教育内容评估", "educational_assessment"),
                    ("娱乐价值分析", "entertainment_analysis"),
                    ("技术内容审查", "technical_review"),
                    ("自定义模版", "custom")
                ],
                value="content_analysis"
            )
            
            template_description = gr.Textbox(
                label="模版描述",
                lines=2,
                placeholder="简要描述此模版的用途和特点"
            )
            
            template_content = gr.Textbox(
                label="模版内容",
                lines=12,
                max_lines=25,
                placeholder="请输入提示词模版内容...",
                info="支持使用变量：{video_title}, {video_duration}, {analysis_type} 等"
            )
            
            template_tags = gr.Textbox(
                label="关联标签（可选）",
                placeholder="用逗号分隔多个标签，例如：教育,技术,评测"
            )
            
            template_is_active = gr.Checkbox(
                label="启用此模版",
                value=True
            )
            
            with gr.Row():
                save_template_btn = gr.Button(
                    "保存模版",
                    variant="primary",
                    scale=1
                )
                
                clear_template_btn = gr.Button(
                    "清空表单",
                    scale=1
                )
            
            template_status = gr.Textbox(
                label="操作状态",
                interactive=False
            )
    
    # 提示词模版管理事件绑定
    def refresh_templates():
        """刷新模版列表"""
        return load_templates_data()
    
    def save_template(template_id, name, template_type, description, content, tags, is_active):
        """保存模版"""
        if not name or not content:
            return "请填写模版名称和内容", load_templates_data()
        
        try:
            # 模拟保存逻辑
            if template_id and template_id > 0:
                # 更新现有模版
                status_msg = f"模版 '{name}' 更新成功"
            else:
                # 创建新模版
                status_msg = f"模版 '{name}' 创建成功"
            
            return status_msg, load_templates_data()
        except Exception as e:
            return f"保存失败: {str(e)}", load_templates_data()
    
    def edit_template(evt: gr.SelectData):
        """编辑选中的模版"""
        if evt.index is None:
            return "请选择要编辑的模版", 0, "", "content_analysis", "", "", "", True
        
        try:
            # 获取选中行的数据
            templates = load_templates_data()
            if evt.index[0] < len(templates):
                template_data = templates[evt.index[0]]
                template_id = int(template_data[0])
                
                # 根据ID获取完整模版信息（模拟）
                template_info = get_template_by_id(template_id)
                
                return (
                    f"正在编辑模版: {template_info['name']}",
                    template_info['id'],
                    template_info['name'],
                    template_info['type'],
                    template_info['description'],
                    template_info['content'],
                    template_info['tags'],
                    template_info['is_active']
                )
            else:
                return "选择的模版不存在", 0, "", "content_analysis", "", "", "", True
        except Exception as e:
            return f"编辑失败: {str(e)}", 0, "", "content_analysis", "", "", "", True
    
    def delete_template(evt: gr.SelectData):
        """删除选中的模版"""
        if evt.index is None:
            return "请选择要删除的模版", load_templates_data()
        
        try:
            templates = load_templates_data()
            if evt.index[0] < len(templates):
                template_data = templates[evt.index[0]]
                template_name = template_data[1]
                
                # 模拟删除逻辑
                return f"模版 '{template_name}' 删除成功", load_templates_data()
            else:
                return "选择的模版不存在", load_templates_data()
        except Exception as e:
            return f"删除失败: {str(e)}", load_templates_data()
    
    def clear_template_form():
        """清空模版表单"""
        return "表单已清空", 0, "", "content_analysis", "", "", "", True
    
    # 绑定模版管理事件
    refresh_templates_btn.click(
        fn=refresh_templates,
        outputs=[templates_df]
    )
    
    save_template_btn.click(
        fn=save_template,
        inputs=[
            template_id, template_name, template_type, template_description,
            template_content, template_tags, template_is_active
        ],
        outputs=[template_status, templates_df]
    )
    
    templates_df.select(
        fn=edit_template,
        outputs=[
            template_status, template_id, template_name, template_type,
            template_description, template_content, template_tags, template_is_active
        ]
    )
    
    delete_template_btn.click(
        fn=delete_template,
        inputs=[templates_df],
        outputs=[template_status, templates_df]
    )
    
    clear_template_btn.click(
        fn=clear_template_form,
        outputs=[
            template_status, template_id, template_name, template_type,
            template_description, template_content, template_tags, template_is_active
        ]
    )

def create_tag_management():
    """创建标签管理界面"""
    
    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("#### 标签组管理")
            
            # 标签组列表
            tag_groups_df = gr.Dataframe(
                headers=["ID", "标签组名称", "标签数量", "创建时间"],
                value=load_tag_groups_data(),
                interactive=False
            )
            
            with gr.Row():
                refresh_groups_btn = gr.Button("刷新组列表", size="sm")
                edit_group_btn = gr.Button("编辑选中组", size="sm")
                delete_group_btn = gr.Button("删除选中组", variant="stop", size="sm")
            
            # 标签组编辑
            gr.Markdown("#### 标签组编辑")
            
            group_id = gr.Number(
                label="标签组ID",
                value=0,
                visible=False
            )
            
            group_name = gr.Textbox(
                label="标签组名称",
                placeholder="例如：技术类标签"
            )
            
            group_description = gr.Textbox(
                label="标签组描述",
                lines=2,
                placeholder="描述此标签组的用途"
            )
            
            with gr.Row():
                save_group_btn = gr.Button(
                    "保存标签组",
                    variant="primary",
                    scale=1
                )
                
                clear_group_btn = gr.Button(
                    "清空表单",
                    scale=1
                )
        
        with gr.Column(scale=2):
            gr.Markdown("#### 标签管理")
            
            # 选择标签组
            selected_tag_group = gr.Dropdown(
                label="选择标签组",
                choices=get_tag_groups_choices(),
                interactive=True
            )
            
            # 标签列表
            tags_df = gr.Dataframe(
                headers=["ID", "标签名称", "使用次数", "创建时间"],
                value=[],
                interactive=False
            )
            
            with gr.Row():
                refresh_tags_btn = gr.Button("刷新标签", size="sm")
                edit_tag_btn = gr.Button("编辑选中", size="sm")
                delete_tag_btn = gr.Button("删除选中", variant="stop", size="sm")
            
            # 标签编辑
            gr.Markdown("#### 标签编辑")
            
            tag_id = gr.Number(
                label="标签ID",
                value=0,
                visible=False
            )
            
            tag_name = gr.Textbox(
                label="标签名称",
                placeholder="例如：编程"
            )
            
            tag_description = gr.Textbox(
                label="标签描述（可选）",
                lines=2,
                placeholder="描述此标签的含义和用途"
            )
            
            tag_color = gr.Dropdown(
                label="标签颜色",
                choices=[
                    ("蓝色", "blue"),
                    ("绿色", "green"),
                    ("红色", "red"),
                    ("黄色", "yellow"),
                    ("紫色", "purple"),
                    ("橙色", "orange"),
                    ("灰色", "gray")
                ],
                value="blue"
            )
            
            with gr.Row():
                save_tag_btn = gr.Button(
                    "保存标签",
                    variant="primary",
                    scale=1
                )
                
                clear_tag_btn = gr.Button(
                    "清空表单",
                    scale=1
                )
            
            tag_status = gr.Textbox(
                label="操作状态",
                value="等待操作",
                interactive=False
            )
    
    # 标签管理完整事件绑定
    def refresh_tag_groups():
        """刷新标签组列表"""
        return load_tag_groups_data()
    
    def refresh_tags_by_group(group_key):
        """根据标签组刷新标签列表"""
        if group_key:
            return load_tags_by_group(group_key)
        return []
    
    def save_tag_group(group_id, name, description):
        """保存标签组"""
        if not name:
            return "请填写标签组名称", load_tag_groups_data()
        
        try:
            if group_id and group_id > 0:
                status_msg = f"标签组 '{name}' 更新成功"
            else:
                status_msg = f"标签组 '{name}' 创建成功"
            
            return status_msg, load_tag_groups_data()
        except Exception as e:
            return f"保存失败: {str(e)}", load_tag_groups_data()
    
    def edit_tag_group(evt: gr.SelectData):
        """编辑选中的标签组"""
        if evt.index is None:
            return "请选择要编辑的标签组", 0, "", ""
        
        try:
            tag_groups = load_tag_groups_data()
            if evt.index[0] < len(tag_groups):
                group_data = tag_groups[evt.index[0]]
                group_id = int(group_data[0])
                group_name = group_data[1]
                
                # 获取标签组详细信息（模拟）
                group_info = get_tag_group_by_id(group_id)
                
                return (
                    f"正在编辑标签组: {group_name}",
                    group_info['id'],
                    group_info['name'],
                    group_info['description']
                )
            else:
                return "选择的标签组不存在", 0, "", ""
        except Exception as e:
            return f"编辑失败: {str(e)}", 0, "", ""
    
    def delete_tag_group(evt: gr.SelectData):
        """删除选中的标签组"""
        if evt.index is None:
            return "请选择要删除的标签组", load_tag_groups_data()
        
        try:
            tag_groups = load_tag_groups_data()
            if evt.index[0] < len(tag_groups):
                group_data = tag_groups[evt.index[0]]
                group_name = group_data[1]
                
                return f"标签组 '{group_name}' 删除成功", load_tag_groups_data()
            else:
                return "选择的标签组不存在", load_tag_groups_data()
        except Exception as e:
            return f"删除失败: {str(e)}", load_tag_groups_data()
    
    def clear_group_form():
        """清空标签组表单"""
        return "表单已清空", 0, "", ""
    
    def save_tag(tag_id, name, description, color, group_key):
        """保存标签"""
        if not name:
            return "请填写标签名称", refresh_tags_by_group(group_key)
        
        if not group_key:
            return "请先选择标签组", refresh_tags_by_group(group_key)
        
        try:
            if tag_id and tag_id > 0:
                status_msg = f"标签 '{name}' 更新成功"
            else:
                status_msg = f"标签 '{name}' 创建成功"
            
            return status_msg, refresh_tags_by_group(group_key)
        except Exception as e:
            return f"保存失败: {str(e)}", refresh_tags_by_group(group_key)
    
    def edit_tag(evt: gr.SelectData, group_key):
        """编辑选中的标签"""
        if evt.index is None:
            return "请选择要编辑的标签", 0, "", "", "blue"
        
        try:
            tags = load_tags_by_group(group_key) if group_key else []
            if evt.index[0] < len(tags):
                tag_data = tags[evt.index[0]]
                tag_id = int(tag_data[0])
                tag_name = tag_data[1]
                
                # 获取标签详细信息（模拟）
                tag_info = get_tag_by_id(tag_id)
                
                return (
                    f"正在编辑标签: {tag_name}",
                    tag_info['id'],
                    tag_info['name'],
                    tag_info['description'],
                    tag_info['color']
                )
            else:
                return "选择的标签不存在", 0, "", "", "blue"
        except Exception as e:
            return f"编辑失败: {str(e)}", 0, "", "", "blue"
    
    def delete_tag(evt: gr.SelectData, group_key):
        """删除选中的标签"""
        if evt.index is None:
            return "请选择要删除的标签", refresh_tags_by_group(group_key)
        
        try:
            tags = load_tags_by_group(group_key) if group_key else []
            if evt.index[0] < len(tags):
                tag_data = tags[evt.index[0]]
                tag_name = tag_data[1]
                
                return f"标签 '{tag_name}' 删除成功", refresh_tags_by_group(group_key)
            else:
                return "选择的标签不存在", refresh_tags_by_group(group_key)
        except Exception as e:
            return f"删除失败: {str(e)}", refresh_tags_by_group(group_key)
    
    def clear_tag_form():
        """清空标签表单"""
        return "表单已清空", 0, "", "", "blue"
    
    # 绑定标签组相关事件
    refresh_groups_btn.click(
        fn=refresh_tag_groups,
        outputs=[tag_groups_df]
    )
    
    save_group_btn.click(
        fn=save_tag_group,
        inputs=[group_id, group_name, group_description],
        outputs=[tag_status, tag_groups_df]
    )
    
    tag_groups_df.select(
        fn=edit_tag_group,
        outputs=[tag_status, group_id, group_name, group_description]
    )
    
    delete_group_btn.click(
        fn=delete_tag_group,
        inputs=[tag_groups_df],
        outputs=[tag_status, tag_groups_df]
    )
    
    clear_group_btn.click(
        fn=clear_group_form,
        outputs=[tag_status, group_id, group_name, group_description]
    )
    
    # 绑定标签相关事件
    selected_tag_group.change(
        fn=refresh_tags_by_group,
        inputs=[selected_tag_group],
        outputs=[tags_df]
    )
    
    refresh_tags_btn.click(
        fn=refresh_tags_by_group,
        inputs=[selected_tag_group],
        outputs=[tags_df]
    )
    
    save_tag_btn.click(
        fn=save_tag,
        inputs=[tag_id, tag_name, tag_description, tag_color, selected_tag_group],
        outputs=[tag_status, tags_df]
    )
    
    tags_df.select(
        fn=lambda evt: edit_tag(evt, selected_tag_group.value),
        outputs=[tag_status, tag_id, tag_name, tag_description, tag_color]
    )
    
    delete_tag_btn.click(
        fn=lambda evt: delete_tag(evt, selected_tag_group.value),
        inputs=[tags_df],
        outputs=[tag_status, tags_df]
    )
    
    clear_tag_btn.click(
        fn=clear_tag_form,
        outputs=[tag_status, tag_id, tag_name, tag_description, tag_color]
    )

def create_system_monitor_tab():
    """创建系统监控标签页"""
    pass

# 事件处理函数
def handle_flexible_upload(
    files: List[str],
    mode: str,
    title_prefix: str,
    description: str,
    auto_analyze: bool,
    individual_auto_analyze: bool
) -> str:
    """处理灵活的视频上传（统一设置或单独设置）"""
    if not files:
        return "请选择要上传的视频文件"
    
    try:
        # 准备上传数据
        upload_files = []
        titles = []
        descriptions = []
        
        if mode == "unified":
            # 统一设置模式
            for i, file_path in enumerate(files):
                filename = file_path.split("/")[-1] if "/" in file_path else file_path.split("\\")[-1]
                title = f"{title_prefix} {filename}" if title_prefix else filename
                titles.append(title)
                descriptions.append(description or "")
                
                # 读取文件内容到内存中
                with open(file_path, "rb") as f:
                    file_content = f.read()
                upload_files.append(("files", (filename, file_content, "video/*")))
            
            use_auto_analyze = auto_analyze
        else:
            # 单独设置模式
            # 由于Gradio的限制，这里简化处理，使用文件名作为标题
            for i, file_path in enumerate(files):
                filename = file_path.split("/")[-1] if "/" in file_path else file_path.split("\\")[-1]
                titles.append(filename)
                descriptions.append("")
                
                # 读取文件内容到内存中
                with open(file_path, "rb") as f:
                    file_content = f.read()
                upload_files.append(("files", (filename, file_content, "video/*")))
            
            use_auto_analyze = individual_auto_analyze
        
        # 准备表单数据
        form_data = {
            "titles": titles,
            "descriptions": descriptions,
            "auto_analyze": use_auto_analyze
        }
        
        # 发送批量上传请求
        response = requests.post(
            "http://localhost:8000/api/v1/upload/batch",
            files=upload_files,
            data=form_data
        )
        
        if response.status_code == 200:
            result = response.json()
            if isinstance(result, list) and len(result) > 0:
                video_titles = [video.get('title', '未命名') for video in result]
                return f"成功上传 {len(result)} 个视频文件（{mode}模式）:\n" + "\n".join([f"- {title}" for title in video_titles])
            else:
                return f"上传完成，但返回结果异常: {result}"
        else:
            try:
                error_detail = response.json().get("detail", "上传失败")
            except:
                error_detail = f"HTTP {response.status_code}: {response.text}"
            return f"上传失败: {error_detail}"
            
    except Exception as e:
        return f"上传出错: {str(e)}"

def handle_simple_batch_upload(
    files: List[str],
    title_prefix: str,
    description: str,
    auto_analyze: bool
) -> str:
    """处理简化的批量视频上传（保留兼容性）"""
    return handle_flexible_upload(files, "unified", title_prefix, description, auto_analyze, None, False)

def handle_video_upload(
    files: List[str],
    title: str,
    description: str,
    auto_analyze: bool
) -> str:
    """处理单个视频上传（保留兼容性）"""
    if not files:
        return "请选择要上传的视频文件"
    
    try:
        # 只处理第一个文件
        file_path = files[0]
        filename = file_path.split("/")[-1] if "/" in file_path else file_path.split("\\")[-1]
        
        # 读取文件内容到内存中
        with open(file_path, "rb") as f:
            file_content = f.read()
        upload_file = ("file", (filename, file_content, "video/*"))
        
        form_data = {
            "title": title or filename,
            "description": description or "",
            "auto_analyze": auto_analyze
        }
        
        # 发送单文件上传请求
        response = requests.post(
            "http://localhost:8000/api/v1/upload/",
            files=[upload_file],
            data=form_data
        )
        
        if response.status_code == 200:
            result = response.json()
            return f"成功上传视频: {result.get('title', '未命名')}"
        else:
            try:
                error_detail = response.json().get("detail", "上传失败")
            except:
                error_detail = f"HTTP {response.status_code}: {response.text}"
            return f"上传失败: {error_detail}"
            
    except Exception as e:
        return f"上传出错: {str(e)}"

def load_videos_data(
    skip: int = 0,
    limit: int = 20,
    search: str = None,
    platform: str = None
) -> List[List[str]]:
    """加载视频数据"""
    try:
        params = {
            "skip": skip,
            "limit": limit
        }
        
        if search:
            params["search"] = search
        if platform and platform != "全部":
            params["platform"] = platform
        
        # 尝试多个可能的API端点
        api_endpoints = [
            "http://localhost:8000/api/v1/videos/",
            "http://localhost:8000/api/v1/videos"
        ]
        
        response = None
        for endpoint in api_endpoints:
            try:
                response = requests.get(endpoint, params=params, timeout=5)
                if response.status_code == 200:
                    break
                elif response.status_code != 404:
                    # 如果不是404错误，记录并继续尝试下一个端点
                    continue
            except requests.exceptions.RequestException:
                continue
        
        # 如果所有端点都失败，创建一个模拟响应
        if not response or response.status_code != 200:
            # 直接从数据库获取数据作为备选方案
            try:
                from app.core.database import SessionLocal
                from app.models.video import Video
                db = SessionLocal()
                videos = db.query(Video).offset(skip).limit(limit).all()
                
                mock_videos = []
                for video in videos:
                    mock_videos.append({
                        "id": video.id,
                        "title": video.title,
                        "platform": video.platform or "local",
                        "author": video.author or "未知",
                        "duration": video.duration,
                        "status": video.status,
                        "created_at": video.created_at.isoformat() if video.created_at else None
                    })
                db.close()
                
                # 创建模拟响应
                class MockResponse:
                    def __init__(self, data):
                        self._data = data
                        self.status_code = 200
                    def json(self):
                        return self._data
                
                response = MockResponse(mock_videos)
            except Exception as db_error:
                return [[f"数据库连接错误: {str(db_error)}", "错误", "错误", "0:00", "错误", "今天"]]
        
        if response.status_code == 200:
            videos = response.json()
            result = []
            
            # 检查返回的数据格式
            if isinstance(videos, list):
                video_list = videos
            elif isinstance(videos, dict) and 'items' in videos:
                video_list = videos['items']
            elif isinstance(videos, dict) and 'data' in videos:
                if isinstance(videos['data'], dict) and 'items' in videos['data']:
                    video_list = videos['data']['items']
                else:
                    video_list = videos['data'] if isinstance(videos['data'], list) else []
            else:
                video_list = []
            
            for video in video_list:
                # 格式化数据为表格行
                duration = video.get("duration")
                if duration:
                    duration_str = f"{int(duration//60)}:{int(duration%60):02d}"
                else:
                    duration_str = "未知"
                
                created_at = video.get("created_at", "")
                if created_at:
                    # 尝试解析日期格式
                    try:
                        from datetime import datetime
                        dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                        date_str = dt.strftime("%m-%d")
                    except:
                        date_str = created_at[:10] if len(created_at) >= 10 else "未知"
                else:
                    date_str = "未知"
                
                result.append([
                    video.get("title", "未命名"),
                    video.get("platform", "local"),
                    video.get("author", "未知"),
                    duration_str,
                    video.get("status", "active"),
                    date_str
                ])
            
            return result if result else [["暂无视频数据", "-", "-", "-", "-", "-"]]
        else:
            error_msg = f"API请求失败 (HTTP {response.status_code})"
            try:
                error_detail = response.json().get('detail', '')
                if error_detail:
                    error_msg += f": {error_detail}"
            except:
                pass
            return [[error_msg, "错误", "错误", "0:00", "错误", "今天"]]
            
    except Exception as e:
        return [[f"连接错误: {str(e)}", "错误", "错误", "0:00", "错误", "今天"]]

def simplify_status(original_status: str) -> str:
    """简化状态显示"""
    status_mapping = {
        "uploaded": "已上传",
        "active": "已上传",  # active也显示为已上传
        "analyzed": "已分析",
        "processing": "已上传",  # 处理中也显示为已上传
        "pending_analysis": "已上传",
        "deleted": "已删除",
        "failed": "已失效",
        "error": "已失效"
    }
    return status_mapping.get(original_status, "已失效")

def format_file_size(size_bytes: int) -> str:
    """格式化文件大小"""
    if not size_bytes:
        return "未知"
    
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f}{unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f}TB"

def create_selection_checkbox(video_id: int) -> str:
    """创建选择框"""
    return "☐"  # 使用Unicode复选框符号

def load_videos_data_enhanced(
    skip: int = 0,
    limit: int = 20,
    search: str = None,
    platform: str = None
) -> List[List[str]]:
    """加载增强的视频数据"""
    try:
        from app.core.database import SessionLocal
        from app.models.video import Video
        db = SessionLocal()
        
        query = db.query(Video)
        
        # 过滤已删除的视频
        query = query.filter(Video.status != 'deleted')
        
        # 搜索过滤
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                Video.title.ilike(search_term) |
                Video.original_filename.ilike(search_term)
            )
        
        # 平台过滤
        if platform and platform != "全部":
            if platform == "本地":
                query = query.filter(Video.platform == "local")
            else:
                query = query.filter(Video.platform == platform)
        
        videos = query.offset(skip).limit(limit).all()
        
        result = []
        for video in videos:
             # 选择框
             selection = create_selection_checkbox(video.id)
             
             # 视频ID
             video_id = str(video.id)
             
             # 源文件名
             original_filename = video.original_filename or "未知"
             
             # 标题（可编辑标识）
             title = video.title or "未命名"
             
             # 文件大小
             file_size = format_file_size(video.file_size)
             
             # 标签（暂时显示为占位符，后续实现）
             tags = "点击查看"
             
             # 简化状态
             status = simplify_status(video.status)
             
             # 日期
             created_at = video.created_at
             if created_at:
                 try:
                     date_str = created_at.strftime("%m-%d")
                 except:
                     date_str = "未知"
             else:
                 date_str = "未知"
             
             result.append([
                 selection,
                 video_id,
                 original_filename,
                 title,
                 file_size,
                 tags,
                 status,
                 date_str
             ])
        
        db.close()
        return result if result else [["暂无数据", "-", "-", "-", "-", "-", "-", "-"]]
        
    except Exception as e:
        return [[f"数据加载错误: {str(e)}", "错误", "错误", "错误", "错误", "错误", "今天"]]

def load_recent_videos(limit: int = 10) -> List[List[str]]:
    """加载最近上传的视频"""
    try:
        from app.core.database import SessionLocal
        from app.models.video import Video
        db = SessionLocal()
        
        videos = db.query(Video).filter(
            Video.status != 'deleted'
        ).order_by(
            Video.created_at.desc()
        ).limit(limit).all()
        
        result = []
        for video in videos:
            # 选择框
            selection = "☐"
            
            # 标题
            title = video.title or "未命名"
            
            # 上传时间
            created_at = video.created_at
            if created_at:
                try:
                    time_str = created_at.strftime("%m-%d %H:%M")
                except:
                    time_str = "未知"
            else:
                time_str = "未知"
            
            # 文件大小
            file_size = format_file_size(video.file_size)
            
            # 状态
            status = simplify_status(video.status)
            
            result.append([
                f"ID:{video.id}",  # 在选择列显示ID
                title,
                time_str,
                file_size,
                status
            ])
        
        db.close()
        return result if result else [["暂无视频", "-", "-", "-", "-"]]
        
    except Exception as e:
        return [[f"加载错误: {str(e)}", "错误", "错误", "错误", "错误"]]

def get_analysis_templates() -> List[tuple]:
    """获取分析模版列表"""
    templates = [
        ("内容分析模版", "content_analysis"),
        ("视觉质量评估", "visual_quality"),
        ("营销效果分析", "marketing_analysis"),
        ("教育内容评估", "educational_assessment"),
        ("娱乐价值分析", "entertainment_analysis"),
        ("技术内容审查", "technical_review")
    ]
    return templates

def get_template_content(template_key: str) -> str:
    """获取模版内容"""
    templates = {
        "content_analysis": "请分析这个视频的主要内容，包括：\n1. 主题和核心信息\n2. 内容结构和逻辑\n3. 目标受众分析\n4. 信息传达效果\n5. 内容价值评估",
        "visual_quality": "请评估视频的视觉质量，包括：\n1. 画面清晰度和分辨率\n2. 色彩和光线效果\n3. 构图和镜头运用\n4. 视觉美感评价\n5. 技术制作水平",
        "marketing_analysis": "请分析视频的营销效果，包括：\n1. 品牌信息传达\n2. 目标市场定位\n3. 营销策略分析\n4. 用户吸引力评估\n5. 转化潜力预测",
        "educational_assessment": "请评估视频的教育价值，包括：\n1. 知识点覆盖情况\n2. 教学方法和技巧\n3. 内容准确性验证\n4. 学习效果预期\n5. 适用年龄和水平",
        "entertainment_analysis": "请分析视频的娱乐价值，包括：\n1. 娱乐元素识别\n2. 观众参与度预测\n3. 情感共鸣分析\n4. 创意和新颖性\n5. 传播潜力评估",
        "technical_review": "请进行技术内容审查，包括：\n1. 技术准确性验证\n2. 实现方案评估\n3. 最佳实践对比\n4. 潜在问题识别\n5. 改进建议提供"
    }
    return templates.get(template_key, "请选择一个分析模版")

def get_tag_sets() -> List[tuple]:
    """获取标签集列表"""
    tag_sets = [
        ("通用内容标签", "general_content"),
        ("技术类标签", "technical"),
        ("教育类标签", "educational"),
        ("娱乐类标签", "entertainment"),
        ("商业类标签", "business"),
        ("生活类标签", "lifestyle")
    ]
    return tag_sets

def get_tag_set_content(tag_set_key: str) -> List[str]:
    """获取标签集内容"""
    tag_sets = {
        "general_content": ["教程", "评测", "新闻", "访谈", "演示", "分享", "讨论", "总结"],
        "technical": ["编程", "算法", "架构", "工具", "框架", "调试", "优化", "部署"],
        "educational": ["课程", "讲解", "实验", "案例", "练习", "考试", "答疑", "复习"],
        "entertainment": ["搞笑", "音乐", "舞蹈", "游戏", "影视", "综艺", "体育", "旅游"],
        "business": ["营销", "销售", "管理", "创业", "投资", "财务", "战略", "品牌"],
        "lifestyle": ["美食", "健康", "时尚", "家居", "育儿", "宠物", "园艺", "手工"]
    }
    return tag_sets.get(tag_set_key, [])

def get_recent_videos_choices() -> List[tuple]:
    """获取最近视频的下拉选择项"""
    try:
        from app.core.database import SessionLocal
        from app.models.video import Video
        db = SessionLocal()
        
        videos = db.query(Video).filter(
            Video.status != 'deleted'
        ).order_by(
            Video.created_at.desc()
        ).limit(10).all()
        
        choices = []
        for video in videos:
            title = video.title or "未命名"
            # 限制标题长度，添加时间信息
            if len(title) > 30:
                title = title[:30] + "..."
            
            created_time = ""
            if video.created_at:
                try:
                    created_time = video.created_at.strftime(" (%m-%d %H:%M)")
                except:
                    created_time = ""
            
            display_text = f"{title}{created_time}"
            choices.append((display_text, video.id))
        
        db.close()
        return choices if choices else [("暂无视频", 0)]
        
    except Exception as e:
        return [(f"加载错误: {str(e)}", 0)]

def load_templates_data() -> List[List[str]]:
    """加载提示词模版数据"""
    # 模拟数据，实际应从数据库获取
    templates = [
        ["1", "内容分析模版", "内容分析", "2024-08-27", "启用"],
        ["2", "视觉质量评估", "视觉质量", "2024-08-26", "启用"],
        ["3", "营销效果分析", "营销分析", "2024-08-25", "启用"],
        ["4", "教育内容评估", "教育评估", "2024-08-24", "禁用"],
        ["5", "娱乐价值分析", "娱乐分析", "2024-08-23", "启用"],
        ["6", "技术内容审查", "技术审查", "2024-08-22", "启用"]
    ]
    return templates

def get_template_by_id(template_id: int) -> dict:
    """根据ID获取模版详细信息"""
    # 模拟数据，实际应从数据库获取
    templates_detail = {
        1: {
            "id": 1,
            "name": "内容分析模版",
            "type": "content_analysis",
            "description": "用于分析视频的主要内容和核心信息",
            "content": "请分析这个视频的主要内容，包括：\n1. 主题和核心信息\n2. 内容结构和逻辑\n3. 目标受众分析\n4. 信息传达效果\n5. 内容价值评估",
            "tags": "内容,分析,评估",
            "is_active": True
        },
        2: {
            "id": 2,
            "name": "视觉质量评估",
            "type": "visual_quality",
            "description": "评估视频的视觉质量和制作水平",
            "content": "请评估视频的视觉质量，包括：\n1. 画面清晰度和分辨率\n2. 色彩和光线效果\n3. 构图和镜头运用\n4. 视觉美感评价\n5. 技术制作水平",
            "tags": "视觉,质量,评估",
            "is_active": True
        },
        3: {
            "id": 3,
            "name": "营销效果分析",
            "type": "marketing_analysis",
            "description": "分析视频的营销价值和效果",
            "content": "请分析视频的营销效果，包括：\n1. 品牌信息传达\n2. 目标市场定位\n3. 营销策略分析\n4. 用户吸引力评估\n5. 转化潜力预测",
            "tags": "营销,分析,效果",
            "is_active": True
        }
    }
    
    return templates_detail.get(template_id, {
        "id": 0,
        "name": "未知模版",
        "type": "custom",
        "description": "",
        "content": "",
        "tags": "",
        "is_active": False
    })

def load_tag_groups_data() -> List[List[str]]:
    """加载标签组数据"""
    # 模拟数据，实际应从数据库获取
    tag_groups = [
        ["1", "通用内容标签", "8", "2024-08-27"],
        ["2", "技术类标签", "8", "2024-08-26"],
        ["3", "教育类标签", "8", "2024-08-25"],
        ["4", "娱乐类标签", "8", "2024-08-24"],
        ["5", "商业类标签", "8", "2024-08-23"],
        ["6", "生活类标签", "8", "2024-08-22"]
    ]
    return tag_groups

def get_tag_groups_choices() -> List[tuple]:
    """获取标签组选择项"""
    choices = [
        ("通用内容标签", "general_content"),
        ("技术类标签", "technical"),
        ("教育类标签", "educational"),
        ("娱乐类标签", "entertainment"),
        ("商业类标签", "business"),
        ("生活类标签", "lifestyle")
    ]
    return choices

def load_tags_by_group(group_key: str) -> List[List[str]]:
    """根据标签组加载标签数据"""
    # 模拟数据，实际应从数据库获取
    tags_data = {
        "general_content": [
            ["1", "教程", "15", "2024-08-27"],
            ["2", "评测", "12", "2024-08-26"],
            ["3", "新闻", "8", "2024-08-25"],
            ["4", "访谈", "6", "2024-08-24"],
            ["5", "演示", "10", "2024-08-23"],
            ["6", "分享", "9", "2024-08-22"],
            ["7", "讨论", "7", "2024-08-21"],
            ["8", "总结", "5", "2024-08-20"]
        ],
        "technical": [
            ["9", "编程", "20", "2024-08-27"],
            ["10", "算法", "15", "2024-08-26"],
            ["11", "架构", "12", "2024-08-25"],
            ["12", "工具", "18", "2024-08-24"],
            ["13", "框架", "14", "2024-08-23"],
            ["14", "调试", "8", "2024-08-22"],
            ["15", "优化", "10", "2024-08-21"],
            ["16", "部署", "6", "2024-08-20"]
        ],
        "educational": [
            ["17", "课程", "25", "2024-08-27"],
            ["18", "讲解", "22", "2024-08-26"],
            ["19", "实验", "18", "2024-08-25"],
            ["20", "案例", "16", "2024-08-24"],
            ["21", "练习", "14", "2024-08-23"],
            ["22", "考试", "12", "2024-08-22"],
            ["23", "答疑", "10", "2024-08-21"],
            ["24", "复习", "8", "2024-08-20"]
        ]
    }
    return tags_data.get(group_key, [])

def get_tag_group_by_id(group_id: int) -> dict:
    """根据ID获取标签组详细信息"""
    # 模拟数据，实际应从数据库获取
    groups_detail = {
        1: {
            "id": 1,
            "name": "通用内容标签",
            "description": "适用于各种类型内容的通用标签集合"
        },
        2: {
            "id": 2,
            "name": "技术类标签",
            "description": "专门用于技术相关内容的标签集合"
        },
        3: {
            "id": 3,
            "name": "教育类标签",
            "description": "用于教育和学习内容的标签集合"
        }
    }
    
    return groups_detail.get(group_id, {
        "id": 0,
        "name": "未知标签组",
        "description": ""
    })

def get_tag_by_id(tag_id: int) -> dict:
    """根据ID获取标签详细信息"""
    # 模拟数据，实际应从数据库获取
    tags_detail = {
        1: {"id": 1, "name": "教程", "description": "教学和指导类内容", "color": "blue"},
        2: {"id": 2, "name": "评测", "description": "产品或服务评测内容", "color": "green"},
        3: {"id": 3, "name": "新闻", "description": "新闻资讯类内容", "color": "red"},
        9: {"id": 9, "name": "编程", "description": "编程和代码相关内容", "color": "purple"},
        10: {"id": 10, "name": "算法", "description": "算法和数据结构内容", "color": "orange"},
        17: {"id": 17, "name": "课程", "description": "系统性的课程内容", "color": "yellow"}
    }
    
    return tags_detail.get(tag_id, {
        "id": 0,
        "name": "未知标签",
        "description": "",
        "color": "blue"
    })

def get_ai_configs() -> List[tuple]:
    """获取AI配置列表"""
    # 这里应该从数据库或配置文件获取，暂时使用模拟数据
    configs = [
        ("GPT-4 Vision (OpenAI)", "gpt4_vision"),
        ("Claude 3 (Anthropic)", "claude3"),
        ("Gemini Pro Vision (Google)", "gemini_pro_vision"),
        ("通义千问 (阿里云)", "qwen_vl"),
        ("文心一言 (百度)", "ernie_bot")
    ]
    return configs

def get_total_videos_count() -> int:
    """获取视频总数"""
    try:
        from app.core.database import SessionLocal
        from app.models.video import Video
        db = SessionLocal()
        total = db.query(Video).filter(Video.status != 'deleted').count()
        db.close()
        return total
    except Exception as e:
        return 0

def update_page_info(current_page: int, page_size: int, total_count: int) -> str:
    """更新分页信息显示"""
    if total_count == 0:
        return "<div style='display: flex; align-items: center; justify-content: flex-end; height: 32px; font-size: 0.8rem; color: #666; white-space: nowrap;'>暂无数据</div>"
    
    start_item = (current_page - 1) * page_size + 1
    end_item = min(current_page * page_size, total_count)
    
    return f"<div style='display: flex; align-items: center; justify-content: flex-end; height: 32px; font-size: 0.8rem; color: #666; white-space: nowrap;'>显示 {start_item}-{end_item} 条，共 {total_count} 条</div>"

def search_videos_handler(search_term: str, platform: str) -> List[List[str]]:
    """搜索视频处理函数"""
    return load_videos_data(search=search_term, platform=platform)

def handle_download(url, quality, format_pref, audio_only, priority):
    """处理下载请求"""
    return "下载功能开发中...", "0%"

def handle_batch_download(urls, quality, format_pref):
    """处理批量下载"""
    return "批量下载功能开发中...", "0%"

if __name__ == "__main__":
    app = create_gradio_app()
    app.launch()