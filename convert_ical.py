import csv
import re
from copy import copy
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import Callable, Optional, Tuple, Sequence, Dict
from pprint import pprint

from icalendar import Calendar, Event

EXCLUDE_HEADER = ["地区", "センター", "センター休止日"]

# TODO:2020-07-08 この指定をしたくない...がいい方法が出なかったので
GOMI_CALENER_START = date(2020, 4, 1)
GOMI_CALENER_END = date(2021, 3, 31)


def youbi_zurashi(n_s, n_q):
    """
    曜日をずらす数値をgetする

    必要な物
    ごみ開始日->ごみ開始日の曜日番号
    繰り返しの曜日->曜日番号


    繰り返しはじめの日付決定用のスライドさせる日数
    もしごみ開始日の曜日番号<=繰り返し番号
    n?-ns
    もしごみ開始日の曜日番号＞繰り返し番号
    (7-ns)+n?

    """
    if n_s <= n_q:
        return n_q - n_s
    else:
        return (7 - n_s) + n_q


# TODO:2020-07-08 ここの戻り値はリストにする。全部においてそうする
def gen_one_event(
    name: str, category: str, center_dates: Sequence[Dict]
) -> Sequence[Event]:
    """5374の不定期イベントを生成する

    # センターの締まっている時間を考慮する
    # - もしその時間にイベントを作ろうとしたら消す（繰り返しイベント的な物の範囲ができるか
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
    """5374の繰り返しイベントを生成する

    # センターの締まっている時間を考慮する
    # - もしその時間にイベントを作ろうとしたら消す（繰り返しイベント的な物の範囲ができるか
    """

    youbi_set = {
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
        youbi = category[0]
        # 曜日文字から、
        ical_byday = youbi_set.get(youbi)[0]
        ical_rrule = {
            "freq": "weekly",
            "wkst": "su",
            "until": None,
            "byday": ical_byday,
        }

    elif len(category) == 2:
        # 曜日 + 数字=第[数字]周の曜日 の場合
        youbi = category[0]
        syuume = category[1]

        ical_byday = youbi_set.get(youbi)[0]
        ical_rrule = {
            "freq": "monthly",
            "wkst": "su",
            "until": None,
            "byday": syuume + ical_byday,
        }

    # センターの休止開始/終了日をdateオブジェクトに
    center_rest_startday = datetime.strptime(center_dates["休止開始日"], "%Y/%m/%d").date()
    center_rest_endday = datetime.strptime(center_dates["休止終了日"], "%Y/%m/%d").date()

    kurikaesi_youbi_num = youbi_set.get(youbi)[1]

    # 年度のセンター休止期間を基準に二つの繰り返しイベントを作成

    # event1: ごみ開始日(+曜日までのプラス数日)->年末のセンター休止開始日

    event1_gomi_rcur_start_youbi_num = int(GOMI_CALENER_START.strftime("%w")) + 1
    event1_zurasu_num = youbi_zurashi(
        event1_gomi_rcur_start_youbi_num, kurikaesi_youbi_num
    )
    event1_gomi_rrule_start_date = GOMI_CALENER_START + timedelta(
        days=event1_zurasu_num
    )

    event1_ical_rrule = copy(ical_rrule)
    event1_ical_rrule["until"] = center_rest_startday

    event1 = Event()
    event1.add("summary", name)
    event1.add("dtstart", event1_gomi_rrule_start_date)
    event1.add("dtend", event1_gomi_rrule_start_date + timedelta(days=1))
    event1.add("dtstamp", event1_gomi_rrule_start_date)
    event1.add("rrule", event1_ical_rrule)

    # この期間の終了日（繰り返し機関の終わり）は、年末のセンター休止開始日まで

    # ---

    # evemt2.年始のセンター休止終了日(+曜日までのプラス数日）->ごみカレンダー終了日

    event2_gomi_rcur_start_youbi_num = int(center_rest_endday.strftime("%w")) + 1
    event2_zurasu_num = youbi_zurashi(
        event2_gomi_rcur_start_youbi_num, kurikaesi_youbi_num
    )
    event2_gomi_rrule_start_date = center_rest_endday + timedelta(
        days=event2_zurasu_num
    )

    # event2_gomi_end_date = datetime.strptime(center_dates["休止終了日"], "%Y/%m/%d").date()
    event2_ical_rrule = copy(ical_rrule)
    event2_ical_rrule["until"] = GOMI_CALENER_END

    event2 = Event()

    event2.add("summary", name)
    event2.add("dtstart", event2_gomi_rrule_start_date)
    event2.add("dtend", event2_gomi_rrule_start_date + timedelta(days=1))
    event2.add("dtstamp", event2_gomi_rrule_start_date)
    event2.add("rrule", event2_ical_rrule)

    return [event1, event2]


def search_pattern(
    event_str: str,
) -> Tuple[Optional[str], Optional[Callable[[str, str], Event]]]:

    """
    ごみのカレンダーのカテゴリ書式をパースして、icalに必要な情報の生成を行う関数を返す

    ごみのカレンダーの定義フォーマット:https://github.com/codeforkanazawa-org/5374/blob/master/LOCALIZE.md
    """

    gomi_cal_paese_pattern_set = [
        (r"^[月火水木金土日]", gen_recurceve_event),
        (r"^[月火水木金土日]\d", gen_recurceve_event),
        (r"^[月火水木金土日]:", None),
        (r"^[月火水木金土日]\d:", None),
        (r"^\d{8}", gen_one_event),
    ]

    for pattern, gen_event_func in gomi_cal_paese_pattern_set:

        # 文字列をre.matchで先頭から当てる
        matched = re.match(pattern, event_str)
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
