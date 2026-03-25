from __future__ import annotations

from app.tasks.celery_app import celery_app

app = celery_app
celery = celery_app

__all__ = ["app", "celery", "celery_app"]

