from typing import NamedTuple, List, Text

import numpy as np
import pandas as pd


class ScheduleDay(NamedTuple):
    """
    При создании этого кортежа нужно указать три значения в следующем порядке:
        1. Начало дня
        2. Конец дня
        3. Флаг (True / False) рабочий ли это день

    .. note::
        Если день выходной, то нужно указать start = end = "ГОД-МЕСЯЦ-ДЕНЬ 00:00:00"

    """
    start: pd.Timestamp  # Начало рабочего дня с точности до секунды
    end: pd.Timestamp  # Конец рабочего дня с точностью до секунды
    is_work: bool  # Флаг рабочего дня


def make_schedule_day(start: Text, end: Text, is_work: bool) -> ScheduleDay:
    """ Функция приведет к нужному типу start, end и сделает объект ScheduleDay """
    start = pd.Timestamp(start)
    end = pd.Timestamp(end)
    return ScheduleDay(start, end, is_work)


def worktime(start: pd.Timestamp, end: pd.Timestamp, schedule: List[ScheduleDay]) -> pd.Timedelta:
    """
    Возвращает число секунд между start и end вычитая нерабочее время из schedule.

    :param start: Дата и время начала какого-то события
    :param end: Дата и время конца какого-то события
    :param schedule: Список из дней (кортеж с началом, концом и флагом рабочего дня)
    :return: pd.Timedelta, который можно преобразовать к секундам с помощью метода атрибута seconds
    """

    assert isinstance(schedule, List), 'type schedule must be list'
    assert isinstance(schedule[0], ScheduleDay), 'type of days must be ScheduleDay'
    assert start <= end, 'timestamp 1 (start) must not be later than timestamp 2 (end)'

    schedule.sort(key=lambda x: x.start)  # Отсортируем расписание по началу рабочего дня

    # Оставим из расписания определенные дни. Начало рабочего дня должно быть меньше второй временной метки
    # Конец рабочего дня должен быть больше первой временной метки.
    schedule = list(filter(lambda x: x.start <= end and start <= x.end, schedule))

    total_time = pd.Timedelta(0)
    if len(schedule) == 1:
        if start.date() == end.date():  # Если две временные отметки в одних сутках, то возвращает просто их разность
            return end - start
        # Если даты разные, но при этом рабочий день один, то есть работник закончил позднее 00:00, но раньше, чем
        # начался следующий рабочий день по расписанию, то находим время от первой отметки до конца рабочего дня
        else:
            return schedule[0].end - start

    if len(schedule) > 2:  # Суммируем все целые рабочие дни
        for day in schedule[1:-1]:  # между датами
            if day.is_work:  # Проверяем, что день рабочий
                total_time += day.end - day.start
            schedule.remove(day)


    if schedule[0].is_work:
        total_time += schedule[0].end - start  # Прибавляем рабочее время в первый РАБОЧИЙ день
    if schedule[1].is_work:
        total_time += end - schedule[1].start  # Прибавляет время в последний РАБОЧИЙ день

    return total_time


def convert_data(data: pd.DataFrame, day_col_name: Text = 'day', start_time_col_name: Text = 'start_time',
                 end_time_col_name: Text = 'end_time', is_work_col_name: Text = 'is_work',
                 start_time_default: Text = '09:00:00', end_time_default: Text = '18:00:00') -> List[ScheduleDay]:
    """
    Возвращает список из объектов ScheduleDay. На вход принимает датасет, в котором есть столбцы со значениями:
        1. День в формате даты без времени "ГОД-МЕСЯЦ-ДЕНЬ". Данные в столбце должен быть в формате datetime64[ns]
        2. Время начала и конца рабочего дня, строковые данные.
        3. Флаг рабочего дня, True если день - рабочий, иначе False

    .. note::
        Если значения в расписаниях пустые, то для рабочих дней они заполнятся с start_time_default и end_time_default,
        а для выходных время начала и конца будут равны 00:00:00.

        Если в выходной день есть время начала и конца, которое отличается от 00:00:00, то этот день считается рабочим.

    :param data: Сама таблица с данными
    :param day_col_name: Название столбца с датой
    :param start_time_col_name: Название столбца с началом рабочего дня
    :param end_time_col_name: Название столбца с концом рабочего дня
    :param is_work_col_name: Флаг рабочего дня
    :param start_time_default: Время для заполнения пропуска в начале рабочего дня
    :param end_time_default: Время для заполнения пропуска в конце рабочего дня
    :return: Список из ScheduleDay

    .. warning:: В таблице data не должно быть пропусков нигде, кроме start_time_col_name, end_time_col_name
                 Типы в столбцах обязательно такие как описаны выше.
    """
    data = data[[day_col_name, start_time_col_name, end_time_col_name, is_work_col_name]]
    assert data.isna().sum(axis=0)[day_col_name] == 0, 'Столбец дня должен быть без пропусков'
    assert data.isna().sum(axis=0)[is_work_col_name] == 0, 'Столбец флага рабочего дня должен быть без пропусков'

    def convert_raw(raw: pd.Series) -> ScheduleDay:
        """Заполняет пропуски во времени. Выходные значениями 00:00:00, Будни с помощью default значений"""
        if not raw[is_work_col_name]:  # Работаем с выходным
            # Если оба значения пропущены, то заполняем нулями
            if np.all(pd.isna(raw[[start_time_col_name, end_time_col_name]])):
                raw = raw.fillna('00:00:00')

            # Если начало пропущено, а конец нет, проверим конец на значение 00:00 и заполним
            elif pd.isna(raw[start_time_col_name]) and pd.notna(raw[end_time_col_name]):
                if pd.Timestamp(raw[end_time_col_name]) == pd.Timestamp('00:00:00'):
                    raw = raw.fillna('00:00:00')
                else:
                    raw[start_time_col_name] = start_time_default
                    raw[is_work_col_name] = True

            # Наоборот проверим конец и начало
            elif pd.isna(raw[end_time_col_name]) and pd.notna(raw[start_time_col_name]):
                if pd.Timestamp(raw[start_time_col_name]) == pd.Timestamp('00:00:00'):
                    raw = raw.fillna('00:00:00')
                else:
                    raw[end_time_col_name] = end_time_default
                    raw[is_work_col_name] = True

            # Если оба значения не пропущены, то проверим, что они оба 00:00:00, если нет, то день рабочий
            else:
                if (pd.Timestamp(raw[start_time_col_name]) != pd.Timestamp('00:00:00') or
                        pd.Timestamp(raw[end_time_col_name]) != pd.Timestamp('00:00:00')):
                    raw[is_work_col_name] = True

        else:  # Заполним рабочий день
            if pd.isna(raw[start_time_col_name]):
                raw[start_time_col_name] = start_time_default
            if pd.isna(raw[end_time_col_name]):
                raw[end_time_col_name] = end_time_default

        # Приводим к корректному времени и создаем ScheduleDay
        start_datetime = pd.Timestamp(raw[day_col_name].strftime('%Y-%m-%d') + ' ' + raw[start_time_col_name])
        end_datetime = pd.Timestamp(raw[day_col_name].strftime('%Y-%m-%d') + ' ' + raw[end_time_col_name])

        return ScheduleDay(start_datetime, end_datetime, raw[is_work_col_name])

    data = data.apply(convert_raw, axis=1)
    return data.to_list()


if __name__ == '__main__':
    pass
    # Проверка на данных из таблицы
    # import pandas as pd
    #
    # schedule_raw = pd.read_excel('test/worktime-test-example.xlsx', sheet_name='Расписание',
    #                              dtype={'Начало рабочего дня': str, 'Конец рабочего дня': str})
    # data_raw = pd.read_excel('test/worktime-test-example.xlsx', sheet_name='Случаи')
    # sch = convert_data(schedule_raw, 'День', 'Начало рабочего дня', 'Конец рабочего дня', 'Рабочий день')
    # for i in range(data_raw.shape[0]):
    #     dt = worktime(data_raw.loc[i, 'Степ 1'], data_raw.loc[i, 'Степ 2'], sch)
    #     data_raw.loc[i, 'Рабочее время в секундах'] = dt

    # Проверка на данных для разработки
    # t1 = pd.Timestamp('2022-05-04 11:15')
    # t2 = pd.Timestamp('2022-05-05 14:50')
    #
    # d5 = make_schedule_day('2022-05-04 09:00', '2022-05-04 18:00', True)
    # d6 = make_schedule_day('2022-05-05 09:00', '2022-05-05 18:00', True)
    # d7 = make_schedule_day('2022-05-06 00:00', '2022-05-06 00:00', False)
    # d8 = make_schedule_day('2022-05-07 00:00', '2022-05-07 00:00', False)
    #
    # sch = [d5, d7, d8, d6]
    # print(worktime(t1, t2, sch))
