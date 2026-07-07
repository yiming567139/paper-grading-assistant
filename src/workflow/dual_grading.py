"""双评卷启用判定（step 与 engine 共用）"""


def is_dual_enabled(config: dict) -> bool:
    """副模型配置存在、未显式关闭、且 api_key 与 model 均非空时启用双评"""
    sec = config.get('llm_secondary') or {}
    if not sec.get('enabled', True):
        return False
    return bool(sec.get('api_key') and sec.get('model'))
