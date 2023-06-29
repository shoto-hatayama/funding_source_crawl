from main.date_formatter import DateFormatter
import datetime

def test_converteddatetime_all_01():
    # 年月日がXXXX年XX月XX日の値で揃っている
    assert DateFormatter('2023年01月01日').converted_datetime() == datetime.datetime(2023,1,1)

def test_converteddatetime_all_02():
    # 年月日がXXXX年X月X日の値で揃っている
    assert DateFormatter('2023年1月1日').converted_datetime() == datetime.datetime(2023,1,1)

def test_converteddatetime_adonly():
    # 西暦のみ渡されている
    assert DateFormatter('2023年').converted_datetime() == None

def test_converteddatetime_monthonly():
    # 月のみ渡されている
    assert DateFormatter('01月').converted_datetime() == None

def test_converteddatetime_dayonly():
    # 日だけ飲み渡されている
    assert DateFormatter('01日').converted_datetime() == None