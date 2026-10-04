"""Celery app for the standalone platform test project.

Needed so `.delay()`/`.apply_async()` calls made from code under test (e.g.
platform.ephemeral_envs' views) actually execute — without a configured
Celery app, `shared_task` falls back to an unconfigured default app that
tries to reach a real broker at its hardcoded default address, ignoring
`CELERY_TASK_ALWAYS_EAGER` in Django settings entirely.

No `autodiscover_tasks()` call, unlike cycom/cymed's own celery.py: nothing
in this project's own test suite needs it (every task used here is already
imported directly by ordinary Python imports in the code that calls
`.delay()`), and it's one less thing scanning every INSTALLED_APP during
Django's own bootstrap.

(A pre-existing, unrelated bug was chased into this file and ruled out
while adding it: 3 `platform.provisioning` routes 404 under
`run_tests.py`. Confirmed via `git stash` that this already happens on a
clean checkout with none of this file's/this app's changes present --
it isn't caused by this file or by platform.ephemeral_envs. Left as its
own separate, not-yet-diagnosed issue.)
"""
import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

app = Celery("platform_core")
app.config_from_object("django.conf:settings", namespace="CELERY")


@app.task(bind=True)
def debug_task(self):
    pass
