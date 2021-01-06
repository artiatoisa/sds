# -*- coding: utf-8 -*-

import json
from datetime import datetime
import sys
from src.StoreDriver import StoreDriver
from src import logger

log = logger.get_logger(__name__)


class JsonStore(StoreDriver):

    def __init__(self, db_file_name: str = 'datastore.json', **kwargs):
        log.debug('Initialising JSON store for keys and tokens...')
        super().__init__(db_file_name)
        self._json_store = {
            'app_code': {'date_exp': datetime.now().timestamp(), 'code': None},
            'app_token': {'date_exp': datetime.now().timestamp(), 'token': None},
            'slid_user_token': {'date_exp': datetime.now().timestamp(), 'token': None},
            'slnet_token': {'date_exp': datetime.now().timestamp(), 'token': None, 'user_id': None}
        }

    def _file(self, mode: str='r'):
        with open(self._db_file_name, mode) as f:
            if mode == 'r':
                try:
                    self._json_store = json.load(f)
                except:
                    log.error('Error while loading JSON store. Case: {}'.format(sys.exc_info()[0]))
            if mode == 'w':
                f.write(json.dumps(self._json_store))

    @property
    def db_init(self):
        try:
            self._file('r')
            log.info('Found exist JSON store. It will be reusing.')
        except FileNotFoundError:
            log.info('Will be creating new JSON store...')
            self._file('w')
        log.info('JSON store was initialising.')
        return self

    def db_insert(self, key: str, value: dict) -> bool:
        try:
            log.debug('Try to insert new line with key: {}, and value: {}'.format(key, value))
            self._json_store[key] = value
            self._file('w')
        except:
            log.error('Error while inserting new line. Case: {}'.format(sys.exc_info()[0]))
        finally:
            log.debug('New line was inserted.')
            return True

    def db_update(self, key: str, value: dict) -> bool:
        try:
            log.debug('Try to update new line with key: {}, and value: {}'.format(key, value))
            self._json_store[key] = value
            self._file('w')
        except:
            log.error('Error while updating new line. Case: {}'.format(sys.exc_info()[0]))
        finally:
            log.debug('New line was updated.')
            return True

    def db_get_value(self, key: str) -> dict:
        log.debug('Retrieve value for key: {}'.format(key))
        return self._json_store[key]
