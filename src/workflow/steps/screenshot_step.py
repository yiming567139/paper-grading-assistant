"""截图步骤"""
import logging
import os
import time
from datetime import datetime
from pathlib import Path
from src.workflow.steps.base_step import BaseStep
from src.workflow.context import StepContext, StepResult, ParamDef
from src.core.screen_capture import ScreenCapture

logger = logging.getLogger('GradingApp')


class ScreenshotStep(BaseStep):
    name = '截图'
    description = '截取屏幕指定区域'

    def execute(self, context: StepContext) -> StepResult:
        config = context.config
        region_name = self.params.get('region', 'capture')
        region = config.get('region', {}).get(region_name, {})

        if not region or not all(k in region for k in ('x1', 'y1', 'x2', 'y2')):
            logger.error(f'截图区域 "{region_name}" 配置不完整: {region}')
            return StepResult(success=False, error=f'截图区域 "{region_name}" 配置不完整')

        logger.info(f'截图: region={region_name}, 坐标=({region.get("x1")},{region.get("y1")})→({region.get("x2")},{region.get("y2")})')

        capture = ScreenCapture(config)
        path, _ = capture.capture(region=region)

        file_size = os.path.getsize(path) if os.path.exists(path) else 0
        logger.info(f'截图完成: path={path}, 文件大小={file_size // 1024}KB')

        context.set('screenshot_path', path)

        # 额外截"给人看"的图（可选，仅展示，不送模型）
        human_region = config.get('region', {}).get('capture_human', {})
        if (human_region and all(k in human_region for k in ('x1', 'y1', 'x2', 'y2'))
                and human_region['x2'] > human_region['x1']
                and human_region['y2'] > human_region['y1']):
            try:
                human_path, _ = capture.capture(region=human_region)
                context.set('screenshot_human_path', human_path)
                logger.info(f'人看截图完成: path={human_path}')
            except Exception as e:
                logger.warning(f'人看截图失败: {e}')

        return StepResult(success=True, data={'screenshot_path': path})
