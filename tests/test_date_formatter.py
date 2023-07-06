"""DateFormatterの単体テスト"""
import datetime
from main.date_formatter import DateFormatter

def test_converteddatetime_all_01():
    """年月日がXXXX年XX月XX日の値で揃っている"""
    assert DateFormatter('2023年01月01日').converted_datetime() == datetime.datetime(2023,1,1)

def test_converteddatetime_all_02():
    """年月日がXXXX年X月X日の値で揃っている"""
    assert DateFormatter('2023年1月1日').converted_datetime() == datetime.datetime(2023,1,1)

def test_converteddatetime_adonly():
    """西暦のみ渡されている"""
    assert DateFormatter('2023年').converted_datetime() is None

def test_converteddatetime_monthonly():
    """月のみ渡されている"""
    assert DateFormatter('01月').converted_datetime() is None

def test_converteddatetime_dayonly():
    """日だけ飲み渡されている"""
    assert DateFormatter('01日').converted_datetime() is None

def test_convertjapanesecalendar():
    """和暦がdatetimeに変換されている"""
    assert DateFormatter('令和2年12月31日').convert_japanese_calendar() == datetime.datetime(2020,12,31)

def test_convertjapanesecalendar_emnumber():
    """全角の数字を渡してもdatetimeに変換される"""
    assert DateFormatter('令和２年１２月３１日').convert_japanese_calendar() == datetime.datetime(2020,12,31)

def test_convertjapanesecalendar_yearandmonthonly():
    """年月のみ入力されている"""
    assert DateFormatter('12月31日').convert_japanese_calendar() is None

def test_convertjapanesecalendar_reiwaonly():
    """元号のみ渡されている"""
    assert DateFormatter('令和2年').convert_japanese_calendar() is None

def test_datesplit_starttoend():
    """XXXX年XX月XX日〜XXXX年XX月XX日の値が辞書型のstart_dateとend_dateに分かれる"""
    term_date = {
        'start_date':datetime.datetime(2023,1,1),
        'end_date':datetime.datetime(2023,1,31)
    }
    assert DateFormatter('2023年01月01日~2023年01月31日').date_split() == term_date

def test_datesplit_startonly():
    """開始日のみ入力"""
    term_date = {
        'start_date':datetime.datetime(2023,1,1),
        'end_date':datetime.datetime(2000,1,1)
    }
    assert DateFormatter('2023年01月01日〜').date_split() == term_date

def test_datesplit_endonly():
    """終了日のみ入力"""
    term_date = {
    'start_date':datetime.datetime(2000,1,1),
    'end_date':datetime.datetime(2023,1,31)
    }
    assert DateFormatter('~2023年01月31日').date_split() == term_date

def test_datesplit_dateonly():
    """~がない"""
    assert DateFormatter('2023年01月31日').date_split() is None