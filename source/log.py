#!/usr/local/bin/python3
# -*- coding: utf-8 -*-
# simagin.mail@yandex.ru


import logging


def report_wrap(report):
    def wrap(message, *args, **kargs):
        if message is str:
             report(message.format(*args, **kargs))
        else:
            report(repr(message))
    return wrap


MESSAGE_FORMAT ='[%(asctime)s] %(levelname)-8s : %(message)s'
DATE_FORMAT = '%y.%m.%d %H:%M:%S'


CRITICAL = logging.CRITICAL
ERROR = logging.ERROR
DEBUG = logging.DEBUG


debug = report_wrap(logging.debug)
error = report_wrap(logging.error)
critical = report_wrap(logging.critical)


def level(level_name):
    return {
        'critical': CRITICAL,
        'error': ERROR,
        'debug': DEBUG
    }[level_name]


def config(level):
    logging.basicConfig(format=MESSAGE_FORMAT, level=level, datefmt=DATE_FORMAT)