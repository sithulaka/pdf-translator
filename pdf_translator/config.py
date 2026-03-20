import os
import yaml
import logging

logger = logging.getLogger(__name__)

DEFAULTS = {
    'target_language': 'si',
    'input_folder': 'input_pdfs',
    'output_folder': 'output_texts',
    'output_format': 'txt',
    'engine': 'google',
    'max_workers': 3,
    'bilingual': False,
}


def load_config(config_path=None):
    config = dict(DEFAULTS)
    if config_path and os.path.exists(config_path):
        with open(config_path, 'r') as f:
            file_config = yaml.safe_load(f) or {}
        config.update(file_config)
        logger.debug("Loaded config from %s", config_path)
    elif config_path:
        logger.warning("Config file not found: %s, using defaults", config_path)
    return config
