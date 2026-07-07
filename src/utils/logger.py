"""
日志工具模块

提供三种日志记录器：
1. setup_logger: 创建应用主日志记录器，同时输出到文件和控制台
2. StepLogger: 分环节日志记录器，分别记录截图、识别、打分环节
3. GradingLogger: 批改结果记录器，以JSON格式保存批改记录

日志文件：
- grading_YYYYMMDD.log: 应用主日志
- screenshot_YYYYMMDD.log: 截图环节日志
- recognition_YYYYMMDD.log: 识别环节日志
- scoring_YYYYMMDD.log: 打分环节日志
- grading_log.json: 批改记录JSON

Author: AI助手
Version: 1.0.0
"""
import logging
import os
import json
from datetime import datetime
from pathlib import Path


def setup_logger(log_dir, db=None):
    """
    创建应用主日志记录器

    同时输出到文件(logs/grading_YYYYMMDD.log)和控制台。
    文件日志级别为DEBUG，控制台日志级别为INFO。
    如果传入 db 参数，还会将日志写入 MySQL 数据库。

    Args:
        log_dir: 日志目录路径
        db: 数据库连接对象（可选），传入时启用 MySQL 双写
    Returns:
        logging.Logger: 配置好的日志记录器
    """
    # 确保日志目录存在
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)

    # 创建日志器
    logger = logging.getLogger('GradingApp')
    logger.setLevel(logging.DEBUG)

    # 避免重复添加handler
    if logger.handlers:
        return logger

    # 日志文件名
    log_file = log_path / f"grading_{datetime.now().strftime('%Y%m%d')}.log"

    # 文件handler
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)

    # 控制台handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    # 格式化
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # 添加handler
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    # MySQL双写（可选）
    if db:
        db_handler = DatabaseLogHandler(db)
        db_handler.setFormatter(formatter)
        logger.addHandler(db_handler)

    return logger


class StepLogger:
    """分环节日志记录器"""

    # 环节枚举
    SCREENSHOT = 'screenshot'
    RECOGNITION = 'recognition'
    SCORING = 'scoring'

    def __init__(self, log_dir):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self._loggers = {}
        self._logger_dates = {}

    def _get_logger(self, step):
        """获取指定环节的日志器"""
        today = datetime.now().strftime('%Y%m%d')
        if step in self._loggers and self._logger_dates.get(step) != today:
            del self._loggers[step]

        if step in self._loggers:
            return self._loggers[step]

        logger = logging.getLogger(f'GradingApp.{step}')
        logger.setLevel(logging.DEBUG)
        logger.handlers = []

        log_file = self.log_dir / f"{step}_{today}.log"
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)

        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        self._loggers[step] = logger
        self._logger_dates[step] = today
        return logger

    def screenshot(self, message, **kwargs):
        """截图环节日志"""
        self._log(self.SCREENSHOT, message, **kwargs)

    def recognition(self, message, **kwargs):
        """识别环节日志"""
        self._log(self.RECOGNITION, message, **kwargs)

    def scoring(self, message, **kwargs):
        """打分环节日志"""
        self._log(self.SCORING, message, **kwargs)

    def _log(self, step, message, **kwargs):
        """记录日志"""
        logger = self._get_logger(step)

        # 构建日志消息
        extra_info = ' '.join([f"{k}={v}" for k, v in kwargs.items()])
        full_message = message if not extra_info else f"{message} {extra_info}"

        logger.info(full_message)

    def screenshot_start(self, task_id):
        """记录截图开始"""
        self.screenshot(f"截图开始", task_id=task_id)

    def screenshot_done(self, path, duration_ms):
        """记录截图完成"""
        self.screenshot(f"截图完成", path=path, duration_ms=duration_ms)

    def recognition_start(self, screenshot_path, task_id):
        """记录识别开始"""
        self.recognition(f"识别开始", screenshot=screenshot_path, task_id=task_id)

    def recognition_done(self, duration_ms, score=0, success=True, error=""):
        """记录识别完成"""
        if success:
            self.recognition(f"识别完成", score=score, duration_ms=duration_ms)
        else:
            self.recognition(f"识别失败", error=error, duration_ms=duration_ms)

    def scoring_start(self, score, task_id):
        """记录打分开始"""
        self.scoring(f"打分开始", score=score, task_id=task_id)

    def scoring_done(self, success=True, error=""):
        """记录打分完成"""
        if success:
            self.scoring(f"打分完成")
        else:
            self.scoring(f"打分失败", error=error)


class GradingLogger:
    """
    批改结果记录器

    将每次批改的结果以JSON格式保存到grading_log.json文件。
    日志按时间倒序返回（最新的在前）。

    Attributes:
        logger: 应用主日志记录器
        log_dir: 日志目录路径
    """

    def __init__(self, logger, log_dir):
        self.logger = logger
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()

    def log_grading(self, screenshot_path, score, status, detail="", vlm_response=""):
        """
        记录批改日志（追加写入，避免全量重写）

        Args:
            screenshot_path: 截图文件路径
            score: 评分分数
            status: 状态（成功/失败）
            detail: 详细信息
            vlm_response: VLM原始返回文本
        """
        log_entry = {
            'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'screenshot': screenshot_path,
            'score': score,
            'status': status,
            'detail': detail,
            'vlm_response': vlm_response
        }

        log_file = self.log_dir / 'grading_log.json'
        with self._lock:
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')

        self.logger.info(f"批改记录: {score}分 - {status}")

    def get_logs(self, page=1, page_size=50):
        """
        获取批改日志（分页，从文件尾部读取，按最新在前排序）

        Args:
            page: 页码，从1开始
            page_size: 每页条数，默认50条
        Returns:
            dict: 包含总条数(total)和日志列表(data)，日志按最新在前排序
        """
        log_file = self.log_dir / 'grading_log.json'

        if not log_file.exists():
            return {'total': 0, 'data': []}

        # 逐行读取，避免一次性加载整个文件到内存
        logs = []
        with open(log_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        logs.append(json.loads(line))
                    except (json.JSONDecodeError, ValueError):
                        continue

        # 按最新时间排序（反转列表）
        total = len(logs)
        reversed_logs = list(reversed(logs))

        # 计算分页
        start = (page - 1) * page_size
        end = start + page_size
        page_data = reversed_logs[start:end]

        return {'total': total, 'data': page_data}


class DatabaseLogHandler(logging.Handler):
    """将日志同时写入 MySQL"""

    def __init__(self, db):
        super().__init__()
        self.db = db
        from src.db.repositories import LogRepository
        self._repo = LogRepository(db)

    def emit(self, record):
        try:
            self._repo.insert_log(
                level=record.levelname,
                module=record.name,
                message=self.format(record)
            )
        except Exception:
            self.handleError(record)
