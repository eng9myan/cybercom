try:
    from .celery import app as celery_app

    __all__ = ("celery_app",)
except (ImportError, AttributeError):
    # Celery unavailable in test/migration environments (platform stdlib conflict)
    pass
