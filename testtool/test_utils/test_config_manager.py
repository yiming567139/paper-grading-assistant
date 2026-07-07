"""测试 ConfigManager 配置管理器"""
import json
from src.utils.config_manager import ConfigManager


def test_load_config(temp_config_file, sample_config):
    """测试加载配置文件"""
    cm = ConfigManager(temp_config_file)
    assert cm.config['llm']['provider'] == sample_config['llm']['provider']
    assert cm.config['llm']['api_key'] == sample_config['llm']['api_key']


def test_save_config(temp_config_file):
    """测试保存配置文件"""
    cm = ConfigManager(temp_config_file)
    cm.set('test_key', 'test_value')
    cm.save()

    with open(temp_config_file, 'r', encoding='utf-8') as f:
        saved = json.load(f)
    assert saved['test_key'] == 'test_value'


def test_get_nested_value(temp_config_file, sample_config):
    """测试获取嵌套配置值"""
    cm = ConfigManager(temp_config_file)
    assert cm.get('llm.provider') == sample_config['llm']['provider']
    assert cm.get('llm.model') == sample_config['llm']['model']
    assert cm.get('llm.nonexistent', 'default') == 'default'


def test_get_top_level_value(temp_config_file, sample_config):
    """测试获取顶层配置值"""
    cm = ConfigManager(temp_config_file)
    assert cm.get('automation') == sample_config['automation']


def test_set_nested_value(temp_config_file):
    """测试设置嵌套配置值"""
    cm = ConfigManager(temp_config_file)
    cm.set('llm.new_field', 'new_value')
    assert cm.get('llm.new_field') == 'new_value'


def test_set_creates_missing_keys(temp_config_file):
    """测试 set 自动创建中间缺失的键"""
    cm = ConfigManager(temp_config_file)
    cm.set('a.b.c', 'deep_value')
    assert cm.get('a.b.c') == 'deep_value'


def test_save_config_alias(temp_config_file):
    """测试 save_config 别名方法"""
    cm = ConfigManager(temp_config_file)
    cm.set('alias_test', 123)
    cm.save_config()

    with open(temp_config_file, 'r', encoding='utf-8') as f:
        saved = json.load(f)
    assert saved['alias_test'] == 123
