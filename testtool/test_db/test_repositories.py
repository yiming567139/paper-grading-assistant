"""测试 GradingRepository 数据操作方法"""


def test_create_batch(mock_repository, mock_db):
    """测试 create_batch 插入批次"""
    mock_repository.create_batch(10)

    conn = mock_db.connection().__enter__()
    cursor = conn.cursor()
    cursor.execute.assert_called_once()
    args = cursor.execute.call_args[0][1]
    assert args[0] == 10


def test_finish_batch(mock_repository, mock_db):
    """测试 finish_batch 更新批次状态"""
    mock_repository.finish_batch(1, 'completed', 5, 4, 1)

    conn = mock_db.connection().__enter__()
    cursor = conn.cursor()
    cursor.execute.assert_called_once()
    args = cursor.execute.call_args[0][1]
    assert args == ('completed', 5, 4, 1, 1)


def test_create_record(mock_repository, mock_db):
    """测试 create_record 插入记录，初始状态为 pending"""
    record_id = mock_repository.create_record(1, 'task_001', '/tmp/test.png')
    assert record_id == 1

    conn = mock_db.connection().__enter__()
    cursor = conn.cursor()
    cursor.execute.assert_called_once()
    args = cursor.execute.call_args[0][1]
    assert args == (1, 'task_001', '/tmp/test.png')
    sql = cursor.execute.call_args[0][0]
    assert "'pending'" in sql


def test_get_records_excludes_pending(mock_repository, mock_db):
    """get_records 默认过滤掉 pending 状态的记录"""
    mock_cursor = mock_db.connection().__enter__().cursor()
    mock_cursor.fetchone.return_value = {'total': 0}
    mock_cursor.fetchall.return_value = []
    mock_repository.get_records(batch_id=None, page=1, page_size=10)
    sql_calls = [c.args[0] for c in mock_cursor.execute.call_args_list]
    assert any("status != 'pending'" in s for s in sql_calls)


def test_finish_record(mock_repository, mock_db):
    """测试 finish_record 更新记录（含双评字段）"""
    mock_repository.finish_record(
        1, 5, 'success', '', '5', 'qwen-vl', 1200,
        score_secondary=4, vlm_response_secondary='4', vlm_model_secondary='deepseek-vl',
        grading_mode='dual', score_consistent=0
    )
    conn = mock_db.connection().__enter__()
    cursor = conn.cursor()
    cursor.execute.assert_called_once()
    args = cursor.execute.call_args[0][1]
    assert args == (5, 'success', '', '5', 'qwen-vl', 1200,
                    4, '4', 'deepseek-vl', 'dual', 0, 1)


def test_finish_record_defaults_single(mock_repository, mock_db):
    """不传双评参数时默认单评、副字段为空"""
    mock_repository.finish_record(1, 5, 'success', '', '5', 'qwen-vl', 1200)
    conn = mock_db.connection().__enter__()
    cursor = conn.cursor()
    args = cursor.execute.call_args[0][1]
    assert args == (5, 'success', '', '5', 'qwen-vl', 1200,
                    None, None, None, 'single', None, 1)


def test_update_human_screenshot_path(mock_repository, mock_db):
    """测试写入人看截图路径"""
    mock_repository.update_human_screenshot_path(1, '/tmp/human.png')
    conn = mock_db.connection().__enter__()
    cursor = conn.cursor()
    args = cursor.execute.call_args[0][1]
    assert args == ('/tmp/human.png', 1)


def test_get_records_with_consistent_filter(mock_repository, mock_db):
    """consistent=0 时应带一致性过滤条件"""
    mock_cursor = mock_db.connection().__enter__().cursor()
    mock_cursor.fetchone.return_value = {'total': 0}
    mock_cursor.fetchall.return_value = []
    mock_repository.get_records(batch_id=None, page=1, page_size=10, consistent=0)
    sql_calls = [c.args[0] for c in mock_cursor.execute.call_args_list]
    assert any('score_consistent' in s for s in sql_calls)


def test_get_records_with_batch_id(mock_repository, mock_db):
    """测试 get_records 按批次查询"""
    mock_cursor = mock_db.connection().__enter__().cursor()
    mock_cursor.fetchall.return_value = [
        {'id': 1, 'batch_id': 2, 'task_id': 'task_001'}
    ]

    total, records = mock_repository.get_records(batch_id=2, page=1, page_size=10)
    assert len(records) == 1
    assert records[0]['batch_id'] == 2


def test_get_statistics(mock_repository, mock_db):
    """测试 get_statistics 统计查询"""
    mock_cursor = mock_db.connection().__enter__().cursor()
    mock_cursor.fetchall.return_value = [
        {'date': '2026-05-28', 'total': 10, 'success': 8}
    ]

    stats = mock_repository.get_statistics('2026-05-01', '2026-05-31')
    assert len(stats) == 1
    assert stats[0]['total'] == 10
    assert stats[0]['success'] == 8
