# -*- coding: utf-8 -*-

from src.JsonStore import JsonStore
import unittest
import tempfile
import json
from datetime import datetime


class JsonStoreTests(unittest.TestCase):

    def setUp(self):
        self.temp_file_name = tempfile.mktemp()
        self.ds = JsonStore(db_file_name=self.temp_file_name)
        self.src = {
            'app_code': {'date_exp': datetime.now().timestamp(), 'code': None},
            'app_token': {'date_exp': datetime.now().timestamp(), 'token': None},
            'slid_user_token': {'date_exp': datetime.now().timestamp(), 'token': None},
            'slnet_token': {'date_exp': datetime.now().timestamp(), 'token': None, 'user_id': None}
        }

    def test_init(self):
        self.ds.db_init
        with open(self.temp_file_name, 'r') as f:
            dst = json.load(f)
            for key, value in self.src.items():
                with self.subTest(case=key):
                    self.assertIn(key, dst)
                    self.assertIsInstance(dst[key], dict)

    def test_insert(self):
        src = {'key1': {'key1': 'value1', 'key2': 'value2'}}
        self.ds.db_insert(key='key1', value={'key1': 'value1', 'key2': 'value2'})
        with open(self.temp_file_name, 'r') as f:
            dst = json.load(f)
            self.assertIn('key1', dst)

    def test_update(self):
        src = {'app_code': {'date_exp': 'value1', 'code': 'value2'}}
        self.ds.db_update(key='app_code', value={'date_exp': 'value1', 'code': 'value2'})
        with open(self.temp_file_name, 'r') as f:
            dst = json.load(f)
            self.assertEqual(dst['app_code'], src['app_code'])

    def test_get_value(self):
        src = {'key1': 'value1', 'key2': 'value2', 'key3': 'value3'}
        with open(self.temp_file_name, 'w') as f:
            f.write(json.dumps(src))
        self.ds.db_init
        for k, v in src.items():
            with self.subTest(case=k):
                self.assertEqual(self.ds.db_get_value(k), v)


