'''
Created on 09.12.2021
Нахождение hash сумм особого вида, c использование C extension
@author: ilalimov
'''
from typing import List, Tuple, Any
import logging
from formatter import FormatterMsTz
import os
import signal
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED
import time
from string import punctuation, digits, ascii_letters
import mining
from dataclasses import dataclass
import argparse


logger = logging.getLogger(os.path.splitext(os.path.basename(__file__))[0])
ch = logging.StreamHandler()
formatter = FormatterMsTz(fmt='%(asctime)s [%(levelname)-8s] %(name)s %(message)s')
ch.setFormatter(formatter)
ch.setLevel(logging.DEBUG)
logger.addHandler(ch)
logger.setLevel(logging.DEBUG)


@dataclass
class Round:
    start: float
    count: int


def form_task(begin_value: str, printable: str, round: int, num_round: int, cpu_count: int, expected: str) \
        -> List[Tuple[Any, ...]]:
    """
    Формирует задание для очередного раунда

    :param begin_value: Начальная строка к которой будет добавляться случайная строка
    :param printable:   Набор символов, используемый для формирования случайной строки
    :param round:       Размер раунда
    :param num_round:   Номер раунда
    :param cpu_count:   Количество параллельно работающих workers
    :param expected:    Ожидаемое начало hash суммы
    :return:            Задание для раунда
    """
    part = round // cpu_count
    tasks = []
    for i in range(cpu_count):
        if i == cpu_count - 1:
            end_value = (num_round + 1) * round
        else:
            end_value = num_round * round + (i + 1) * part
        tasks.append((begin_value, printable, num_round * round + i * part, end_value, expected, num_round))
    return tasks


def main():
    parser = argparse.ArgumentParser(description='Поиск hash значений особого вида (sha256)')
    parser.add_argument('-b', '--begin', help='Начальная строка к которой будет добавляться случайная строка',
                        default='Начальное значение!')
    parser.add_argument('-s', '--set-characters',
                        help='Список символов, который будет использован для формирования случайной строки',
                        default=punctuation + digits + ascii_letters)
    parser.add_argument('-w', '--workers', type=int, help='Количество параллельно работающих обработчиков',
                        default=os.cpu_count())
    parser.add_argument('-e', '--expected', help='Ожидаемое начало hash суммы', default='00000000')
    parser.add_argument('-r', '--round', type=int, help='Размер раунда', default=100000000)
    args = parser.parse_args()
    logger.info('Start')
    num_round = 0
    start_program = time.time()
    success = False
    tasks = []
    futures = set()
    rounds = {}
    with ThreadPoolExecutor(max_workers=args.workers) as executor:

        def signal_handler(signum, frame):
            mining.stop_working()
            executor.shutdown()

        signal.signal(signal.SIGINT, signal_handler)
        while not success:
            while len(futures) < args.workers:
                if len(tasks) == 0:
                    tasks = form_task(args.begin, args.set_characters, args.round, num_round, args.workers,
                                      args.expected)
                    num_round += 1
                arguments = tasks.pop()
                task_round = arguments[-1]
                if task_round in rounds:
                    rounds[task_round].count += 1
                else:
                    rounds[task_round] = Round(start=time.time(), count=1)
                logger.debug('Start thread %s, round %s', rounds[task_round].count, task_round)
                future = executor.submit(mining.mining, *arguments[:-1])
                future.num_round = task_round
                futures.add(future)
            completed, futures = wait(futures, return_when=FIRST_COMPLETED)
            for done in completed:
                result = done.result()
                if result:
                    value, hexdigest, i = result
                    logger.info('Success "%s" hash: %s Hash rate %.3f kH/s', args.begin + value, hexdigest,
                                i/(1000 * (time.time() - start_program)))
                    success = True
                else:
                    logger.debug('Stop thread %s, round %s', rounds[done.num_round].count, done.num_round)
                    rounds[done.num_round].count -= 1
                    if rounds[done.num_round].count == 0:
                        logger.info('Round %s end, Hash rate %.3f kH/s', done.num_round,
                                    args.round / (1000 * (time.time() - rounds[done.num_round].start)))
                        del rounds[done.num_round]
        mining.stop_working()


if __name__ == '__main__':
    main()
