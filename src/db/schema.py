"""数据库表结构定义与自动建表"""

import pymysql

DDL_STATEMENTS = [
    """
    CREATE TABLE IF NOT EXISTS grading_batches (
        id INT AUTO_INCREMENT PRIMARY KEY,
        started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        ended_at TIMESTAMP NULL,
        max_count INT DEFAULT 0 COMMENT '计划批改数量，0=无限',
        status ENUM('running', 'completed', 'stopped', 'error') DEFAULT 'running',
        total_count INT DEFAULT 0,
        success_count INT DEFAULT 0,
        fail_count INT DEFAULT 0
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """,
    """
    CREATE TABLE IF NOT EXISTS grading_records (
        id INT AUTO_INCREMENT PRIMARY KEY,
        batch_id INT NOT NULL,
        task_id VARCHAR(50) NOT NULL,
        screenshot_path VARCHAR(500) COMMENT '截图完整路径',
        score INT COMMENT 'AI评分结果',
        status ENUM('pending', 'success', 'fail', 'error', 'skipped') DEFAULT 'success',
        error_message TEXT,
        vlm_response TEXT COMMENT '大模型原始返回',
        vlm_model VARCHAR(100) COMMENT '使用的模型',
        duration_ms INT COMMENT '单次批改耗时',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (batch_id) REFERENCES grading_batches(id) ON DELETE CASCADE,
        INDEX idx_batch_id (batch_id),
        INDEX idx_created_at (created_at)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """,
    """
    CREATE TABLE IF NOT EXISTS step_executions (
        id INT AUTO_INCREMENT PRIMARY KEY,
        record_id INT NOT NULL,
        step_id VARCHAR(50) NOT NULL COMMENT '如 screenshot, vlm_eval',
        step_type VARCHAR(50) NOT NULL,
        status ENUM('start', 'success', 'fail') DEFAULT 'start',
        duration_ms INT,
        error_message TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (record_id) REFERENCES grading_records(id) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """,
    """
    CREATE TABLE IF NOT EXISTS vlm_call_logs (
        id BIGINT AUTO_INCREMENT PRIMARY KEY,
        record_id INT COMMENT '关联的批改记录ID',
        provider VARCHAR(50),
        model VARCHAR(100),
        base_url VARCHAR(500),
        prompt TEXT,
        image_path VARCHAR(500),
        raw_response TEXT,
        score INT,
        duration_ms INT COMMENT '调用耗时(ms)',
        status ENUM('success','fail') DEFAULT 'success',
        error_message TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        INDEX idx_record_id (record_id),
        INDEX idx_created_at (created_at)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """,
    """
    CREATE TABLE IF NOT EXISTS system_logs (
        id BIGINT AUTO_INCREMENT PRIMARY KEY,
        level ENUM('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL') DEFAULT 'INFO',
        module VARCHAR(100) COMMENT '来源模块',
        message TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        INDEX idx_created_at (created_at),
        INDEX idx_level (level)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """,
]


NEW_RECORD_COLUMNS = [
    ("score_secondary", "INT NULL COMMENT '副模型评分'"),
    ("vlm_response_secondary", "TEXT NULL COMMENT '副模型原始返回'"),
    ("vlm_model_secondary", "VARCHAR(100) NULL COMMENT '副模型名称'"),
    ("grading_mode", "ENUM('single','dual') DEFAULT 'single' COMMENT '批改模式'"),
    ("score_consistent", "TINYINT(1) NULL COMMENT '双评一致=1/不一致或失败=0/单评=NULL'"),
    ("screenshot_human_path", "VARCHAR(500) NULL COMMENT '人看截图完整路径'"),
]


def migrate_grading_records(db):
    """为 grading_records 幂等补充新列与枚举值"""
    with db.connection() as conn:
        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            for col, ddl in NEW_RECORD_COLUMNS:
                cursor.execute(
                    "SELECT COUNT(*) AS cnt FROM information_schema.columns "
                    "WHERE table_schema = DATABASE() AND table_name = 'grading_records' "
                    "AND column_name = %s",
                    (col,)
                )
                row = cursor.fetchone()
                exists = row['cnt'] if row else 0
                if not exists:
                    cursor.execute(f"ALTER TABLE grading_records ADD COLUMN {col} {ddl}")
            # 幂等扩展 status 枚举：若不存在 pending 则添加
            cursor.execute(
                "SELECT COUNT(*) AS cnt FROM information_schema.columns "
                "WHERE table_schema = DATABASE() AND table_name = 'grading_records' "
                "AND column_name = 'status' AND column_type LIKE %s",
                ("%pending%",)
            )
            row = cursor.fetchone()
            has_pending = row and row['cnt'] > 0
            if not has_pending:
                cursor.execute(
                    "ALTER TABLE grading_records MODIFY COLUMN "
                    "status ENUM('pending', 'success', 'fail', 'error', 'skipped') DEFAULT 'success'"
                )


def init_database(db):
    """初始化数据库表结构"""
    with db.connection() as conn:
        with conn.cursor() as cursor:
            for ddl in DDL_STATEMENTS:
                cursor.execute(ddl)
    migrate_grading_records(db)
