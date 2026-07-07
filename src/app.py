"""Flask 应用与路由"""
import json
import os
import re
import threading
import webbrowser
from functools import wraps
from pathlib import Path
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

from src.db.database import Database
from src.db.schema import init_database
from src.db.repositories import GradingRepository
from src.workflow.engine import WorkflowEngine
from src.utils.logger import setup_logger

project_root = Path(__file__).parent.parent

DEFAULT_ORIGINS = [
    'http://localhost:8080',
    'http://localhost:8081',
    'http://127.0.0.1:8080',
    'http://127.0.0.1:8081',
]
SENSITIVE_KEYS = {'api_key', 'password'}
MAX_PAGE_SIZE = 500
DATE_PATTERN = re.compile(r'^\d{4}-\d{2}-\d{2}$')

app = Flask(__name__, static_folder='static/web', static_url_path='')
CORS(app, origins=DEFAULT_ORIGINS)

workflow_engine = None
repository = None
logger = None


def _mask_sensitive(obj):
    """递归遮盖敏感字段。"""
    if isinstance(obj, dict):
        return {k: '***' if k in SENSITIVE_KEYS else _mask_sensitive(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_mask_sensitive(i) for i in obj]
    return obj


def _restore_masked_secrets(new_obj, old_obj):
    """保存配置时，把前端回显为 '***' 的敏感字段用旧配置的真实值回填，避免脱敏值覆盖真实密钥。"""
    if not isinstance(new_obj, dict) or not isinstance(old_obj, dict):
        return
    for k, v in new_obj.items():
        if k in SENSITIVE_KEYS and v == '***':
            if k in old_obj:
                new_obj[k] = old_obj[k]
        elif isinstance(v, dict):
            _restore_masked_secrets(v, old_obj.get(k, {}))
        elif isinstance(v, list):
            ov = old_obj.get(k, [])
            for i, item in enumerate(v):
                if isinstance(item, dict) and i < len(ov):
                    _restore_masked_secrets(item, ov[i])


def local_only(f):
    """限制端点仅限本地访问（127.0.0.1 或 ::1）"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if request.remote_addr not in ('127.0.0.1', '::1'):
            return jsonify({'error': '该端点仅限本地访问'}), 403
        return f(*args, **kwargs)
    return decorated_function


def _validate_config(data):
    """简单的配置结构校验，拒绝明显非法的键。"""
    if not isinstance(data, dict):
        raise ValueError('配置必须是 JSON 对象')
    allowed_keys = {'automation', 'http_server', 'llm', 'llm_secondary', 'mysql', 'paths', 'region', 'window'}
    for key in data.keys():
        if key not in allowed_keys:
            raise ValueError(f'不允许的顶级配置键: {key}')
    return True


def _parse_pagination_args():
    """解析并校验分页参数。"""
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 50, type=int)
    if page < 1:
        page = 1
    if page_size < 1:
        page_size = 50
    if page_size > MAX_PAGE_SIZE:
        page_size = MAX_PAGE_SIZE
    return page, page_size


def _fmt_dt(value):
    """把 datetime/date 格式化为『年-月-日 时:分:秒』字符串，避免前端时区换算。"""
    from datetime import datetime, date
    if isinstance(value, (datetime, date)):
        return value.strftime('%Y-%m-%d %H:%M:%S')
    return value


def init_app(config):
    global workflow_engine, repository, logger

    _try_connect_db(config)

    workflow_engine = WorkflowEngine(config, logger, repository)
    return app


def _try_connect_db(config):
    """尝试连接数据库，成功则初始化 repository，失败则保持 None"""
    global repository, logger

    db_config = config.get('mysql', {})
    if not db_config or not db_config.get('host'):
        if not logger:
            logger = setup_logger(config.get('paths', {}).get('logs', './logs'))
        return

    db = Database(db_config)
    if db.test_connection():
        init_database(db)
        repository = GradingRepository(db)
        if not logger:
            logger = setup_logger(config['paths']['logs'], db)
        else:
            # 已有 logger，添加 DB handler
            from src.utils.logger import DatabaseLogHandler
            db_handler = DatabaseLogHandler(db)
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            db_handler.setFormatter(formatter)
            logger.addHandler(db_handler)
        logger.info('MySQL 连接成功')
    else:
        if not logger:
            logger = setup_logger(config.get('paths', {}).get('logs', './logs'))
        logger.warning('MySQL 连接失败，降级为文件日志模式')


import logging


@app.route('/')
def index():
    return app.send_static_file('index.html')


@app.errorhandler(404)
def spa_fallback(e):
    """SPA 路由兜底：非 API 请求返回 index.html"""
    if request.path.startswith('/api/'):
        return jsonify({'error': 'Not Found'}), 404
    return app.send_static_file('index.html')


@app.route('/api/v1')
def api_info():
    return jsonify({'name': '试卷自动批改外挂 API', 'version': '2.0.0'})


@app.route('/api/v1/workflow/start', methods=['POST'])
@local_only
def workflow_start():
    data = request.get_json() or {}
    batch_limit = data.get('batch_limit', 0)
    if not isinstance(batch_limit, int) or batch_limit < 0:
        return jsonify({'error': 'batch_limit 必须为非负整数'}), 400
    if workflow_engine.is_running:
        return jsonify({'error': '工作流已在运行中'}), 409
    threading.Thread(target=workflow_engine.start, args=(batch_limit,), daemon=True).start()
    return jsonify({'status': 'started', 'batch_limit': batch_limit})


@app.route('/api/v1/workflow/stop', methods=['POST'])
@local_only
def workflow_stop():
    workflow_engine.stop()
    return jsonify({'status': 'stopped'})


@app.route('/api/v1/workflow/pause', methods=['POST'])
@local_only
def workflow_pause():
    workflow_engine.pause()
    return jsonify({'status': 'paused'})


@app.route('/api/v1/workflow/resume', methods=['POST'])
@local_only
def workflow_resume():
    workflow_engine.resume()
    return jsonify({'status': 'resumed'})


@app.route('/api/v1/workflow/status', methods=['GET'])
def workflow_status():
    return jsonify(workflow_engine.get_status())


@app.route('/api/v1/config', methods=['GET', 'POST'])
@local_only
def config_api():
    config_path = project_root / 'config' / 'config.json'
    if request.method == 'GET':
        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
        return jsonify(_mask_sensitive(config_data))
    else:
        new_config = request.get_json()
        try:
            _validate_config(new_config)
        except ValueError as ve:
            return jsonify({'error': str(ve)}), 400
        # 回填被前端回显为 '***' 的敏感字段（api_key/password），避免脱敏值覆盖真实密钥
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                old_config = json.load(f)
        except Exception:
            old_config = {}
        _restore_masked_secrets(new_config, old_config)
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(new_config, f, ensure_ascii=False, indent=2)
        if logger:
            logger.info(f'配置已更新: llm.model={new_config.get("llm", {}).get("model")}, '
                        f'region.capture={new_config.get("region", {}).get("capture")}')
        # 保存后尝试重新连接数据库
        _try_connect_db(new_config)
        # 更新工作流引擎的配置和 repository 引用
        if workflow_engine:
            workflow_engine.config = new_config
            if repository:
                workflow_engine.repository = repository
                workflow_engine._db_available = True
        return jsonify({'status': 'saved'})


@app.route('/api/v1/workflow/config', methods=['GET', 'POST'])
@local_only
def workflow_config():
    workflow_path = project_root / 'config' / 'workflow.json'
    if request.method == 'GET':
        with open(workflow_path, 'r', encoding='utf-8') as f:
            return jsonify(json.load(f))
    else:
        new_workflow = request.get_json()
        if not isinstance(new_workflow, dict) or 'workflow' not in new_workflow:
            return jsonify({'error': '工作流配置必须是包含 "workflow" 键的 JSON 对象'}), 400
        with open(workflow_path, 'w', encoding='utf-8') as f:
            json.dump(new_workflow, f, ensure_ascii=False, indent=2)
        if logger:
            steps = new_workflow.get('workflow', {}).get('steps', [])
            enabled = [s['id'] for s in steps if s.get('enabled')]
            logger.info(f'工作流配置已更新: 启用步骤={enabled}')
        return jsonify({'status': 'saved'})


@app.route('/api/v1/records', methods=['GET'])
def get_records():
    if not repository:
        return jsonify({'data': [], 'error': '数据库未连接'}), 503
    batch_id = request.args.get('batch_id', type=int)
    page, page_size = _parse_pagination_args()
    consistent_arg = request.args.get('consistent')
    consistent = int(consistent_arg) if consistent_arg in ('0', '1') else None
    total, records = repository.get_records(batch_id, page, page_size, consistent=consistent)
    for r in records:
        r['created_at'] = _fmt_dt(r.get('created_at'))
    return jsonify({'data': records, 'total': total})


@app.route('/api/v1/statistics', methods=['GET'])
def get_statistics():
    if not repository:
        return jsonify({'data': [], 'error': '数据库未连接'}), 503
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')
    if start_date and not DATE_PATTERN.match(start_date):
        return jsonify({'error': 'start_date 格式必须为 YYYY-MM-DD'}), 400
    if end_date and not DATE_PATTERN.match(end_date):
        return jsonify({'error': 'end_date 格式必须为 YYYY-MM-DD'}), 400
    stats = repository.get_statistics(start_date, end_date)
    return jsonify({'data': stats})


@app.route('/api/v1/screenshots/<path:filename>')
def serve_screenshot(filename):
    screenshots_dir = workflow_engine.config.get('paths', {}).get('screenshots', './screenshots')
    return send_from_directory(str(screenshots_dir), filename)


@app.route('/api/v1/calibration/screenshot', methods=['POST'])
def calibration_screenshot():
    if request.remote_addr not in ('127.0.0.1', '::1'):
        return jsonify({'error': '该校准端点仅限本地访问'}), 403
    from src.core.screen_capture import ScreenCapture
    capture = ScreenCapture(workflow_engine.config)
    path, _ = capture.capture_full_screen()
    filename = os.path.basename(path)
    return jsonify({'filename': filename, 'url': '/api/v1/screenshots/' + filename})


@app.route('/api/v1/calibration/move-mouse', methods=['POST'])
@local_only
def calibration_move_mouse():
    """模拟点击：移动鼠标到指定坐标（校准辅助，始终真实移动）"""
    import pyautogui
    data = request.get_json() or {}
    x = data.get('x')
    y = data.get('y')
    if x is None or y is None:
        return jsonify({'success': False, 'error': '缺少 x 或 y 参数'}), 400
    try:
        x_int = int(x)
        y_int = int(y)
    except (ValueError, TypeError):
        return jsonify({'success': False, 'error': '坐标必须是整数'}), 400
    screen_width, screen_height = pyautogui.size()
    if not (0 <= x_int <= screen_width and 0 <= y_int <= screen_height):
        return jsonify({
            'success': False,
            'error': f'坐标超出屏幕范围 (0,0)~({screen_width},{screen_height})'
        }), 400
    try:
        pyautogui.moveTo(x_int, y_int, duration=0.3)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})
    return jsonify({'success': True})


INTERNAL_ERROR_MSG = '服务器内部错误，请稍后重试'


@app.route('/api/v1/llm/test', methods=['POST'])
@local_only
def test_llm():
    data = request.get_json() or {}
    provider = data.get('provider', 'dashscope')
    api_key = data.get('api_key', '')
    model = data.get('model', '')
    try:
        from src.llm import create_llm_client
        client = create_llm_client({
            'provider': provider,
            'api_key': api_key,
            'model': model,
            'base_url': data.get('base_url', ''),
            'timeout': 10,
            'max_retries': 0
        })
        return jsonify({'success': True, 'message': f'{provider} 客户端创建成功'})
    except Exception as e:
        if logger:
            logger.warning(f'LLM 测试失败: {e}')
        return jsonify({'success': False, 'message': INTERNAL_ERROR_MSG}), 500


MAX_IMAGE_SIZE = 10 * 1024 * 1024
ALLOWED_IMAGE_EXTS = {'.png', '.jpg', '.jpeg', '.gif', '.webp'}


@app.route('/api/v1/llm/evaluate', methods=['POST'])
@local_only
def llm_evaluate():
    """使用临时配置对上传的图片进行 LLM 识别测试"""
    import tempfile
    import imghdr

    if 'image' not in request.files:
        return jsonify({'success': False, 'error': '未上传图片'}), 400

    image_file = request.files['image']
    config_str = request.form.get('config', '{}')
    prompt = request.form.get('prompt', '')

    # 文件大小检查
    image_file.seek(0, os.SEEK_END)
    file_size = image_file.tell()
    image_file.seek(0)
    if file_size > MAX_IMAGE_SIZE:
        return jsonify({'success': False, 'error': f'图片大小超过限制 (最大 {MAX_IMAGE_SIZE // 1024 // 1024}MB)'}), 413

    # 扩展名校验
    _, ext = os.path.splitext(image_file.filename or '')
    if ext.lower() not in ALLOWED_IMAGE_EXTS:
        return jsonify({'success': False, 'error': '不支持的图片格式，请上传 PNG/JPG/GIF/WebP'}), 400

    try:
        temp_config = json.loads(config_str)
    except json.JSONDecodeError:
        return jsonify({'success': False, 'error': '配置格式错误'}), 400

    if not temp_config.get('api_key'):
        return jsonify({'success': False, 'error': 'API Key 不能为空'}), 400
    if not prompt:
        return jsonify({'success': False, 'error': '提示词不能为空'}), 400

    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=ext.lower() or '.png', delete=False) as tmp:
            image_file.save(tmp)
            tmp_path = tmp.name

        from src.llm import create_llm_client
        import time
        client = create_llm_client({
            'provider': temp_config.get('provider', 'dashscope'),
            'api_key': temp_config.get('api_key', ''),
            'model': temp_config.get('model', ''),
            'base_url': temp_config.get('base_url', ''),
            'timeout': temp_config.get('timeout', 60),
            'max_retries': 0
        })
        start_time = time.time()
        result = client.evaluate(tmp_path, prompt)
        duration_ms = int((time.time() - start_time) * 1000)

        try:
            if repository:
                from src.db.repositories import VlmCallLogRepository
                vlm_repo = VlmCallLogRepository(repository.db)
                vlm_repo.insert(
                    record_id=None,
                    provider=temp_config.get('provider', ''),
                    model=temp_config.get('model', ''),
                    base_url=temp_config.get('base_url', ''),
                    prompt=prompt,
                    image_path=tmp_path,
                    raw_response=result.get('raw_response', ''),
                    score=result.get('score', 0),
                    duration_ms=duration_ms,
                    status='success' if result.get('success') else 'fail',
                    error_message=result.get('error')
                )
        except Exception as log_err:
            if logger:
                logger.warning(f'模型识别测试日志写入失败: {log_err}')

        return jsonify(result)
    except Exception as e:
        if logger:
            logger.error(f'LLM 评分失败: {e}')
        return jsonify({'success': False, 'error': INTERNAL_ERROR_MSG}), 500
    finally:
        if tmp_path:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass


@app.route('/api/v1/vlm-logs', methods=['GET'])
def get_vlm_logs():
    if not repository:
        return jsonify({'data': [], 'total': 0, 'error': '数据库未连接'}), 503
    from src.db.repositories import VlmCallLogRepository
    page, page_size = _parse_pagination_args()
    record_id = request.args.get('record_id', type=int)
    vlm_repo = VlmCallLogRepository(repository.db)
    total, logs = vlm_repo.get_logs(page, page_size, record_id)
    return jsonify({'data': logs, 'total': total})


@app.route('/api/v1/services/status', methods=['GET'])
def services_status():
    """查询各服务状态"""
    return jsonify({
        'backend': 'running',
        'mysql': 'connected' if repository else 'disconnected',
        'llm_configured': bool(app.config.get('LLM_CONFIGURED', False))
    })


@app.route('/api/v1/health', methods=['GET'])
def health_check():
    """健康检查端点"""
    health = {
        'status': 'healthy',
        'mysql': 'connected' if repository else 'disconnected',
    }
    if repository:
        try:
            with repository.db.connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute('SELECT 1')
        except Exception:
            health['mysql'] = 'error'
            health['status'] = 'degraded'
    return jsonify(health)


# 兼容旧 API
@app.route('/api/v1/correction/start', methods=['POST'])
def correction_start():
    return workflow_start()


@app.route('/api/v1/correction/stop', methods=['POST'])
def correction_stop():
    return workflow_stop()


@app.route('/api/v1/correction/pause', methods=['POST'])
def correction_pause():
    return workflow_pause()


@app.route('/api/v1/correction/resume', methods=['POST'])
def correction_resume():
    return workflow_resume()


@app.route('/api/v1/correction/status', methods=['GET'])
def correction_status():
    return workflow_status()


@app.route('/api/v1/correction/logs', methods=['GET'])
def correction_logs():
    """兼容旧前端的日志接口，映射到 records 接口"""
    if not repository:
        return jsonify({'success': True, 'data': [], 'total': 0})
    page, page_size = _parse_pagination_args()
    consistent_arg = request.args.get('consistent')
    consistent = int(consistent_arg) if consistent_arg in ('0', '1') else None
    total, records = repository.get_records(None, page, page_size, consistent=consistent)
    logs = []
    for r in records:
        logs.append({
            'time': _fmt_dt(r.get('created_at', '')),
            'screenshot': r.get('screenshot_path', ''),
            'screenshot_human': r.get('screenshot_human_path', ''),
            'score': r.get('score'),
            'score_secondary': r.get('score_secondary'),
            'status': '成功' if r.get('status') == 'success' else '失败' if r.get('status') == 'fail' else '异常',
            'detail': r.get('error_message', ''),
            'vlm_response': r.get('vlm_response', ''),
            'vlm_response_secondary': r.get('vlm_response_secondary', ''),
            'vlm_model': r.get('vlm_model', ''),
            'vlm_model_secondary': r.get('vlm_model_secondary', ''),
            'grading_mode': r.get('grading_mode', 'single'),
            'score_consistent': r.get('score_consistent'),
        })
    return jsonify({'success': True, 'data': logs, 'total': total})
