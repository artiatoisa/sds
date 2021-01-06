# -*- coding: utf-8 -*-

import unittest
import requests_mock
from unittest.mock import Mock
from datetime import datetime, timedelta
import os
os.environ['STARLINE_CONFIG_FILE'] = '../config/config.yaml'

from src.StarLine import StarLine
from src.StoreDriver import StoreDriver



class StarLineTests(unittest.TestCase):

    def setUp(self):
        # self.temp_file_name = tempfile.mktemp()
        # self.ds = JsonStore(db_file_name=self.temp_file_name)
        self.src = {'user_data': {'shared_devices': [], 'devices': [
            {'telephone': '+7 (983) 123-45-67', 'type': 3, 'firmware_version': '2.21.3',
             'functions': ['gsm_control', 'xml_cfg', 'shock_cfg', 'int_sensor', 'eng_sensor', 'scoring', 'rstart_cfg',
                           'gsm', 'info', 'position', 'state', 'adv_state', 'mon_cfg', 'tracking', 'push', 'events',
                           'controls', 'adv_controls', 'adv_guard', 'rstart_cfg', 'shock_cfg', 'obd_params', 'ble2'],
             'device_id': 874369789277938,
             'alarm_state': {'shock_l': False, 'add_h': False, 'ts': 1608839234, 'pbrake': False, 'tilt': False,
                             'shock_h': False, 'add_l': False, 'run': False, 'door': False, 'trunk': False,
                             'hood': False, 'hbrake': False, 'hijack': False},
             'balance': [{'operator': '', 'ts': 1608830215, 'key': 'active', 'value': 211, 'currency': '', 'state': 2}],
             'event': {'type': 1090, 'timestamp': 1608807989},
             'position': {'ts': 1608839119, 'x': 80.97399139404297, 'r': 0, 'is_move': True, 'dir': 100, 'sat_qty': 9,
                          's': 0, 'y': 51.98942184448242},
             'r_start': {'period': {'has': False}, 'cron': {'has': False}, 'battery': {'has': False},
                         'temp': {'has': False}}, 'ua_url': '', 'sn': 'A96 S906 123456',
             'obd': {'mileage': 6944, 'fuel_litres': None, 'fuel_percent': 37, 'ts': 1608808021}, 'status': 2,
             'alias': 'Qashqai', 'activity_ts': 1608839234, 'typename': 'Охранный комплекс',
             'state': {'ign': False, 'alarm': False, 'r_start_timer': 0, 'webasto_timer': 0, 'run': False,
                       'door': False, 'hbrake': False, 'trunk': False, 'valet': False, 'neutral': False, 'out': False,
                       'hfree': False, 'arm': True, 'add_sens_bpass': False, 'arm_auth_wait': False, 'pbrake': True,
                       'shock_bpass': False, 'r_start': False, 'arm_moving_pb': False, 'webasto': False,
                       'ts': 1608839234, 'hood': False, 'tilt_bpass': False, 'hijack': False},
             'common': {'etemp': -6, 'ctemp': -6, 'gps_lvl': 9, 'ts': 1608839032, 'mayak_temp': 0, 'gsm_lvl': 17,
                        'battery': 12.345000267028809, 'reg_date': 1579020289}}]}, 'codestring': 'OK', 'code': 200}
        mock_StoreDriver = Mock(spec=StoreDriver)
        mock_StoreDriver.db_get_value.return_value = {'date_exp': (datetime.now()+timedelta(hours=1)).timestamp()}
        self.starline = StarLine(
            app_id=12345,
            secret='test_secret',
            login='test_login',
            password='test_password',
            datastore=mock_StoreDriver
        )

    @requests_mock.Mocker()
    def test_get_http(self, mocker):
        with self.subTest(case='Get method'):
            src = {
                "state": 1,
                "desc": {
                    "code": "3ca3ae6d958508450b54fc6f29a48877"
                }}
            mocker.register_uri('GET', 'http://get.test.com', json=src)

            response = self.starline._get_http('http://get.test.com', method='get')
            self.assertEqual(src, response[0])
        with self.subTest(case='Post method'):
            src = {
                'code': '200',
                'codestring': 'OK',
                'realplexor_id': '52862F00D94602BE549933CCD3D483FD',
                'user_id': '1116'
            }
            mocker.register_uri('POST', 'http://post.test.com', json=src)

            response = self.starline._get_http('http://post.test.com', method='post')
            self.assertEqual(src, response[0])
        with self.subTest(case='Sate Exeption'):
            src = {
                "state": 0,
                "desc": {
                    "code": "3ca3ae6d958508450b54fc6f29a48877"
                }}
            mocker.register_uri('GET', 'http://state.test.com', json=src)
            self.assertRaises(Exception, self.starline._get_http, 'http://state.test.com', method='get')

    def test_date_exp(self):
        td = timedelta(hours=1)
        dt = self.starline._date_exp(td)
        with self.subTest(case='Time more'):
            self.assertTrue(dt > datetime.now().timestamp())
        with self.subTest(case='Time less'):
            self.assertFalse(dt < datetime.now().timestamp())

    @requests_mock.Mocker()
    def test_get_app_code(self, mocker):
        url = 'https://id.sds.ru/apiV3/application/getCode/'
        src = {
            'state': 1,
            'desc': {
                'code': '3ca3ae6d958508450b54fc6f29a48877'
            }}
        mocker.register_uri('GET', url, json=src)
        app_code = self.starline._get_app_code(12345, 'test_secret')
        self.assertEqual(src['desc']['code'], app_code['code'])

    @requests_mock.Mocker()
    def test_get_app_token(self, mocker):
        url = 'https://id.sds.ru/apiV3/application/getToken/'
        src = {
            'state': 1,
            'desc': {
                'token': 'a5c7babc3bac519753e0e93fafa94abe84c7fe19b8a94d115bb2bf28cc3bd3e6'
            }}
        mocker.register_uri('GET', url, json=src)
        app_token = self.starline._get_app_token(12345, 'test_secret', '3ca3ae6d958508450b54fc6f29a48877')
        self.assertEqual(src['desc']['token'], app_token['token'])



    @requests_mock.Mocker()
    def test_get_slid_user_token(self, mocker):
        url = 'https://id.sds.ru/apiV3/user/login/'
        src = {
            'state': 1,
            'desc': {
                'user_token': 'a5c7babc3bac519753e0e93fafa94abe84c7fe19b8a94d115bb2bf28cc3bd3e6'
            }}
        mocker.register_uri('POST', url, json=src)
        user_token = self.starline._get_slid_user_token('3ca3ae6d958508450b54fc6f29a48877', 'login', 'password')
        self.assertEqual(src['desc']['user_token'], user_token['token'])

    @requests_mock.Mocker()
    def test_get_slnet_token(self, mocker):
        url = 'https://developer.sds.ru/json/v2/auth.slid'
        src = {
            'code': '200',
            'codestring': 'OK',
            'realplexor_id': '52862F00D94602BE549933CCD3D483FD',
            'user_id': '98765'
        }
        mocker.register_uri('POST', url, json=src, cookies={'slnet': '3ca3ae6d958508450b54fc6f29a48877'})
        slnet_token = self.starline._get_slnet_token('a5c7babc3bac519753e0e93fafa94abe84c7fe19b8a94d115bb2bf28cc3bd3e6')
        self.assertEqual(src['user_id'], slnet_token['user_id'])
        self.assertEqual('3ca3ae6d958508450b54fc6f29a48877', slnet_token['token'])

    @requests_mock.Mocker()
    def test_get_user_data(self, mocker):
        url = "https://developer.sds.ru/json/v3/user/12345/data"
        mocker.register_uri('GET', url, json=self.src)
        data = self.starline._get_user_data('12345', '3ca3ae6d958508450b54fc6f29a48877')
        self.assertEqual(self.src, data)

    def test_devices(self):
        src_f = {"telephone": "+7 (983) 123-45-67", "type": 3, "firmware_version": "2.21.3", "functions.0": "gsm_control",
         "functions.1": "xml_cfg", "functions.2": "shock_cfg", "functions.3": "int_sensor", "functions.4": "eng_sensor",
         "functions.5": "scoring", "functions.6": "rstart_cfg", "functions.7": "gsm", "functions.8": "info",
         "functions.9": "position", "functions.10": "state", "functions.11": "adv_state", "functions.12": "mon_cfg",
         "functions.13": "tracking", "functions.14": "push", "functions.15": "events", "functions.16": "controls",
         "functions.17": "adv_controls", "functions.18": "adv_guard", "functions.19": "rstart_cfg",
         "functions.20": "shock_cfg", "functions.21": "obd_params", "functions.22": "ble2",
         "device_id": 874369789277938, "alarm_state.shock_l": False, "alarm_state.add_h": False,
         "alarm_state.ts": 1608839234, "alarm_state.pbrake": False, "alarm_state.tilt": False,
         "alarm_state.shock_h": False, "alarm_state.add_l": False, "alarm_state.run": False, "alarm_state.door": False,
         "alarm_state.trunk": False, "alarm_state.hood": False, "alarm_state.hbrake": False,
         "alarm_state.hijack": False, "balance.0.operator": "", "balance.0.ts": 1608830215, "balance.0.key": "active",
         "balance.0.value": 211, "balance.0.currency": "", "balance.0.state": 2, "event.type": 1090,
         "event.timestamp": 1608807989, "position.ts": 1608839119, "position.x": 80.97399139404297, "position.r": 0,
         "position.is_move": True, "position.dir": 100, "position.sat_qty": 9, "position.s": 0,
         "position.y": 51.98942184448242, "r_start.period.has": False, "r_start.cron.has": False,
         "r_start.battery.has": False, "r_start.temp.has": False, "ua_url": "", "sn": "A96 S906 123456",
         "obd.mileage": 6944, "obd.fuel_litres": None, "obd.fuel_percent": 37, "obd.ts": 1608808021, "status": 2,
         "alias": "Qashqai", "activity_ts": 1608839234,
         "typename": "\u041e\u0445\u0440\u0430\u043d\u043d\u044b\u0439 \u043a\u043e\u043c\u043f\u043b\u0435\u043a\u0441",
         "state.ign": False, "state.alarm": False, "state.r_start_timer": 0, "state.webasto_timer": 0,
         "state.run": False, "state.door": False, "state.hbrake": False, "state.trunk": False, "state.valet": False,
         "state.neutral": False, "state.out": False, "state.hfree": False, "state.arm": True,
         "state.add_sens_bpass": False, "state.arm_auth_wait": False, "state.pbrake": True, "state.shock_bpass": False,
         "state.r_start": False, "state.arm_moving_pb": False, "state.webasto": False, "state.ts": 1608839234,
         "state.hood": False, "state.tilt_bpass": False, "state.hijack": False, "common.etemp": -6, "common.ctemp": -6,
         "common.gps_lvl": 9, "common.ts": 1608839032, "common.mayak_temp": 0, "common.gsm_lvl": 17,
         "common.battery": 12.345000267028809, "common.reg_date": 1579020289}

        dev = self.starline._devices(self.src)
        self.assertIsInstance(dev, list)
        self.assertEqual(dev[0], src_f)

    @requests_mock.Mocker()
    def test_get_events(self, mocker):
        src = {
            'events': [
                {
                    'ts': 1461262503,
                    'group_id': 2,
                    'event_id': 307
                },
                {
                    'ts': 1461262503,
                    'group_id': 2,
                    'event_id': 320
                },
                {
                    'ts': 1461262503,
                    'group_id': 2,
                    'event_id': 301
                }
            ],
            'code': 200,
            'codestring': 'OK'
        }
        url = "https://developer.sds.ru/json/v1/device/356306056285332/events"
        mocker.register_uri('POST', url, json=src, cookies={'slnet': '3ca3ae6d958508450b54fc6f29a48877'})
        events = self.starline._get_events('3ca3ae6d958508450b54fc6f29a48877', '356306056285332')
        self.assertIsInstance(events, list)
        self.assertEqual(src['events'], events)

