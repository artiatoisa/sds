# -*- coding: utf-8 -*-

from abc import ABC, abstractmethod


class StoreDriver(ABC):

    def __init__(self, db_file_name: str = None):
        self._db_file_name = db_file_name or 'data_store.db'

    @abstractmethod
    def db_init(self):
        pass

    @abstractmethod
    def db_insert(self, key: str, value: dict):
        pass

    @abstractmethod
    def db_update(self, key: str, value: dict):
        pass

    @abstractmethod
    def db_get_value(self, key: str):
        pass


