# -*- coding: utf-8 -*-
import importlib
import logging
import os
import sys

logger = logging.getLogger(__name__)

# Track hot-loaded modules at runtime
LOADED_APPS = {}


class AppRegistry:
    """Micro-kernel registry managing hot-loading of decoupled business applications."""

    @staticmethod
    def hot_load_apps(active_apps: list):
        """Dynamically imports apps from the /apps path and registers their routers/models."""
        apps_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "apps"))
        if apps_path not in sys.path:
            sys.path.append(apps_path)

        for app_name in active_apps:
            if app_name in LOADED_APPS:
                continue

            try:
                logger.info(f"Initiating hot-load sequence for: {app_name}")
                # Dynamically import the app module package
                module = importlib.import_module(app_name)
                LOADED_APPS[app_name] = module
                logger.info(f"Module {app_name} successfully hot-loaded into registry.")
            except Exception as e:
                logger.error(f"Failed to hot-load application {app_name}: {str(e)}")

    @staticmethod
    def get_active_apps() -> list:
        return list(LOADED_APPS.keys())

    @staticmethod
    def unload_app(app_name: str):
        """Unregisters an app from the micro-kernel registry."""
        if app_name in LOADED_APPS:
            del LOADED_APPS[app_name]
            logger.info(f"Application {app_name} unloaded from registry.")
