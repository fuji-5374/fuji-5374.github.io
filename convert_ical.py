# coding: utf-8

import csv
import re
from copy import copy
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Callable, Dict, Optional, Sequence, Tuple

from icalendar import Calendar, Event

EXCLUDE_HEADER = ["地区", "センター", "センター休止日"]

# TODO:2020-07-08 この指定をしたくない...がいい方法が出なかったので
GOMI_CALENER_START = date(2020, 4, 1)
GOMI_CALENER_END = date(2021, 3, 31)


def ajust_weeknum(n_s: int, n_q: int):
    """
    5374が扱う開始日付と、ごみカテゴリ記法の繰り返し表現を元に、ical繰り返しイベントの開始日に合わせる日付調整用の数値を生成

    date.timedeltaメソッドで利用する

    曜日と曜日の並び番号は、スタートが日曜日, 日曜:1、月曜:2...土曜:7 となる

    考え方として、n_sを開始日付の曜日番号, n_qを繰り返しイベントに設定する曜日の番号とする。

    # 7/1:4 <= 7/7:3 = 6
    >>> print(ajust_weeknum(4, 3))
    6

    # 7/1:4 > 7/4:7 = 3
    >>> print(ajust_weeknum(4, 1))
    3

    """
    if n_s <= n_q:
        return n_q - n_s
    else:
        return (7 - n_s) + n_q


def gen_one_event(
    name: str, category: str, center_dates: Sequence[Dict]
) -> Sequence[Event]:
    """
    5374の不定期イベントを生成する

    8文字の数字を読み込んで、icalイベントに変換している。

    """

    start_date = datetime.strptime(category, "%Y%m%d").date()
    end_date = start_date + timedelta(days=1)

    event = Event()

    event.add("summary", name)
    event.add("dtstart", start_date)
    event.add("dtend", end_date)
    event.add("dtstamp", start_date)

    return [event]


# TODO:2020-07-08 ここの戻り値はリストにする
def gen_recurceve_event(
    name: str, category: str, center_dates: Sequence[Dict]
) -> Sequence[Event]:
    """
    5374の繰り返しイベントを生成する

    センターの休止期間を考慮して、二つの繰り返しイベントが生成される。

    """

    def _event_generate(
        event_startdate: date,
        gomi_pattern_weeknum: int,
        event_untiledate: date,
        ical_rrule: dict,
    ):
        """
        繰り返しイベントに必要な情報を元に、icalイベントの生成をする


        """
        rcur_start_weeknum = int(event_startdate.strftime("%w")) + 1

        start_date = event_startdate + timedelta(
            days=ajust_weeknum(rcur_start_weeknum, gomi_pattern_weeknum)
        )

        e_ical_rrule = copy(ical_rrule)
        e_ical_rrule["until"] = event_untiledate

        e = Event()
        e.add("summary", name)
        e.add("dtstart", start_date)
        e.add("dtend", start_date + timedelta(days=1))
        e.add("dtstamp", start_date)
        e.add("rrule", e_ical_rrule)

        return e

    # icalフォーマットと、ここで利用する曜日の番号のセットを用意
    week_map = {
        "日": ("SU", 1),
        "月": ("MO", 2),
        "火": ("TU", 3),
        "水": ("WE", 4),
        "木": ("TH", 5),
        "金": ("FR", 6),
        "土": ("SA", 7),
    }

    if len(category) == 1:
        # 曜日のみの場合
        week_jp_fmt = category[0]
        # 曜日文字から、
        ical_byday = week_map.get(week_jp_fmt)[0]
        ical_rrule = {
            "freq": "weekly",
            "wkst": "su",
            "until": None,
            "byday": ical_byday,
        }

    elif len(category) == 2:
        # 曜日 + 数字=第[数字]周の曜日 の場合
        week_jp_fmt = category[0]
        month_of_weeknum = category[1]

        ical_byday = week_map.get(week_jp_fmt)[0]
        ical_rrule = {
            "freq": "monthly",
            "wkst": "su",
            "until": None,
            "byday": month_of_weeknum + ical_byday,
        }

    # センターの休止開始/終了日をdateオブジェクトに
    center_rest_startday = datetime.strptime(center_dates["休止開始日"], "%Y/%m/%d").date()
    center_rest_endday = datetime.strptime(center_dates["休止終了日"], "%Y/%m/%d").date()

    gomi_pattern_weeknum = week_map.get(week_jp_fmt)[1]

    # 年度のセンター休止期間を基準に二つの繰り返しイベントを作成
    # event1: ごみ開始日(+曜日までのプラス数日)->年末のセンター休止開始日
    event1 = _event_generate(
        GOMI_CALENER_START, gomi_pattern_weeknum, center_rest_startday, ical_rrule
    )
    # event2: 年始のセンター休止終了日(+曜日までのプラス数日）->ごみカレンダー終了日
    event2 = _event_generate(
        center_rest_endday, gomi_pattern_weeknum, GOMI_CALENER_END, ical_rrule
    )

    return [event1, event2]


def search_pattern(
    event_str: str,
) -> Tuple[Optional[str], Optional[Callable[[str, str], Sequence[Event]]]]:

    """
    ごみのカレンダーのカテゴリ記法を元に、文字列をパターンマッチさせて、マッチした文字列とicalに必要な情報の生成を行う関数を返す

    ごみのカレンダーの定義フォーマット:https://github.com/codeforkanazawa-org/5374/blob/master/LOCALIZE.md


    """

    # パターンと処理する関数をセットにする。関数の部分がNoneはまだ未実装
    gomi_category_patternset = [
        (r"^[月火水木金土日]", gen_recurceve_event),
        (r"^[月火水木金土日]\d", gen_recurceve_event),
        (r"^[月火水木金土日]:", None),
        (r"^[月火水木金土日]\d:", None),
        (r"^\d{8}", gen_one_event),
    ]

    # regexでマッチさせて
    for category_pattern, gen_event_func in gomi_category_patternset:

        matched = re.match(category_pattern, event_str)
        # 当たったら、その結果を返す
        if matched:
            return (matched.group(), gen_event_func)

    # 見つからなければ タプルの中身は全部Noneを返す
    return (None, None)


def main():
    # CSVファイル読み込み
    # センター情報
    center_csv_datalist = None
    with open("./data/center.csv", encoding="utf-8") as center_csv_file:
        center_csv_datalist = list(csv.DictReader(center_csv_file))

    # areadaysを読み込む -> 各地区=パターンとしていく
    areadays_csv_datalist = None
    with open("./data/area_days.csv", encoding="utf-8") as areadays_csv_file:
        areadays_csv_datalist = list(csv.DictReader(areadays_csv_file))

    # センター休止日情報もarea_days側にジョイント
    gomi_pattern_list = list()
    for areaday in areadays_csv_datalist:
        # csvなので浅めのコピー
        gomi_pattern = copy(areaday)
        # TODO:2020-07-07 もうちょっときれいに書けそう。。
        for center in center_csv_datalist:
            if areaday["センター"] == center["名称"]:
                gomi_pattern["センター休止日"] = {
                    key: center[key]
                    for key in [k for k in center.keys() if k not in ["名称"]]
                }
                gomi_pattern_list.append(gomi_pattern)

    # カレンダー生成: パターンごとに生成
    for gomi_pattern in gomi_pattern_list:

        # ディレクトリとファイル名生成
        ical_dir = Path("./ical/")
        ical_dir.mkdir(exist_ok=True)
        filename = ical_dir / "fuji5374_{}.ical".format(gomi_pattern["地区"])

        # パターンのカレンダーを作成
        cal = Calendar()
        cal.add("prodid", "-//fuji-5374//fuji-5374//JP")
        cal.add("version", "2.0")

        # パターンのごみカテゴリ事にicalイベント生成
        for gomi_name, gomi_events in gomi_pattern.items():

            if gomi_name in EXCLUDE_HEADER:
                continue

            _gomi_events_str = copy(gomi_events)

            # カテゴリの文字列をパターンマッチさせてイベントを生成する
            while len(_gomi_events_str) > 0:

                # ごみカテゴリーをひとつづつ抽出
                match_event_str, gen_ical_func = search_pattern(_gomi_events_str)

                # マッチしない出来ないイベント or マッチしても現時点で対応してない場合
                if gen_ical_func is None:
                    continue
                else:
                    # icalイベントを生成する
                    ical_events = gen_ical_func(
                        gomi_name, match_event_str, gomi_pattern["センター休止日"]
                    )
                    # icalカレンダーオブジェクトへ追加
                    for ical_event in ical_events:
                        cal.add_component(ical_event)

                # イベントの元になる文字列を削る。+1は空白除去
                _gomi_events_str = _gomi_events_str[len(match_event_str) + 1 :]

        # icsファイルに保存
        with open(filename, "wb") as export_ics:
            export_ics.write(cal.to_ical())


if __name__ == "__main__":
    main()
