"""主入口 - 启动 Flask HTTP 服务"""
import sys
import json
import webbrowser
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.app import app, init_app
from src.config_loader import load_config


def main():
    config = load_config(project_root / 'config' / 'config.json')
    init_app(config)

    host = config.get('http_server', {}).get('host', '127.0.0.1')
    port = config.get('http_server', {}).get('port', 8081)

    if config.get('window', {}).get('auto_open_browser', True):
        webbrowser.open(f'http://localhost:{port}')

    from src.app import logger
    logger.info(f'服务已启动: http://localhost:{port}')
    # 生产环境建议使用: gunicorn -w 4 -b 0.0.0.0:8081 src.main:app
    app.run(host=host, port=port, threaded=True)


if __name__ == '__main__':
    main()
