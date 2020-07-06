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

# センター情報を紐づけて、ごみ収集しない日時を間に入れる

# まず地区ごとにグルーピングする


# ごみの項目を、パーサーで読ませて、icalに渡すためのデータにする: icalのデータ形式を見直す

# カレンダーオブジェクト生成

cal = Calendar()
cal.add("prodid", "-//fuji-5374//fuji-5374//JP")
cal.add("version", "2.0")

# 繰り返しイベントは繰り返しイベントとして処理
# そうでない数字のみはdateな処理

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