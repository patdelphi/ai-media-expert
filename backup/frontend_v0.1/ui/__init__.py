"""用户界面模块

提供基于Gradio的Web用户界面。
"""

from app.ui.gradio_app import create_gradio_app

__all__ = [
    "create_gradio_app",
]