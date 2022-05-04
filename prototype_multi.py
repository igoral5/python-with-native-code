'''
Created on 06.12.2021
Нахождение hash сумм особого вида, прототип с использованием параллельно работающих процессов
@author: ilalimov
'''
import logging
from multiprocessing import get_logger, Process, Queue
from multiprocessing.connection import wait
from string import digits, ascii_letters, punctuation
from dataclasses import dataclass
from typing import Dict, List
import hashlib
from formatter import FormatterMsTz
import time
import os
import argparse

logger = get_logger()
logger.name = os.path.splitext(os.path.basename(__file__))[0]
ch = logging.StreamHandler()
formatter = FormatterMsTz(fmt='%(asctime)s [%(levelname)-8s] %(name)s %(message)s')
ch.setFormatter(formatter)
ch.setLevel(logging.INFO)
logger.addHandler(ch)
logger.setLevel(logging.INFO)


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


def mining(begin_value: str, printable: str, start: int, end: int, expected: str, queue: Queue):
    """
    Производит поиск hash сумм начинающихся особым образом

    :param begin_value: Начальная строка к которой будет добавляться случайная строка
    :param printable:   Набор символов, используемый для формирования случайной строки
    :param start:       Начальный номер строки
    :param end:         Конечный номер строки
    :param expected:    Ожидаемое начало hash суммы
    :param queue:       Очередь для отправки результата
    """
    position = slice(0, len(expected))
    for i in range(start, end):
        value = get_value(printable, i)
        hexdigest = hashlib.sha256((begin_value + value).encode()).hexdigest()
        if hexdigest[position] == expected:
            queue.put((value, hexdigest, i))
            return
    queue.put(None)


@dataclass
class Round:
    start: float
    count: int


def form_task(begin_value: str, printable: str, round: int, num_round: int, cpu_count: int, expected:str) \
        -> List[Process]:
    """
    Формирует задание для очередного раунда

    :param begin_value: Начальная строка к которой будет добавляться случайная строка
    :param printable:   Набор символов, используемый для формирования случайной строки
    :param round:       Размер раунда
    :param num_round:   Номер раунда
    :param cpu_count:   Количество параллельно работающих workers
    :param expected:    Ожидаемое начало hash суммы
    :return:            Список процессов для выполнения
    """
    part = round // cpu_count
    tasks = []
    for i in range(cpu_count):
        queue = Queue()
        if i == cpu_count - 1:
            end_value = (num_round + 1) * round
        else:
            end_value = num_round * round + (i + 1) * part
        process = Process(
            target=mining,
            args=(begin_value, printable, num_round * round + i * part, end_value, expected, queue)
        )
        process.num_round = num_round
        process.queue = queue
        tasks.append(process)
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
    rounds: Dict[int, Round] = {}
    processes: Dict[int, Process] = {}
    tasks: List[Process] = []
    success = False
    while not success:
        while len(processes) < args.workers:
            if len(tasks) == 0:
                tasks = form_task(args.begin, args.set_characters, args.round, num_round, args.workers, args.expected)
                num_round += 1
            process = tasks.pop()
            process.start()
            processes[process.sentinel] = process
            if process.num_round not in rounds:
                rounds[process.num_round] = Round(start=time.time(), count=1)
            else:
                rounds[process.num_round].count += 1
        exited = wait(processes.keys())
        for exit_process in exited:
            process = processes[exit_process]
            process.join()
            result = process.queue.get()
            del processes[exit_process]
            if result:
                value, hexdigest, i = result
                logger.info('Success "%s" hash: %s Hash rate %.3f kH/s', args.begin + value, hexdigest,
                            i/(1000 * (time.time() - start_program)))
                success = True
            else:
                rounds[process.num_round].count -= 1
                if rounds[process.num_round].count == 0:
                    logger.info('Round %s end, Hash rate %.3f kH/s', process.num_round,
                                args.round / (1000 * (time.time() - rounds[process.num_round].start)))
                    del rounds[process.num_round]
    for process in processes.values():
        process.terminate()


if __name__ == '__main__':
    main()
