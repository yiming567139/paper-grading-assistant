"""MySQL 数据库连接管理"""
import pymysql
from contextlib import contextmanager


class Database:
    """MySQL 连接管理器"""

    def __init__(self, config: dict):
        self.config = {
            'host': config.get('host', 'localhost'),
            'port': config.get('port', 3306),
            'database': config.get('database', 'grading_app'),
            'user': config.get('user', 'root'),
            'password': config.get('password', ''),
            'charset': config.get('charset', 'utf8mb4'),
            'autocommit': False,
        }
        self._connected = False
        self._conn = None

    @contextmanager
    def connection(self):
        if self._conn is None or not self._conn.open:
            self._conn = pymysql.connect(**self.config)
        try:
            yield self._conn
            self._conn.commit()
        except Exception:
            self._conn.rollback()
            raise

    def test_connection(self) -> bool:
        try:
            with self.connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute('SELECT 1')
                    return True
        except Exception:
            return False
