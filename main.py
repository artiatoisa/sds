# -*- coding: utf-8 -*-

import yaml
import os
from src.StarLine import StarLine
from src.JsonStore import JsonStore
from src import logger


log = logger.get_logger(__name__)


def _read_env():
    env = {
        'app_id': os.getenv('STARLINE_APP_ID', None),
        'secret': os.getenv('STARLINE_SECRET', None),
        'login': os.getenv('STARLINE_LOGIN', None),
        'password': os.getenv('STARLINE_PASSWORD', None),
        'update_data': os.getenv('STARLINE_UPDATE', None),
        'metric_port': os.getenv('STARLINE_METRIC_PORT', None),
    }

    return env


def _get_config(config) -> dict:
    '''

    :param config:
    :return:
    TODO: Add doc string
    TODO: Add default config
    '''
    log.debug('Try to read configuration file: {}'.format(config))
    with open(config, 'r') as c:
        try:
            log.debug('Try to parse yaml')
            cfg = yaml.safe_load(c)
        except yaml.YAMLError as err:
            log.error('Error parse yaml: {}'.format(err))
        else:
            if cfg.pop('datastore') == 'JsonStore':
                cfg['datastore'] = JsonStore().db_init
            log.debug('Configuration read successful')
            cfg.pop('logging')
            for k, value in _read_env().items():
                if value:
                    if k in ('app_id', 'update_data', 'metric_port'):
                        value = int(value)
                    cfg[k] = value
            return cfg


if __name__ == '__main__':
    log = logger.get_logger(__name__)
    log.info('Starting application...')
    config_file = os.getenv('STARLINE_CONFIG_FILE', 'config/config.yaml')
    starline = StarLine(**_get_config(config_file))
    starline.monitoring_run()
