"""年月日のデータを変換する"""
import datetime
import re

class DateFormatter:
    """年月日データの変換を行う

    Attributes;
        __date:変換する日付データ

    Methods:
        converted_datetime:XXXX年XX月XX日形式の日付をdatetimeに変換する

    """
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