# -*- coding: utf-8 -*-

from prometheus_client import start_http_server, Counter, Gauge

system_metrics = {
    'http_requests': Counter('http_requests', 'Запросы к серверу', ['url', 'code', 'message']),
    'http_requests_period': Gauge('http_requests_period', 'Интервал опроса'),
}


# event_metric = Counter('event_id', 'group_id', 'date', 'msg')

starline_user_metrics = {
    'fuel_litres': Gauge('starline_user_fuel_litres', 'Уровень топлива, литры. Расчитано относительно процентов.',
                         ['device_id', 'alias']),
    'fuel_in_100km': Gauge('starline_user_fuel_in_100km', 'Средний расход топлива на 100км за день',
                           ['device_id', 'alias']),
    'fuel_price_1km': Gauge('starline_user_fuel_price_1km', 'Средняя стоимость 1 км пути за день',
                            ['device_id', 'alias']),
}

starline_metrics = {
    'activity_ts': Gauge('starline_activity_ts',
                         'Время последней активности устройства, число секунд прошедших с 01.01.1970 по UTC',
                         ['device_id', 'alias']),
    'obd.mileage': Gauge('starline_obd_mileage', 'Пробег всего', ['device_id', 'alias']),
    'obd.ts': Gauge('starline_obd_ts', 'Метка времени обновления данных', ['device_id', 'alias']),
    'obd.fuel_percent': Gauge('starline_obd_fuel_percent', 'Уровень топлива, проценты', ['device_id', 'alias']),
    'common.etemp': Gauge('starline_common_etemp', 'Температура двигателя', ['device_id', 'alias']),
    'common.ctemp': Gauge('starline_common_ctemp', 'Температура салона', ['device_id', 'alias']),
    'common.gps_lvl': Gauge('starline_common_gps_lvl', 'Уровень приёма GPS сигнала, соответвует числу спутников GPS',
                     ['device_id', 'alias']),
    'common.gsm_lvl': Gauge('starline_common_gsm_lvl',
                     'ровень приёма GSM сигнала, соответвует числу спутников GSM. Допустимые значения: 1-30',
                     ['device_id', 'alias']),
    'common.battery': Gauge('starline_common_battery', 'Напряжение АКБ сигнализации (вольты)', ['device_id', 'alias']),
    'common.reg_date': Gauge('starline_common_reg_date', 'Метка времени обновления данных', ['device_id', 'alias']),
    'alarm_state.shock_l': Gauge('starline_alarm_state_shock_l', 'Состояние предупредительного уровня датчика удара',
                                 ['device_id', 'alias']),
    'alarm_state.add_h': Gauge('starline_alarm_state_add_h', 'Состояние тревожного уровня дополнительного датчика',
                                 ['device_id', 'alias']),
    'alarm_state.ts': Gauge('starline_alarm_state_ts', 'Метка времени обновления данных',
                                 ['device_id', 'alias']),
    'alarm_state.pbrake': Gauge('starline_alarm_state_pbrake', 'Состояние педали тормоза',
                                 ['device_id', 'alias']),
    'alarm_state.tilt': Gauge('starline_alarm_state_tilt', 'Состояние датчика наклона',
                                 ['device_id', 'alias']),
    'alarm_state.shock_h': Gauge('starline_alarm_state_shock_h', 'Состояние тревожного уровня дополнительного датчика',
                                 ['device_id', 'alias']),
    'alarm_state.add_l': Gauge('starline_alarm_state_add_l', 'Состояние предупредительного уровня дополнительного датчика',
                                 ['device_id', 'alias']),
    'alarm_state.run': Gauge('starline_alarm_state_run', 'Состояние зажигания', ['device_id', 'alias']),
    'alarm_state.door': Gauge('starline_alarm_state_door', 'Состояние зоны дверей', ['device_id', 'alias']),
    'alarm_state.trunk': Gauge('starline_alarm_state_trunk', 'Состояние зоны багажника', ['device_id', 'alias']),
    'alarm_state.hood': Gauge('starline_alarm_state_hood', 'Состояние зоны капота', ['device_id', 'alias']),
    'alarm_state.hbrake': Gauge('starline_alarm_state_hbrake', 'Состояние ручного тормоза', ['device_id', 'alias']),
    'alarm_state.hijack': Gauge('starline_alarm_state_hijack', 'Состояние режима Антиограбление', ['device_id', 'alias']),
    'balance.0.ts': Gauge('starline_balance_0_ts', 'Метка времени обновления данных', ['device_id', 'alias']),
    'balance.0.value': Gauge('starline_balance_0_value', 'Баланс SIM-карты', ['device_id', 'alias']),
    'event.type': Gauge('starline_event_type', 'Тип последнего важного события', ['device_id', 'alias']),
    'event.timestamp': Gauge('starline_event_timestamp', 'Метка времени обновления данных', ['device_id', 'alias']),
    'r_start.period.has': Gauge('starline_r_start_period', 'Наличие периодического автозапуска', ['device_id', 'alias']),
    'r_start.cron.has': Gauge('starline_r_start_cron', 'Наличие автозапуска по будильнику', ['device_id', 'alias']),
    'r_start.battery.has': Gauge('starline_r_start_battery', 'Наличие автозапуска по напряжению АКБ', ['device_id', 'alias']),
    'r_start.temp.has': Gauge('starline_r_start_temp', 'Наличие автозапуска по температуре', ['device_id', 'alias']),
    'state.ign': Gauge('starline_state_ign', 'Состояние двигателя', ['device_id', 'alias']),
    'state.alarm': Gauge('starline_state_alarm', 'Статус тревоги сигнализации', ['device_id', 'alias']),
    'state.r_start_timer': Gauge('starline_state_r_start_timer', 'Время до окончания работы автозапуска',
                                 ['device_id', 'alias']),
    'state.webasto_timer': Gauge('starline_state_webasto_timer',
                                 'Время до окончания работы предпускового подогревателя', ['device_id', 'alias']),
    'state.run': Gauge('starline_state_run', 'Состояние зажигания', ['device_id', 'alias']),
    'state.door': Gauge('starline_state_door', 'Состояние дверей', ['device_id', 'alias']),
    'state.hbrake': Gauge('starline_state_hbrake', 'Состояние ручного тормоза', ['device_id', 'alias']),
    'state.trunk': Gauge('starline_state_trunk', 'Состояние багажника', ['device_id', 'alias']),
    'state.valet': Gauge('starline_state_valet', 'Статус сервисного режима', ['device_id', 'alias']),
    'state.neutral': Gauge('starline_state_neutral', 'Режим программной нейтрали', ['device_id', 'alias']),
    'state.out': Gauge('starline_state_out', 'Состояние доп. канала', ['device_id', 'alias']),
    'state.hfree': Gauge('starline_state_hfree', 'Состояние режима Свободные руки', ['device_id', 'alias']),
    'state.arm': Gauge('starline_state_arm', 'Состояние режима охраны', ['device_id', 'alias']),
    'state.add_sens_bpass': Gauge('starline_state_add_sens_bpass', 'Состояние дополнительного датчика',
                                  ['device_id', 'alias']),
    'state.arm_auth_wait': Gauge('starline_state_arm_auth_wait',
                                 'Режим подтверждения авторизации (для устройств 6-го поколения)',
                                 ['device_id', 'alias']),
    'state.pbrake': Gauge('starline_state_pbrake', 'Состояние педали тормоза', ['device_id', 'alias']),
    'state.shock_bpass': Gauge('starline_state_shock_bpass', 'Состояние датчика удара', ['device_id', 'alias']),
    'state.r_start': Gauge('starline_state_r_start', 'Статус дистанционного запуска', ['device_id', 'alias']),
    'state.arm_moving_pb': Gauge('starline_state_arm_moving_pb', 'Режим запрета поездки (для устройств 6-го поколения)',
                                 ['device_id', 'alias']),
    'state.webasto': Gauge('starline_state_webasto', 'Состояние предпускового подогревателя', ['device_id', 'alias']),
    'state.ts': Gauge('starline_state_ts', 'Метка времени обновления данных', ['device_id', 'alias']),
    'state.hood': Gauge('starline_state_hood', 'Состояние капота', ['device_id', 'alias']),
    'state.tilt_bpass': Gauge('starline_state_tilt_bpass', 'Состояние датчика наклона', ['device_id', 'alias']),
    'state.hijack': Gauge('starline_state_hijack', 'Состояние режима Антиограбление', ['device_id', 'alias']),
    'status': Gauge('starline_status', 'Статус соединения с сервером (1-Online, 2-Offline)', ['device_id', 'alias']),
}


def start_server(port):
    start_http_server(port)


