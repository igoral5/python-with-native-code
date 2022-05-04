'''
Created on 29.11.2021
Нахождение hash сумм особого вида, простой, однопоточный вариант
@author: ilalimov
'''
from typing import Optional, Tuple
import logging
from string import digits, ascii_letters, punctuation
import hashlib
from formatter import FormatterMsTz
import time
import os
import argparse


logger = logging.getLogger(os.path.splitext(os.path.basename(__file__))[0])
ch = logging.StreamHandler()
formatter = FormatterMsTz(fmt='%(asctime)s [%(levelname)-8s] %(name)s %(message)s')
ch.setFormatter(formatter)
ch.setLevel(logging.DEBUG)
logger.addHandler(ch)
logger.setLevel(logging.DEBUG)


def get_value(printable: str, n: int) -> str:
    """
    Формирует строку, вид строки определяется числом n

    :param printable:   Список символов используемых для формирования строки
    :param n:           Число определяющее внешний вид строки
    :return:            Сформированная строка
    """
    value = ''
    length_printable = len(printable)
    n += 1
    while n > 0:
        value += printable[(n - 1) % length_printable]
        n = (n - 1) // length_printable
    return value


def mining(begin_value: str, printable: str, start: int, end: int, expected: str) -> Optional[Tuple[str, str, int]]:
    """
    Производит поиск hash сумм начинающихся особым образом

    :param begin_value: Начальная строка к которой будет добавляться случайная строка
    :param printable:   Набор символов, используемый для формирования случайной строки
    :param start:       Начальный номер строки
    :param end:         Конечный номер строки
    :param expected:    Ожидаемое начало hash суммы
    :return:            Добавленную строку, ее хеш вместе с начальной строкой и число определяющее добавленную строку
    """
    position = slice(0, len(expected))
    for i in range(start, end):
        value = get_value(printable, i)
        hexdigest = hashlib.sha256((begin_value + value).encode()).hexdigest()
        if hexdigest[position] == expected:
            return value, hexdigest, i


def main():
    parser = argparse.ArgumentParser(description='Поиск hash значений особого вида (sha256)')
    parser.add_argument('-b', '--begin', help='Начальная строка к которой будет добавляться случайная строка',
                        default='Начальное значение!')
    parser.add_argument('-s', '--set-characters',
                        help='Список символов, который будет использован для формирования случайной строки',
                        default=punctuation + digits + ascii_letters)
    parser.add_argument('-e', '--expected', help='Ожидаемое начало hash суммы', default='00000000')
    parser.add_argument('-r', '--round', type=int, help='Размер раунда', default=100000000)
    args = parser.parse_args()
    logger.info('Start')
    num_round = 0
    start_program = time.time()
    start_round = time.time()
    while True:
        res = mining(args.begin, args.set_characters, num_round * args.round, (num_round + 1) * args.round,
                     args.expected)
        if res:
            value, hexdigest, i = res
            logger.info('Success "%s" hash: %s Hash rate %.3f kH/s', args.begin + value, hexdigest,
                        i/(1000 * (time.time() - start_program)))
            break
        else:
            logger.info('Round %s end, Hash rate %.3f kH/s', num_round, args.round / (1000 * (time.time() - start_round)))
            start_round = time.time()
        num_round += 1


if __name__ == '__main__':
    main()
