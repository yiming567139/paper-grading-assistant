"""
[已废弃] 纯API后端启动脚本

APIServer 模块已移除。请使用 python -m src.main 启动服务。
保留此文件仅作历史参考，运行时会自动转发到新的启动入口。
"""
import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.main import main

if __name__ == "__main__":
    print("[警告] server_only.py 已废弃，请使用 python -m src.main 启动")
    main()
