"""年月日のデータを変換する"""
import datetime
import unicodedata
import re

class DateFormatter:
    """年月日データの変換を行う

    Attributes;
        __date:変換する日付データ
        start_reiwa:令和の元号開始年

    Methods:
        converted_datetime:XXXX年XX月XX日形式の日付をdatetimeに変換する
        convert_japanesecalendar:和暦をdatetimeに変換する

    """
    start_reiwa =  2019

    def __init__(self,date:str):
        self.__date = date

    def converted_datetime(self):
        """
        XXXX年XX月XX日形式の日付をdatetimeに変換する
        """
        pattern = r"(?P<year>[0-9]{4})年(?P<month>[0-9]{1,2})月(?P<day>[0-9]{1,2})日"

        redate = re.search(pattern,self.__date)

        # 正規表現に当てはまらない時はNoneを返す
        if redate is None:
            return

        return datetime.datetime(int(redate.group('year')),int(redate.group('month')),int(redate.group('day')))

    def convert_japanese_calendar(self):
        """
        和暦を西暦のdatetimeに変換
        """

        normalized_text = unicodedata.normalize("NFKC",self.__date)

        # 年月日抽出
        pattern = r"令和(?P<year>[0-9]{1,2}|元)年(?P<month>[0-9]{1,2})月(?P<day>[0-9]{1,2})日"
        date = re.search(pattern,normalized_text)

        if date is None:
            return

        if date.group("year") == "元":
            year = self.start_reiwa
        else:
            year = self.start_reiwa + int(date.group("year")) -1

        return datetime.datetime(year,int(date.group("month")),int(date.group("day")))
