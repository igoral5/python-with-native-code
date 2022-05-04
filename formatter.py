'''
Created on 24.11.2021
Formatter лога с долями секунды и временной зоной
@author: ilalimov
'''

import logging
import time


class FormatterMsTz(logging.Formatter):
    def __init__(self, fmt=None, datefmt=None, style='%', validate=True):
        super().__init__(fmt, datefmt, style, validate)

    def formatTime(self, record, datefmt=None):
        ct = self.converter(record.created)
        if datefmt:
            s = time.strftime(datefmt, ct)
        else:
            t = time.strftime("%Y-%m-%d %H:%M:%S", ct)
            tz = time.strftime("%Z", ct)
            s = f'{t}.{int(record.msecs):03d} {tz}'
        return s
