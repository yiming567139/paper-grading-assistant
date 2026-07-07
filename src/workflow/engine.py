"""工作流引擎"""
import threading
import time
import uuid
from datetime import datetime
from src.workflow.steps import create_step
from src.workflow.context import StepContext


class WorkflowEngine:
    """配置驱动的工作流引擎"""

    MAX_CONSECUTIVE_FAILURES = 10

    def __init__(self, config, logger, repository=None):
        self.config = config
        self.logger = logger
        self.repository = repository
        self._stop_event = threading.Event()
        self._stop_event.set()
        self._pause_event = threading.Event()
        self.current_step = ''
        self.batch_id = None
        self.on_step_changed = None
        self.on_progress = None
        self._db_available = repository is not None
        self._lock = threading.Lock()
        self.batch_limit: int = 0
        self.completed_count: int = 0
        self._running = False

    def load_workflow(self, workflow_config: dict = None):
        if workflow_config is None:
            import json
            from pathlib import Path
            workflow_path = Path(__file__).parent.parent.parent / 'config' / 'workflow.json'
            with open(workflow_path, 'r', encoding='utf-8') as f:
                workflow_config = json.load(f)
        self.workflow = workflow_config.get('workflow', {})
        self.steps_config = self.workflow.get('steps', [])

    def start(self, batch_limit: int = 0) -> None:
        with self._lock:
            if self._running:
                self.logger.warning('工作流已在运行中，忽略重复启动请求')
                return
            if batch_limit < 0:
                self.logger.error('batch_limit 不能为负数')
                return
            self.batch_limit = batch_limit
            self.completed_count = 0
            self._running = True
            self._stop_event.clear()
            self._pause_event.clear()

        self.load_workflow()

        if self._db_available:
            self.batch_id = self.repository.create_batch(batch_limit)
        else:
            self.batch_id = None
            self.logger.warning('数据库不可用，批改记录将不会持久化')

        self.logger.info(f'开始工作流，批次: {self.batch_id}, 限制: {batch_limit}')

        count = 0
        success_count = 0
        fail_count = 0

        while not self._stop_event.is_set():
            if self._pause_event.is_set():
                time.sleep(0.5)
                continue

            if self.batch_limit > 0 and count >= self.batch_limit:
                break

            task_id = f"task_{datetime.now().strftime('%H%M%S')}_{uuid.uuid4().hex[:6]}"
            context = StepContext(config=self.config)

            try:
                record_id = None
                if self._db_available:
                    record_id = self.repository.create_record(self.batch_id, task_id, '')

                self._execute_workflow(context, record_id, task_id)

                if context.get('score') is not None:
                    success_count += 1

            except Exception as e:
                self.logger.error(f'工作流执行异常: {e}')
                fail_count += 1
                if fail_count >= self.MAX_CONSECUTIVE_FAILURES:
                    self.logger.error(f'连续失败 {self.MAX_CONSECUTIVE_FAILURES} 次，自动停止工作流')
                    self._stop_event.set()
                    break
                error_str = str(e).lower()
                if any(k in error_str for k in ('database', 'connection', 'mysql', 'pymysql')):
                    self.logger.error('检测到数据库连接异常，自动停止工作流')
                    self._stop_event.set()
                    break
            finally:
                with self._lock:
                    count += 1
                    self.completed_count += 1
                if self.on_progress:
                    self.on_progress(
                        self.completed_count,
                        self.batch_limit,
                        self.batch_limit - self.completed_count if self.batch_limit > 0 else 0
                    )

        with self._lock:
            self._running = False
        status = 'completed' if not self.is_running else 'stopped'
        if self._db_available and self.batch_id:
            self.repository.finish_batch(self.batch_id, status, count, success_count, fail_count)
        self._stop_event.set()
        self.current_step = ''
        self.logger.info('工作流结束')

    def _execute_workflow(self, context: StepContext, record_id: int, task_id: str):
        screenshot_path = ''
        score = None
        vlm_response = ''
        vlm_model = ''
        total_duration = 0
        active_branch = None

        for step_config in self.steps_config:
            if self._stop_event.is_set():
                break

            if not step_config.get('enabled', True):
                self.logger.debug(f'步骤 {step_config["id"]} 已禁用，跳过')
                continue

            step_id = step_config['id']
            step_type = step_config['type']
            params = step_config.get('params', {})

            if active_branch is not None:
                if step_id in active_branch:
                    active_branch.discard(step_id)
                    if not active_branch:
                        active_branch = None
                else:
                    continue

            self.current_step = step_id
            self.logger.info(f'步骤开始: {step_id} ({step_type})')
            if self.on_step_changed:
                self.on_step_changed(step_id)

            # 步骤前置等待
            delay = step_config.get('delay', 0)
            if delay > 0:
                self.logger.info(f'步骤 {step_id} 等待 {delay} 秒')
                time.sleep(delay)

            if step_type == 'ConditionStep':
                step = create_step(step_id, step_type, params)
                result = step.evaluate(context)
                branch = 'then_steps' if result else 'else_steps'
                active_branch = set(params.get(branch, []))
                self.logger.info(f'条件分支 {step_id}: {branch}={active_branch}')
                continue

            step = create_step(step_id, step_type, params)
            start_time = time.time()

            try:
                result = step.execute(context)
                duration_ms = int((time.time() - start_time) * 1000)
                total_duration += duration_ms

                if step_id == 'screenshot':
                    screenshot_path = context.get('screenshot_path', '')
                    if self._db_available and record_id and screenshot_path:
                        self.repository.update_screenshot_path(record_id, screenshot_path)
                    human_path = context.get('screenshot_human_path', '')
                    if self._db_available and record_id and human_path:
                        self.repository.update_human_screenshot_path(record_id, human_path)

                if self._db_available and record_id:
                    step_status = 'success' if result.success else 'fail'
                    step_error = result.error if not result.success else None
                    self.repository.insert_step_execution(
                        record_id, step_id, step_type, step_status, duration_ms, step_error
                    )

                # VLM 评分步骤：写入调用日志
                if step_id == 'evaluate' and self._db_available and record_id:
                    self._log_vlm_call(record_id, context, result, duration_ms)

                self.logger.info(f'步骤完成: {step_id}, 耗时={duration_ms}ms')

                if not result.success:
                    self.logger.error(f'步骤 {step_id} 失败: {result.error}, 耗时={duration_ms}ms')
                    if self._db_available and record_id:
                        self.repository.finish_record(
                            record_id, score, 'fail', result.error, vlm_response, vlm_model, total_duration,
                            context.get('score_secondary'), context.get('vlm_response_secondary'),
                            context.get('vlm_model_secondary'), context.get('grading_mode', 'single'),
                            context.get('score_consistent')
                        )
                    return

            except Exception as e:
                duration_ms = int((time.time() - start_time) * 1000)
                self.logger.error(f'步骤 {step_id} 异常: {e}')
                if self._db_available and record_id:
                    self.repository.insert_step_execution(
                        record_id, step_id, step_type, 'fail', duration_ms, str(e)
                    )
                    self.repository.finish_record(
                        record_id, score, 'error', str(e), vlm_response, vlm_model, total_duration,
                        context.get('score_secondary'), context.get('vlm_response_secondary'),
                        context.get('vlm_model_secondary'), context.get('grading_mode', 'single'),
                        context.get('score_consistent')
                    )
                return

        score = context.get('score')
        vlm_response = context.get('vlm_response', '')
        vlm_model = context.get('vlm_model', '')

        self.logger.info(f'任务 {task_id} 完成: score={score}, 总耗时={total_duration}ms')

        if self._db_available and record_id:
            self.repository.finish_record(
                record_id, score, 'success', '', vlm_response, vlm_model, total_duration,
                context.get('score_secondary'), context.get('vlm_response_secondary'),
                context.get('vlm_model_secondary'), context.get('grading_mode', 'single'),
                context.get('score_consistent')
            )

    def _log_vlm_call(self, record_id, context, result, duration_ms):
        """写入 VLM 调用日志：主模型一条，双评时副模型再一条"""
        from src.db.repositories import VlmCallLogRepository
        cfg = context.config
        primary_cfg = cfg.get('llm', {})
        try:
            vlm_repo = VlmCallLogRepository(self.repository.db)
            vlm_repo.insert(
                record_id=record_id,
                provider=primary_cfg.get('provider', ''),
                model=primary_cfg.get('model', ''),
                base_url=primary_cfg.get('base_url', ''),
                prompt=primary_cfg.get('prompt_template', ''),
                image_path=context.get('screenshot_path', ''),
                raw_response=context.get('vlm_response', '') or '',
                score=context.get('score') or 0,
                duration_ms=duration_ms,
                status='success' if result.success else 'fail',
                error_message=result.error if not result.success else None
            )
            if context.get('grading_mode') == 'dual':
                sec_cfg = cfg.get('llm_secondary', {})
                sec_score = context.get('score_secondary')
                sec_ok = sec_score is not None
                vlm_repo.insert(
                    record_id=record_id,
                    provider=sec_cfg.get('provider', ''),
                    model=sec_cfg.get('model', ''),
                    base_url=sec_cfg.get('base_url', ''),
                    prompt=sec_cfg.get('prompt_template', primary_cfg.get('prompt_template', '')),
                    image_path=context.get('screenshot_path', ''),
                    raw_response=context.get('vlm_response_secondary', '') or '',
                    score=sec_score if sec_ok else 0,
                    duration_ms=duration_ms,
                    status='success' if sec_ok else 'fail',
                    error_message=None if sec_ok else (context.get('vlm_response_secondary', '') or '副模型失败')
                )
        except Exception as e:
            self.logger.warning(f'写入 VLM 调用日志失败: {e}')

    def stop(self):
        self._stop_event.set()
        with self._lock:
            self._running = False
        self.logger.info('正在停止工作流...')

    def pause(self):
        self._pause_event.set()
        self.logger.info('工作流已暂停')

    def resume(self):
        self._pause_event.clear()
        self.logger.info('工作流已恢复')

    @property
    def is_running(self):
        return self._running and not self._stop_event.is_set()

    @property
    def is_paused(self):
        return self._pause_event.is_set()

    def get_status(self):
        from src.workflow.dual_grading import is_dual_enabled
        with self._lock:
            dual = is_dual_enabled(self.config)
            return {
                'is_running': self._running and not self._stop_event.is_set(),
                'is_paused': self._pause_event.is_set(),
                'current_step': self.current_step,
                'batch_id': self.batch_id,
                'batch_limit': self.batch_limit,
                'completed_count': self.completed_count,
                'dual_grading': dual,
                'primary_model': self.config.get('llm', {}).get('model', ''),
                'secondary_model': self.config.get('llm_secondary', {}).get('model', '') if dual else '',
            }
