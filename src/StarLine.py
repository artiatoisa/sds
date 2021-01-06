# -*- coding: utf-8 -*-

import requests
import hashlib
from datetime import datetime, timedelta
from time import sleep
from flatten_json import flatten
from src.StoreDriver import StoreDriver
from src import metrics, logger
import sys


log = logger.get_logger(__name__)


class StarLine:

    def __init__(self, app_id: int, secret: str, login: str, password: str, datastore: StoreDriver, **kwargs):
        log.debug('Initialising StarLine...')
        self._login = login
        self._password = password
        self._app_id = app_id
        self._secret = secret
        self._datastore = datastore
        self._metric_port = kwargs.get('metric_port', 8080)
        self._update_data = kwargs.get('update_data', 10)
        self._app_code_exp = timedelta(hours=1)
        self._app_token_exp = timedelta(hours=4)
        self._slid_user_token_exp = timedelta(hours=4)
        self._slnet_token_exp = timedelta(hours=24)
        self._event_time = datetime.utcnow().timestamp()
        self._last_event_timestamp = datetime.now().timestamp()
        metrics.system_metrics['http_requests_period'].set(self._update_data)
        log.info('StarLine was initialising with params: {}'.format(vars(self)))

    def _get_http(self, url, method='get', **kwargs):
        try:
            r = requests.request(method, url, **kwargs)
        except:
            metrics.system_metrics['http_requests'].labels(url, 'error', 'Can not request URL').inc()
            log.error('Error while request url {}. Case: {}'.format(url, sys.exc_info()[0]))
        else:
            response = r.json()
            state = int(response.get('state', 1))
            code = int(response.get('code', 200))
            if state != 1:
                message = response['desc']['message']
                metrics.system_metrics['http_requests'].labels(url, state, message).inc()
                log.error('Error while request url {}. Case: {}'.format(url, message))
            elif code != 200:
                message = response['codestring']
                metrics.system_metrics['http_requests'].labels(url, code, message).inc()
                log.error('Error while request url {}. Case: {}'.format(url, message))
            else:
                metrics.system_metrics['http_requests'].labels(url, code, 'success').inc()
                log.debug('Request url {} was successful.'.format(url))
                return [response, r.cookies]

    def _date_exp(self, exp: timedelta):
        date_exp = datetime.now() + exp
        return date_exp.timestamp()

    def _chk_time(self, exp: float) -> bool:
        return datetime.now() > datetime.fromtimestamp(exp)

    def _get_app_code(self, app_id, app_secret):
        """
        Получение кода приложения для дальнейшего получения токена.
        Идентификатор приложения и пароль выдаются контактным лицом СтарЛайн.
        Срок годности кода приложения 1 час.
        :param app_id: Идентификатор приложения
        :param app_secret: Пароль приложения
        :return: Код, необходимый для получения токена приложения
        """

        url = 'https://id.sds.ru/apiV3/application/getCode/'

        payload = {
            'appId': app_id,
            'secret': hashlib.md5(app_secret.encode('utf-8')).hexdigest()
        }
        log.debug('Try to get app_code...')
        app_code = {'code': self._get_http(url, params=payload)[0]['desc']['code']}
        app_code['date_exp'] = self._date_exp(self._app_code_exp)
        log.debug('Got app_code: {}, expired date: {}'.format(
            app_code['code'],
            datetime.fromtimestamp(app_code['date_exp']).strftime('%Y/%m/%d %H:%M')))
        return app_code

    def _get_app_token(self, app_id, app_secret, app_code):
        """
        Получение токена приложения для дальнейшей авторизации.
        Время жизни токена приложения - 4 часа.
        Идентификатор приложения и пароль можно получить на my.sds.ru.
        :param app_id: Идентификатор приложения
        :param app_secret: Пароль приложения
        :param app_code: Код приложения
        :return: Токен приложения
        """
        url = 'https://id.sds.ru/apiV3/application/getToken/'
        payload = {
            'appId': app_id,
            'secret': hashlib.md5((app_secret + app_code).encode('utf-8')).hexdigest()
        }
        log.debug('Try to get app_token...')
        app_token = {'token': self._get_http(url, params=payload)[0]['desc']['token']}
        app_token['date_exp'] = self._date_exp(self._app_token_exp)
        log.debug('Got app_token: {}, expired date: {}'.format(
            app_token['token'],
            datetime.fromtimestamp(app_token['date_exp']).strftime('%Y/%m/%d %H:%M')))

        return app_token

    def _get_slid_user_token(self, app_token, user_login, user_password):
        """
             Аутентификация пользователя по логину и паролю.
             Неверные данные авторизации или слишком частое выполнение запроса авторизации с одного
             ip-адреса может привести к запросу капчи.
             Для того, чтобы сервер SLID корректно обрабатывал клиентский IP,
             необходимо проксировать его в параметре user_ip.
             В противном случае все запросы авторизации будут фиксироваться для IP-адреса сервера приложения, что приведет к частому требованию капчи.
            :param sid_url: URL StarLineID сервера
            :param app_token: Токен приложения
            :param user_login: Логин пользователя
            :param user_password: Пароль пользователя
            :return: Токен, необходимый для работы с данными пользователя. Данный токен потребуется для авторизации на StarLine API сервере.
            """
        url = 'https://id.sds.ru/apiV3/user/login/'
        payload = {
            'token': app_token
        }

        data = {"login": user_login, "pass": hashlib.sha1(user_password.encode('utf-8')).hexdigest()}
        log.debug('Try to get slid_user_token...')
        slid_token = {'token': self._get_http(url, method='post', params=payload, data=data)[0]['desc']['user_token']}
        slid_token['date_exp'] = self._date_exp(self._slid_user_token_exp)
        log.debug('Got slid_user_token: {}, expired date: {}'.format(
            slid_token['token'],
            datetime.fromtimestamp(slid_token['date_exp']).strftime('%Y/%m/%d %H:%M')))

        return slid_token

    def _get_slnet_token(self, slid_token):
        """
            Авторизация пользователя по токену StarLineID. Токен авторизации предварительно необходимо получить на сервере StarLineID.
            :param slid_token: Токен StarLineID
            :return: Токен пользователя на StarLineAPI
            """
        url = 'https://developer.sds.ru/json/v2/auth.slid'
        data = {
            'slid_token': slid_token
        }
        log.debug('Try to get slnet_token and user_id...')
        response = self._get_http(url, method='post', json=data)
        slnet_token = {'token': response[1]['slnet']}
        slnet_token['user_id'] = response[0]['user_id']
        slnet_token['date_exp'] = self._date_exp(self._slnet_token_exp)
        log.debug('Got slnet_token: {}, expired date: {} and user_id: {}'.format(
            slnet_token['token'],
            datetime.fromtimestamp(slnet_token['date_exp']).strftime('%Y/%m/%d %H:%M'), slnet_token['user_id']))

        return slnet_token

    def _get_user_data(self, user_id, slnet_token):
        """
            Получение списка устройств принадлежиших пользователю или устройств, доступ к которым предоставлен пользователю
             другими пользователями. Ответ содержит полное состояние устройств.
            :param user_id: user identifier
            :param slnet_token: StarLineAPI Token
            :return: Код, необходимый для получения токена приложения
            """
        url = "https://developer.sds.ru/json/v3/user/{}/data".format(user_id)
        cookies = "slnet={}".format(slnet_token)

        log.debug('Try to get user data...')
        user_data = self._get_http(url, headers={"Cookie": cookies})
        log.debug('Got user data.')

        return user_data[0]

    def _get_events(self, slnet_token, device):
        """
        Получение истории событий. Для того, чтобы получить историю событий устройства,
        необходимо передать даты начала и конца временного периода,
        за который запрашивается информация (в формате Unix timestamp UTC).

        :param slnet_token: StarLineAPI Token
        :param device: идентификатор устройства в SLNet
        :return: list events
        """
        url = 'https://developer.sds.ru/json/v1/device/{}/events'
        cookies = "slnet={}".format(slnet_token)
        data = {
            "from": self._event_time,
            "to": datetime.now().utcnow().timestamp()
        }

        log.debug('Try to get device ({}) events...'.format(device))
        events = self._get_http(url.format(device), method='post', headers={"Cookie": cookies}, json=data)
        events = events[0]['events']
        self._event_time = datetime.now().utcnow().timestamp()
        log.debug('Got device ({}) events ({} events).'.format(device, len(events)))

        return events

    def _get_obd_errors(self, slnet_token, device):
        """
        Получение ошибок OBD из кеша. Запрос данных об ошибках OBD, полученных от автомобиля и хранящихся в кеше.

        :param slnet_token: StarLineAPI Token
        :param device: идентификатор устройства в SLNet
        :return: list events
        """
        url = 'https://developer.sds.ru/json/v1/device/{}/obd_errors'
        cookies = "slnet={}".format(slnet_token)

        log.debug('Try to get device ({}) obd errors...'.format(device))
        errors = self._get_http(url.format(device), method='post', headers={"Cookie": cookies})
        errors = errors[0]['obd_errors']
        self._event_time = datetime.now().utcnow().timestamp()
        log.debug('Got device ({}) obd errors ({} errors).'.format(device, len(errors)))

        return events

    def _auth(self):

        log.debug('Updating codes and tokens...')

        if self._chk_time(self._datastore.db_get_value('app_code')['date_exp']):
            self._datastore.db_update(
                'app_code',
                self._get_app_code(self._app_id, self._secret)
            )

        if self._chk_time(self._datastore.db_get_value('app_token')['date_exp']):
            self._datastore.db_update(
                'app_token',
                self._get_app_token(self._app_id, self._secret, self._datastore.db_get_value('app_code')['code'])
            )

        if self._chk_time(self._datastore.db_get_value('slid_user_token')['date_exp']):
            self._datastore.db_update(
                'slid_user_token',
                self._get_slid_user_token(self._datastore.db_get_value('app_token')['token'], self._login,
                                          self._password)
            )

        if self._chk_time(self._datastore.db_get_value('slnet_token')['date_exp']):
            self._datastore.db_update(
                'slnet_token',
                self._get_slnet_token(self._datastore.db_get_value('slid_user_token')['token'])
            )

        log.info('Codes and tokens were updated.')

    @property
    def user_data(self):
        if self._chk_time(self._datastore.db_get_value('slnet_token')['date_exp']):
            self._auth()

        ud = self._get_user_data(
            self._datastore.db_get_value('slnet_token')['user_id'],
            self._datastore.db_get_value('slnet_token')['token']
        )

        return ud

    def _devices(self, user_data: dict) -> list:
        log.debug('Try to convert JSON to flatten format...')
        flatten_devices = []
        for d in user_data['user_data']['devices']:
            flatten_devices.append(flatten(d, separator='.'))
        log.debug('JSON was converted to flatten format.')
        return flatten_devices


    # def _events(self, dev_id):
    #     events = self._get_events(self._datastore.db_get_value('slnet_token')['token'], dev_id)
    #     for event in events:
    #         log.info('')

    def monitoring_run(self):
        metrics.start_server(self._metric_port)
        first_run = True
        while True:
            src_data = self._devices(self.user_data)
            for dev in src_data:
                for key_metric, metric in metrics.starline_metrics.items():
                    log.debug('Update metric {} on device {}({})'.format(key_metric, dev['alias'], dev['device_id']))
                    metric.labels(dev['device_id'], dev['alias']).set(dev[key_metric])
                # if dev['event.timestamp'] != self._last_event_timestamp:
                #     self._last_event_timestamp = dev['event.timestamp']
                #     self._events(dev['device_id'])
            if first_run:
                log.info('Application was started.')
                first_run = False
            sleep(self._update_data * 60)



