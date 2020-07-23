from abc import ABC

from src.homi.app import BaseApp


class BaseServiceConfig(ABC):
    def __init__(self, name: str, default: dict = None):
        self._default = default
        self.name = name
        self.app: BaseApp = None

    def register_app(self, app: BaseApp):
        self.app = app

    def get_config(self) -> dict:
        return self._default


class MergeConfig(BaseServiceConfig):

    def register_app(self, app: BaseApp):
        super().register_app(app)
        app_config = self.app.config.get(self.name)
        if app_config:
            self._default.update(app_config)