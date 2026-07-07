"""数据仓库 - 批改记录与日志的数据库操作"""
import pymysql
from datetime import datetime


class GradingRepository:
    """批改数据仓库"""

    def __init__(self, db):
        self.db = db

    def create_batch(self, max_count=0) -> int:
        with self.db.connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO grading_batches (max_count, status) VALUES (%s, 'running')",
                    (max_count,)
                )
                return cursor.lastrowid

    def finish_batch(self, batch_id: int, status: str, total: int, success: int, fail: int):
        with self.db.connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "UPDATE grading_batches SET ended_at = NOW(), status = %s, "
                    "total_count = %s, success_count = %s, fail_count = %s WHERE id = %s",
                    (status, total, success, fail, batch_id)
                )

    def create_record(self, batch_id: int, task_id: str, screenshot_path: str) -> int:
        with self.db.connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO grading_records (batch_id, task_id, screenshot_path, status) VALUES (%s, %s, %s, 'pending')",
                    (batch_id, task_id, screenshot_path)
                )
                return cursor.lastrowid

    def update_screenshot_path(self, record_id: int, screenshot_path: str):
        with self.db.connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "UPDATE grading_records SET screenshot_path = %s WHERE id = %s",
                    (screenshot_path, record_id)
                )

    def finish_record(self, record_id: int, score: int, status: str, error_message: str,
                      vlm_response: str, vlm_model: str, duration_ms: int,
                      score_secondary: int = None, vlm_response_secondary: str = None,
                      vlm_model_secondary: str = None, grading_mode: str = 'single',
                      score_consistent: int = None):
        with self.db.connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "UPDATE grading_records SET score = %s, status = %s, error_message = %s, "
                    "vlm_response = %s, vlm_model = %s, duration_ms = %s, "
                    "score_secondary = %s, vlm_response_secondary = %s, vlm_model_secondary = %s, "
                    "grading_mode = %s, score_consistent = %s WHERE id = %s",
                    (score, status, error_message, vlm_response, vlm_model, duration_ms,
                     score_secondary, vlm_response_secondary, vlm_model_secondary,
                     grading_mode, score_consistent, record_id)
                )

    def update_human_screenshot_path(self, record_id: int, screenshot_human_path: str):
        with self.db.connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "UPDATE grading_records SET screenshot_human_path = %s WHERE id = %s",
                    (screenshot_human_path, record_id)
                )

    def get_records(self, batch_id=None, page=1, page_size=50, consistent=None):
        offset = (page - 1) * page_size
        conditions = ["status != 'pending'"]
        params = []
        if batch_id:
            conditions.append("batch_id = %s")
            params.append(batch_id)
        if consistent in (0, 1):
            conditions.append("score_consistent = %s")
            params.append(consistent)
        where = " WHERE " + " AND ".join(conditions)
        with self.db.connection() as conn:
            with conn.cursor(pymysql.cursors.DictCursor) as cursor:
                cursor.execute(f"SELECT COUNT(*) as total FROM grading_records{where}", tuple(params))
                total = cursor.fetchone()['total']
                cursor.execute(
                    f"SELECT * FROM grading_records{where} ORDER BY created_at DESC LIMIT %s OFFSET %s",
                    tuple(params) + (page_size, offset)
                )
                return total, cursor.fetchall()

    def insert_step_execution(self, record_id: int, step_id: str, step_type: str,
                              status: str, duration_ms: int = None, error_message: str = None):
        with self.db.connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO step_executions (record_id, step_id, step_type, status, duration_ms, error_message) "
                    "VALUES (%s, %s, %s, %s, %s, %s)",
                    (record_id, step_id, step_type, status, duration_ms, error_message)
                )

    def get_statistics(self, start_date: str, end_date: str):
        with self.db.connection() as conn:
            with conn.cursor(pymysql.cursors.DictCursor) as cursor:
                cursor.execute(
                    "SELECT DATE(created_at) as date, COUNT(*) as total, "
                    "SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as success "
                    "FROM grading_records WHERE created_at BETWEEN %s AND %s GROUP BY DATE(created_at)",
                    (start_date, end_date)
                )
                return cursor.fetchall()


class LogRepository:
    """日志数据仓库"""

    def __init__(self, db):
        self.db = db

    def insert_log(self, level: str, module: str, message: str):
        with self.db.connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO system_logs (level, module, message) VALUES (%s, %s, %s)",
                    (level, module, message)
                )


class VlmCallLogRepository:
    """VLM 调用日志仓库"""

    def __init__(self, db):
        self.db = db

    def insert(self, record_id: int, provider: str, model: str, base_url: str,
               prompt: str, image_path: str, raw_response: str, score: int,
               duration_ms: int, status: str, error_message: str = None):
        with self.db.connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO vlm_call_logs "
                    "(record_id, provider, model, base_url, prompt, image_path, "
                    "raw_response, score, duration_ms, status, error_message) "
                    "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                    (record_id, provider, model, base_url, prompt, image_path,
                     raw_response, score, duration_ms, status, error_message)
                )

    def get_logs(self, page=1, page_size=50, record_id=None):
        offset = (page - 1) * page_size
        with self.db.connection() as conn:
            with conn.cursor(pymysql.cursors.DictCursor) as cursor:
                if record_id:
                    cursor.execute(
                        "SELECT COUNT(*) as total FROM vlm_call_logs WHERE record_id = %s",
                        (record_id,)
                    )
                    total = cursor.fetchone()['total']
                    cursor.execute(
                        "SELECT * FROM vlm_call_logs WHERE record_id = %s "
                        "ORDER BY created_at DESC LIMIT %s OFFSET %s",
                        (record_id, page_size, offset)
                    )
                else:
                    cursor.execute("SELECT COUNT(*) as total FROM vlm_call_logs")
                    total = cursor.fetchone()['total']
                    cursor.execute(
                        "SELECT * FROM vlm_call_logs ORDER BY created_at DESC LIMIT %s OFFSET %s",
                        (page_size, offset)
                    )
                return total, cursor.fetchall()
