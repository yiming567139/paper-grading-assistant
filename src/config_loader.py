"""配置加载器 - 支持环境变量覆盖配置文件"""
import json
import os
from pathlib import Path


def load_config(config_path: Path):
    """加载配置，环境变量优先于配置文件。"""
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)

    if api_key := os.getenv('LLM_API_KEY'):
        config['llm']['api_key'] = api_key
    if base_url := os.getenv('LLM_BASE_URL'):
        config['llm']['base_url'] = base_url
    if db_password := os.getenv('MYSQL_PASSWORD'):
        config['mysql']['password'] = db_password

    return config
