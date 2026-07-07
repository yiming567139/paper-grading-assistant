"""
配置工具模块

管理和读写config/config.json配置文件。
支持读取、修改、保存配置，以及使用点号路径访问嵌套配置。

Author: AI助手
Version: 1.0.0
"""
import json
from pathlib import Path


class ConfigManager:
    """
    配置管理器类

    管理应用程序的配置，支持从JSON文件加载和保存。

    Attributes:
        config_path: 配置文件路径
        config: 配置字典对象

    Example:
        cm = ConfigManager()
        mock_mode = cm.get('dify.mock_mode')
        cm.set('dify.mock_mode', True)
        cm.save_config()
    """

    def __init__(self, config_path=None):
        if config_path is None:
            # 获取项目根目录
            project_root = Path(__file__).parent.parent.parent
            config_path = project_root / "config" / "config.json"
        self.config_path = Path(config_path)
        self.config = self.load()

    def load(self):
        """加载配置"""
        with open(self.config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
        return self.config

    def save(self):
        """保存配置"""
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, ensure_ascii=False, indent=2)

    def get(self, key, default=None):
        """获取配置值"""
        keys = key.split('.')
        value = self.config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
            if value is None:
                return default
        return value

    def set(self, key, value):
        """设置配置值"""
        keys = key.split('.')
        config = self.config
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        config[keys[-1]] = value

    def save_config(self):
        """保存配置到文件"""
        self.save()
