#encoding:utf-8

from icalendar import Calendar, Event
import pytz
from datetime import datetime

# CSVファイルをパースする

import csv

# センター情報
center_csv_list = None
with open("./data/center.csv", encoding="utf-8") as center_csv_file:
    center_csv_file = list(csv.DictReader(center_csv_file))
        
# areadaysを読み込む
areadays_csv_file = None
with open("./data/areadays.csv", encoding="utf-8") as areadays_csv_file:
    areadays_csv_file = list(csv.DictReader(areadays_csv_file))

pattern_list = list()
# センター情報を紐づけて、ごみ収集しない日時を間に入れる

# まず地区ごとにグルーピングする

# 繰り返しは、範囲指定ができるといい。カレンダー側のプロパティなのかイベント側なのかは不明
# - 繰り返しイベントは毎週＊曜日 のみ 何時から何時までの指定が可能かを考える）

# パターンごと, イベントをひとつづつ作る。繰り返しは一番上でいいかな


# ごみの項目を、パーサーで読ませて、icalに渡すためのデータにする: icalのデータ形式を見直す

# カレンダーオブジェクト生成: パターンごとに生成

for pattern in pattern_list:
    cal = Calendar()
    cal.add("prodid", "-//fuji-5374//fuji-5374//JP")
    cal.add("version", "2.0")

    # 各ごみ日時情報をイベントに変換

    # icalで必要なデータは
    # - そのごみの日付: 終日は時間入れないでやるらしい-> googleは時間ありで0時~0字と表現 
    #   - event.add("dtstart", datetime(2020,7,10,0,0,0,tzinfo=pytz.timezone("Asia/Tokyo"))) 
    #   - event.add("dtend", datetime(2020,7,11,0,0,0,tzinfo=pytz.timezone("Asia/Tokyo")))  
    # - ごみの種類の日: event.add("summary", "日本語サマリー")                                          
    # - 繰り返しイベントは毎週＊曜日 のみ 何時から何時までの指定が可能かを考える）
    #   - 
    # - そのほか: icalでスケジュールを作ったスタンプevent.add("dtstamp", datetime(2020,7,10,0,0,0,tzinfo=pytz.timezone("Asia/Tokyo"))) 

    # センターの締まっている時間を考慮する
    # - もしその時間にイベントを作ろうとしたら消す（繰り返しイベント的な物の範囲ができるか


    # icsファイルに保存