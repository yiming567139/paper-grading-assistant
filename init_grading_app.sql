-- grading_app 数据库初始化脚本
-- 由 init_db.py --export-sql 自动生成
-- 执行方式: mysql -u root -p < init_grading_app.sql

CREATE DATABASE IF NOT EXISTS `grading_app` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE `grading_app`;

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

CREATE TABLE IF NOT EXISTS grading_records (
        id INT AUTO_INCREMENT PRIMARY KEY,
        batch_id INT NOT NULL,
        task_id VARCHAR(50) NOT NULL,
        screenshot_path VARCHAR(500) COMMENT '截图完整路径',
        score INT COMMENT 'AI评分结果',
        status ENUM('success', 'fail', 'error', 'skipped') DEFAULT 'success',
        error_message TEXT,
        vlm_response TEXT COMMENT '大模型原始返回',
        vlm_model VARCHAR(100) COMMENT '使用的模型',
        duration_ms INT COMMENT '单次批改耗时',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (batch_id) REFERENCES grading_batches(id),
        INDEX idx_batch_id (batch_id),
        INDEX idx_created_at (created_at)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS step_executions (
        id INT AUTO_INCREMENT PRIMARY KEY,
        record_id INT NOT NULL,
        step_id VARCHAR(50) NOT NULL COMMENT '如 screenshot, vlm_eval',
        step_type VARCHAR(50) NOT NULL,
        status ENUM('start', 'success', 'fail') DEFAULT 'start',
        duration_ms INT,
        error_message TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (record_id) REFERENCES grading_records(id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

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

CREATE TABLE IF NOT EXISTS system_logs (
        id BIGINT AUTO_INCREMENT PRIMARY KEY,
        level ENUM('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL') DEFAULT 'INFO',
        module VARCHAR(100) COMMENT '来源模块',
        message TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        INDEX idx_created_at (created_at),
        INDEX idx_level (level)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
