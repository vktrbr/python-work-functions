from numbers import Real
from typing import NamedTuple, List

import pandas as pd


class ScheduleDay(NamedTuple):
    start: pd.Timestamp  # Начало рабочего дня с точности до секунды
    end: pd.Timestamp  # Конец рабочего дня с точностью до секунды
    work: bool  # Флаг рабочего дня


def worktime(start: pd.Timestamp, end: pd.Timestamp, schedule: List[ScheduleDay]) -> Real:
    """
    Считает секунды между start и end вычитая нерабочее время из schedule

    :param start: Дата и время начала какого-то события
    :param end: Дата и время конца какого-то события
    :param schedule: Список из дней (кортеж с началом, концом и флагом рабочего дня)
    :return: Количество секунд рабочего времени
    """
    assert isinstance(schedule, List), 'type schedule must be list'
    assert isinstance(schedule[0], ScheduleDay), 'type of days must be ScheduleDay'
    schedule.sort(key=lambda x: x.start)
    return schedule


if __name__ == '__main__':
    t1 = pd.Timestamp('2022-05-04 11:15')
    t2 = pd.Timestamp('2022-05-04 14:50')

    d5 = ScheduleDay('2022-05-04 09:00', '2022-05-04 18:00', True)
    d6 = ScheduleDay('2022-06-04 09:00', '2022-06-04 18:00', True)
    d7 = ScheduleDay('2022-07-04 09:00', '2022-07-04 18:00', False)
    d8 = ScheduleDay('2022-08-04 09:00', '2022-08-04 18:00', False)

    sch = [d5, d7, d8, d6]
    print(worktime(t1, t2, sch))
