"""数据库初始化脚本

检查并创建业务数据库和表结构。
支持命令行参数覆盖配置，支持重置和导出纯 SQL。

用法：
  python init_db.py                  # 使用 config.json 中的配置
  python init_db.py --reset          # 删除并重建所有表
  python init_db.py --export-sql     # 导出纯 SQL 文件
  python init_db.py --host 127.0.0.1 --port 3306 --user root --password 123456
"""
import argparse
import json
import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / 'src'))

from db.schema import DDL_STATEMENTS

EXPECTED_TABLES = [
    'grading_batches',
    'grading_records',
    'step_executions',
    'vlm_call_logs',
    'system_logs',
]

# ── 彩色输出 ──────────────────────────────────────────────

def _color(code, msg):
    return f'\033[{code}m{msg}\033[0m'

def ok(msg):    print(_color(32, f'[OK]    {msg}'))
def info(msg):  print(_color(36, f'[INFO]  {msg}'))
def warn(msg):  print(_color(33, f'[WARN]  {msg}'))
def error(msg): print(_color(31, f'[ERROR] {msg}'))


# ── 配置加载 ──────────────────────────────────────────────

def load_config() -> dict:
    config_path = project_root / 'config' / 'config.json'
    if not config_path.exists():
        error(f'配置文件不存在: {config_path}')
        sys.exit(1)
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def resolve_db_config(args) -> dict:
    """合并 config.json 和命令行参数，命令行参数优先"""
    config = load_config()
    base = config.get('mysql', {})
    overrides = {
        'host': args.host,
        'port': args.port,
        'user': args.user,
        'password': args.password,
        'database': args.database,
    }
    for k, v in overrides.items():
        if v is not None:
            base[k] = v
    return base


# ── 数据库操作 ────────────────────────────────────────────

def connect_without_db(db_config: dict):
    """连接 MySQL 但不指定数据库，用于建库"""
    import pymysql
    cfg = {k: v for k, v in db_config.items() if k != 'database'}
    return pymysql.connect(**cfg)


def connect_to_db(db_config: dict):
    """连接到指定数据库"""
    import pymysql
    return pymysql.connect(**db_config)


def test_mysql_connection(db_config: dict) -> bool:
    """测试 MySQL 是否可达"""
    import pymysql
    try:
        conn = connect_without_db(db_config)
        conn.close()
        return True
    except pymysql.err.OperationalError as e:
        code, msg = e.args
        if code in (2003, 2006):
            error(f'无法连接 MySQL 服务器 {db_config["host"]}:{db_config["port"]}，请确认 MySQL 服务已启动')
        elif code in (1045, 1698):
            error(f'MySQL 认证失败: {msg}')
        else:
            error(f'MySQL 连接失败: {msg}')
        return False
    except Exception as e:
        error(f'MySQL 连接异常: {e}')
        return False


def ensure_database(db_config: dict) -> bool:
    """确保数据库存在"""
    database = db_config.get('database', 'grading_app')
    try:
        conn = connect_without_db(db_config)
        with conn.cursor() as cursor:
            cursor.execute("SHOW DATABASES LIKE %s", (database,))
            if cursor.fetchone():
                ok(f'数据库 "{database}" 已存在')
            else:
                info(f'数据库 "{database}" 不存在，正在创建...')
                cursor.execute(
                    f"CREATE DATABASE `{database}` "
                    "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
                )
                conn.commit()
                ok(f'数据库 "{database}" 创建成功')
        conn.close()
        return True
    except Exception as e:
        error(f'创建数据库失败: {e}')
        return False


def ensure_tables(db_config: dict) -> bool:
    """确保所有业务表存在"""
    database = db_config.get('database', 'grading_app')
    try:
        conn = connect_to_db(db_config)
        with conn.cursor() as cursor:
            cursor.execute("SHOW TABLES")
            existing = {row[0] for row in cursor.fetchall()}
            missing = [t for t in EXPECTED_TABLES if t not in existing]

            if not missing:
                ok('所有业务表已存在')
            else:
                info(f'缺失表: {missing}，正在创建...')
                for ddl in DDL_STATEMENTS:
                    cursor.execute(ddl)
                conn.commit()
                ok('业务表创建完成')
        conn.close()
        return True
    except Exception as e:
        error(f'建表失败: {e}')
        return False


def reset_tables(db_config: dict) -> bool:
    """删除并重建所有表"""
    database = db_config.get('database', 'grading_app')
    try:
        conn = connect_to_db(db_config)
        with conn.cursor() as cursor:
            info('正在删除所有业务表...')
            # 按依赖顺序反序删除
            for table in reversed(EXPECTED_TABLES):
                cursor.execute(f"DROP TABLE IF EXISTS `{table}`")
            conn.commit()
            ok('所有表已删除')

            info('正在重新创建表...')
            for ddl in DDL_STATEMENTS:
                cursor.execute(ddl)
            conn.commit()
            ok('所有表已重建')
        conn.close()
        return True
    except Exception as e:
        error(f'重置失败: {e}')
        return False


def verify_tables(db_config: dict) -> bool:
    """验证所有表存在并打印状态"""
    database = db_config.get('database', 'grading_app')
    try:
        conn = connect_to_db(db_config)
        all_ok = True
        print()
        print(f'  {"表名":<25} {"状态":<10} {"行数"}')
        print(f'  {"-" * 25} {"-" * 10} {"-" * 10}')
        with conn.cursor() as cursor:
            for table in EXPECTED_TABLES:
                cursor.execute("SHOW TABLES LIKE %s", (table,))
                exists = cursor.fetchone() is not None
                if exists:
                    cursor.execute(f"SELECT COUNT(*) FROM `{table}`")
                    count = cursor.fetchone()[0]
                    print(f'  {table:<25} {_color(32, "OK"):<19} {count}')
                else:
                    print(f'  {table:<25} {_color(31, "MISSING"):<19} -')
                    all_ok = False
        conn.close()
        print()
        return all_ok
    except Exception as e:
        error(f'验证失败: {e}')
        return False


# ── SQL 导出 ──────────────────────────────────────────────

def export_sql(db_config: dict):
    """导出纯 SQL 初始化脚本"""
    database = db_config.get('database', 'grading_app')
    output_path = project_root / 'init_grading_app.sql'

    lines = [
        f'-- grading_app 数据库初始化脚本',
        f'-- 由 init_db.py --export-sql 自动生成',
        f'-- 执行方式: mysql -u root -p < init_grading_app.sql',
        f'',
        f'CREATE DATABASE IF NOT EXISTS `{database}` '
        'CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;',
        f'USE `{database}`;',
        f'',
    ]
    for ddl in DDL_STATEMENTS:
        lines.append(ddl.strip())
        lines.append('')

    output_path.write_text('\n'.join(lines), encoding='utf-8')
    ok(f'SQL 文件已导出: {output_path}')


# ── 命令行参数 ────────────────────────────────────────────

def parse_args():
    parser = argparse.ArgumentParser(description='grading_app 数据库初始化工具')
    parser.add_argument('--host', help='MySQL 主机 (默认从 config.json)')
    parser.add_argument('--port', type=int, help='MySQL 端口')
    parser.add_argument('--user', help='MySQL 用户名')
    parser.add_argument('--password', help='MySQL 密码')
    parser.add_argument('--database', help='数据库名')
    parser.add_argument('--reset', action='store_true',
                        help='删除并重建所有表（会丢失数据）')
    parser.add_argument('--export-sql', action='store_true',
                        help='导出纯 SQL 文件，不执行任何操作')
    return parser.parse_args()


# ── 主流程 ────────────────────────────────────────────────

def main():
    args = parse_args()
    db_config = resolve_db_config(args)

    print('=' * 55)
    print('  grading_app 数据库初始化工具')
    print('=' * 55)
    print(f'  MySQL:  {db_config.get("host")}:{db_config.get("port", 3306)}')
    print(f'  用户:   {db_config.get("user")}')
    print(f'  数据库: {db_config.get("database", "grading_app")}')
    print('-' * 55)

    # 导出模式
    if args.export_sql:
        export_sql(db_config)
        return

    # 测试连接
    info('正在连接 MySQL...')
    if not test_mysql_connection(db_config):
        sys.exit(1)
    ok('MySQL 连接成功')

    # 确保数据库存在
    if not ensure_database(db_config):
        sys.exit(1)

    # 重置或建表
    if args.reset:
        warn('--reset 将删除所有业务表及其数据！')
        confirm = input('  确认继续？输入 yes 继续: ').strip().lower()
        if confirm != 'yes':
            info('已取消')
            return
        if not reset_tables(db_config):
            sys.exit(1)
    else:
        if not ensure_tables(db_config):
            sys.exit(1)

    # 验证
    if not verify_tables(db_config):
        sys.exit(1)

    print('-' * 55)
    ok('数据库初始化完成')
    print('=' * 55)


if __name__ == '__main__':
    main()
