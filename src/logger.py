# -*- coding: utf-8 -*-

import logging
import logging.config
import yaml
import os


_log_format = f"%(asctime)s %(name)s (%(threadName)s) [%(levelname)s] %(filename)s(%(lineno)d): %(message)s"


def _get_config(config) -> dict:
    with open(config, 'r') as c:
        try:
            cfg = yaml.safe_load(c)
        except yaml.YAMLError:
            print('Bad config')
        else:
            return cfg.get('logging')


def get_logger(name):
    """

    :param name:
    :return:
    TODO: add docstring
    TODO: add check to logger configuration
    TODO: remove sensitive data from logs
    """
    config_file = os.getenv('STARLINE_CONFIG_FILE', 'config/config.yaml')
    cfg = _get_config(config_file)
    cfg['formatters'] = {'simple': {'format': _log_format}}
    cfg['handlers']['console']['formatter'] = 'simple'
    cfg['handlers']['console']['stream'] = 'ext://sys.stdout'
    cfg['handlers']['console']['class'] = 'logging.StreamHandler'
    cfg['handlers']['file']['formatter'] = 'simple'
    cfg['handlers']['file']['class'] = 'logging.handlers.RotatingFileHandler'
    cfg['loggers'] = {'': {'level': 'NOTSET', 'handlers': ['console', 'file']},
                      'src.StarLine': {'level': 'NOTSET'},
                      'src.JsonStore': {'level': 'NOTSET'},
                      'src.logger': {'level': 'NOTSET'}
                      }
    cfg['version'] = 1

    logging.config.dictConfig(cfg)
    logger = logging.getLogger(name)

    return logger
