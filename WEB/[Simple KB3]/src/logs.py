import logging
import logging.config
import yaml
import os
from pathlib import Path


def setup_logging(
    default_path='logging_config.yaml',
    default_level=logging.INFO,
    env_key='LOG_CFG'
):
    """Настройка логирования из YAML файла."""
    path = os.getenv(env_key, default_path)
    if os.path.exists(path):
        with open(path, 'rt') as f:
            config = yaml.safe_load(f)

        # Создаем директорию для логов если её нет
        log_dir = Path('log')
        log_dir.mkdir(exist_ok=True)
        
        log_dir2 = Path('log/db')
        log_dir2.mkdir(exist_ok=True)
        

        # Применяем конфигурацию
        logging.config.dictConfig(config)
    else:
        logging.basicConfig(level=default_level)