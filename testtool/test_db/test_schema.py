"""测试数据库表结构定义与初始化"""
import pytest
from unittest.mock import MagicMock, call

from src.db.schema import DDL_STATEMENTS, NEW_RECORD_COLUMNS, init_database


class TestDDLStatements:
    """测试 DDL 语句定义"""

    def test_ddl_statements_not_empty(self):
        """DDL_STATEMENTS 不应为空"""
        assert len(DDL_STATEMENTS) > 0

    def test_ddl_contains_grading_batches(self):
        """应包含 grading_batches 表定义"""
        found = any('grading_batches' in ddl for ddl in DDL_STATEMENTS)
        assert found is True

    def test_ddl_contains_grading_records(self):
        """应包含 grading_records 表定义"""
        found = any('grading_records' in ddl for ddl in DDL_STATEMENTS)
        assert found is True

    def test_ddl_contains_step_executions(self):
        """应包含 step_executions 表定义"""
        found = any('step_executions' in ddl for ddl in DDL_STATEMENTS)
        assert found is True

    def test_ddl_contains_vlm_call_logs(self):
        """应包含 vlm_call_logs 表定义"""
        found = any('vlm_call_logs' in ddl for ddl in DDL_STATEMENTS)
        assert found is True

    def test_ddl_contains_system_logs(self):
        """应包含 system_logs 表定义"""
        found = any('system_logs' in ddl for ddl in DDL_STATEMENTS)
        assert found is True

    def test_all_ddls_are_create_table(self):
        """所有 DDL 语句应为 CREATE TABLE IF NOT EXISTS"""
        for ddl in DDL_STATEMENTS:
            assert 'CREATE TABLE IF NOT EXISTS' in ddl


class TestInitDatabase:
    """测试数据库初始化函数"""

    def test_init_database_executes_all_ddls(self, mock_db):
        """init_database 应执行所有 DDL 语句及迁移检查"""
        mock_conn = mock_db.connection.return_value.__enter__.return_value
        mock_cursor = mock_conn.cursor.return_value
        # 模拟所有列已存在且 status 枚举已包含 pending
        mock_cursor.fetchone.return_value = {'cnt': 1}

        init_database(mock_db)

        # DDL + 每条新列的 information_schema 存在性检查 + status 枚举检查
        assert mock_cursor.execute.call_count == len(DDL_STATEMENTS) + len(NEW_RECORD_COLUMNS) + 1

    def test_init_database_uses_connection_context_manager(self, mock_db):
        """init_database 应正确使用 connection context manager"""
        mock_conn = mock_db.connection.return_value.__enter__.return_value
        mock_cursor = mock_conn.cursor.return_value
        mock_cursor.fetchone.return_value = {'cnt': 1}

        init_database(mock_db)

        # init_database 内部会分别开启两次连接（DDL 执行 + 迁移）
        assert mock_db.connection.call_count == 2
        cm = mock_db.connection.return_value
        assert cm.__enter__.call_count == 2
        assert cm.__exit__.call_count == 2

    def test_init_database_executes_correct_sql(self, mock_db):
        """init_database 应执行正确的 SQL"""
        mock_conn = mock_db.connection.return_value.__enter__.return_value
        mock_cursor = mock_conn.cursor.return_value
        mock_cursor.fetchone.return_value = {'cnt': 1}

        init_database(mock_db)

        executed_calls = mock_cursor.execute.call_args_list
        assert len(executed_calls) == len(DDL_STATEMENTS) + len(NEW_RECORD_COLUMNS) + 1

        for i, ddl in enumerate(DDL_STATEMENTS):
            actual_sql = executed_calls[i][0][0]
            assert actual_sql == ddl

        for i, (col, _ddl) in enumerate(NEW_RECORD_COLUMNS, start=len(DDL_STATEMENTS)):
            actual_sql = executed_calls[i][0][0]
            assert 'information_schema.columns' in actual_sql
            assert col in executed_calls[i][0][1]

        # 最后一项为 status 枚举存在性检查
        assert 'status' in executed_calls[-1][0][0]


def test_migrate_grading_records_adds_missing_columns(mock_db):
    """列不存在且 status 枚举未扩展时应执行 ALTER TABLE 添加"""
    from src.db.schema import migrate_grading_records, NEW_RECORD_COLUMNS

    cursor = mock_db.connection().__enter__().cursor()
    # 模拟 information_schema 查询：每列都不存在，status 枚举也不包含 pending
    cursor.fetchone.return_value = {'cnt': 0}

    migrate_grading_records(mock_db)

    executed = [c.args[0] for c in cursor.execute.call_args_list]
    alters = [s for s in executed if s.strip().upper().startswith('ALTER TABLE')]
    assert len(alters) == len(NEW_RECORD_COLUMNS) + 1
    assert any('score_secondary' in s for s in alters)
    assert any('grading_mode' in s for s in alters)
    assert any('screenshot_human_path' in s for s in alters)
    assert any("MODIFY COLUMN status" in s for s in alters)


def test_migrate_grading_records_skips_existing_columns(mock_db):
    """列已存在时不应执行 ALTER"""
    from src.db.schema import migrate_grading_records

    cursor = mock_db.connection().__enter__().cursor()
    cursor.fetchone.return_value = {'cnt': 1}  # 所有列都已存在

    migrate_grading_records(mock_db)

    executed = [c.args[0] for c in cursor.execute.call_args_list]
    alters = [s for s in executed if s.strip().upper().startswith('ALTER TABLE')]
    assert len(alters) == 0
