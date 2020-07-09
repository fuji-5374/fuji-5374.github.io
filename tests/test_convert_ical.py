# coding: utf-8

import pytest

from icalendar import Event, Calendar
from convert_ical import adjust_weeknum, gen_recurceve_event, gen_one_event


@pytest.mark.parametrize(("number", "n_s", "n_q"), [(6, 4, 3), (3, 4, 7)])
def test_ajust_weeknum(number, n_s, n_q):
    assert number == adjust_weeknum(n_s, n_q)


def test_gen_one_event():

    name = "びん"
    category = "20200716"
    center_dates = {"休止開始日": "2020/12/30", "休止終了日": "2021/1/3"}

    test_events = gen_one_event(name, category, center_dates)
    assert len(test_events) == 1

    # TODO:2020-07-09 eventのical出力をそのまま生成する？
    # print(test_events[0].to_ical())


def test_gen_recurceve_event():

    name = "燃えるごみ"
    category = "火"
    center_dates = {"休止開始日": "2020/12/30", "休止終了日": "2021/1/3"}

    test_events = gen_recurceve_event(name, category, center_dates)
    assert len(test_events) == 2

    # TODO:2020-07-09 eventのical出力をそのまま生成する？
