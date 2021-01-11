# -*- coding: utf-8 -*-

import requests
import hashlib
from datetime import datetime, timedelta
from time import sleep
from flatten_json import flatten
from src.StoreDriver import StoreDriver
from src import metrics, logger
from src.Exception import *
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
        except Exception as e:
            metrics.system_metrics['http_requests'].labels(url, 'error', 'Can not request URL').inc()
            log.error('Error while request url {}. Case: {}'.format(url, e.args[0]))
            raise SdsHttpException('Error while request url {}. Case: {}'.format(url, sys.exc_info()[0]))
        else:
            response = r.json()
            state = int(response.get('state', 1))
            code = int(response.get('code', 200))
            if state != 1:
                message = response['desc']['message']
                metrics.system_metrics['http_requests'].labels(url, state, message).inc()
                log.error('Error while request url {}. State: {}. Case: {}'.format(url, state, message))
                raise SdsHttpResultCodeException('Error while request url {}. State: {}. Case: {}'.format(
                    url, state, message
                ))
            elif code != 200:
                message = response['codestring']
                metrics.system_metrics['http_requests'].labels(url, code, message).inc()
                log.error('Error while request url {}. Code: {}. Case: {}'.format(url, code, message))
                raise SdsHttpResultCodeException('Error while request url {}. Code: {}. Case: {}'.format(
                    url, code, message
                ))
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

        url = 'https://id.starline.ru/apiV3/application/getCode/'

        payload = {
            'appId': app_id,
            'secret': hashlib.md5(app_secret.encode('utf-8')).hexdigest()
        }
        log.debug('Try to get app_code...')
        try:
            app_code = {'code': self._get_http(url, params=payload)[0]['desc']['code']}
        except SdsHttpException as e:
            log.error('App_code не получен. ({})'.format(e.args[0]))
            raise SdsAppCodeException('App_code не получен. ({})'.format(e.args[0]))
        else:
            app_code['date_exp'] = self._date_exp(self._app_code_exp)
            log.debug('Got app_code: {}, expired date: {}'.format(
                app_code['code'],
                datetime.fromtimestamp(app_code['date_exp']).strftime('%Y/%m/%d %H:%M')))
            return app_code

    def _get_app_token(self, app_id, app_secret, app_code):
        """
        Получение токена приложения для дальнейшей авторизации.
        Время жизни токена приложения - 4 часа.
        Идентификатор приложения и пароль можно получить на my.starline.ru.
        :param app_id: Идентификатор приложения
        :param app_secret: Пароль приложения
        :param app_code: Код приложения
        :return: Токен приложения
        """
        url = 'https://id.starline.ru/apiV3/application/getToken/'
        payload = {
            'appId': app_id,
            'secret': hashlib.md5((app_secret + app_code).encode('utf-8')).hexdigest()
        }
        log.debug('Try to get app_token...')
        try:
            app_token = {'token': self._get_http(url, params=payload)[0]['desc']['token']}
        except SdsHttpException as e:
            log.error('App_token не получен ({})'.format(e.args[0]))
            raise SdsAppTokenException('App_token не получен ({})'.format(e.args[0]))
        else:
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
        url = 'https://id.starline.ru/apiV3/user/login/'
        payload = {
            'token': app_token
        }

        data = {"login": user_login, "pass": hashlib.sha1(user_password.encode('utf-8')).hexdigest()}
        log.debug('Try to get slid_user_token...')
        try:
            slid_token = {'token': self._get_http(url, method='post', params=payload, data=data)[0]['desc']['user_token']}
        except SdsHttpException as e:
            log.error('Slid_user_token не получен ({})'.format(e.args[0]))
            raise SdsSlidUserTokenException('Slid_user_token не получен ({})'.format(e.args[0]))
        else:
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
        url = 'https://developer.starline.ru/json/v2/auth.slid'
        data = {
            'slid_token': slid_token
        }
        log.debug('Try to get slnet_token and user_id...')
        try:
            response = self._get_http(url, method='post', json=data)
            slnet_token = {'token': response[1]['slnet']}
            slnet_token['user_id'] = response[0]['user_id']
        except SdsHttpException as e:
            log.error('Slnet_token не получен ({})'.format(e.args[0]))
            raise SdsSlnetTokenException('Slnet_token не получен ({})'.format(e.args[0]))
        else:
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
        url = "https://developer.starline.ru/json/v3/user/{}/data".format(user_id)
        cookies = "slnet={}".format(slnet_token)

        log.debug('Try to get user data...')
        try:
            user_data = self._get_http(url, headers={"Cookie": cookies})[0]
        except SdsHttpException as e:
            log.error('User data не получен ({})'.format(e.args[0]))
            raise SdsUserDataException('User data не получен ({})'.format(e.args[0]))
        else:
            log.debug('Got user data.')

            return user_data

    def _get_events(self, slnet_token, device) -> list:
        """
        Получение истории событий. Для того, чтобы получить историю событий устройства,
        необходимо передать даты начала и конца временного периода,
        за который запрашивается информация (в формате Unix timestamp UTC).

        :param slnet_token: StarLineAPI Token
        :param device: идентификатор устройства в SLNet
        :return: list events
        """
        url = 'https://developer.starline.ru/json/v1/device/{}/events'
        cookies = "slnet={}".format(slnet_token)
        data = {
            "from": self._event_time,
            "to": datetime.now().utcnow().timestamp()
        }

        log.debug('Try to get device ({}) events...'.format(device))
        try:
            events = self._get_http(url.format(device), method='post', headers={"Cookie": cookies}, json=data)
            events = events[0]['events']
        except SdsHttpException as e:
            log.error('Device events не получен ({})'.format(e.args[0]))
            raise SdsEventsException('Device events не получен ({})'.format(e.args[0]))
        else:
            self._event_time = datetime.now().utcnow().timestamp()
            log.debug('Got device ({}) events ({} events).'.format(device, len(events)))

            return events

    # def _get_obd_errors(self, slnet_token, device):
    #     """
    #     Получение ошибок OBD из кеша. Запрос данных об ошибках OBD, полученных от автомобиля и хранящихся в кеше.
    #
    #     :param slnet_token: StarLineAPI Token
    #     :param device: идентификатор устройства в SLNet
    #     :return: list events
    #     """
    #     url = 'https://developer.starline.ru/json/v1/device/{}/obd_errors'
    #     cookies = "slnet={}".format(slnet_token)
    #
    #     log.debug('Try to get device ({}) obd errors...'.format(device))
    #     try:
    #         errors = self._get_http(url.format(device), method='post', headers={"Cookie": cookies})
    #         errors = errors[0]['obd_errors']
    #     except SdsHttpException as e:
    #         log.error('OBD errors не получен ({})'.format(e.args[0]))
    #         raise SdsOBDException('OBD errors не получен ({})'.format(e.args[0]))
    #     else:
    #         self._event_time = datetime.now().utcnow().timestamp()
    #         log.debug('Got device ({}) obd errors ({} errors).'.format(device, len(errors)))
    #
    #         return errors

    def _auth(self):

        log.debug('Updating codes and tokens...')
        try:
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
        except SdsAuthException as e:
            log.error('Codes and tokens were updated ({})'.format(e.args[0]))
        else:
            log.info('Codes and tokens were updated.')

    @property
    def user_data(self):
        if self._chk_time(self._datastore.db_get_value('slnet_token')['date_exp']):
            self._auth()

        try:
            ud = self._get_user_data(
                self._datastore.db_get_value('slnet_token')['user_id'],
                self._datastore.db_get_value('slnet_token')['token']
            )
        except SdsUserDataException as e:
            log.error(e.args[0])
        else:
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
    #     for event in reversed(events):
    #         log.debug('Got event src: {}'.format(event))
    #         dt = datetime.fromtimestamp(event['ts']).strftime('%Y/%m/%d %H:%M')
    #         log.info('EVENT: {} at {}'.format(events_map.events[event['event_id']], dt))
    #         metrics.event_metric.labels(
    #             event['event_id'],
    #             event['group_id'],
    #             events_map.events[event['event_id']]
    #         ).inc()

    def monitoring_run(self):
        metrics.start_server(self._metric_port)
        first_run = True
        while True:
            src_data = self._devices(self.user_data)
            for dev in src_data:
                for key_metric, metric in metrics.starline_metrics.items():
                    log.debug('Update metric {} on device {}({})'.format(key_metric, dev['alias'], dev['device_id']))
                    metric.labels(dev['device_id'], dev['alias']).set(dev[key_metric])
                if dev['event.timestamp'] != self._last_event_timestamp:
                    self._events(dev['device_id'])
                    self._last_event_timestamp = dev['event.timestamp']
            if first_run:
                log.info('Application was started.')
                first_run = False
            sleep(self._update_data * 60)



