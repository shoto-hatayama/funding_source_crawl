"""公募情報のクロール"""
import logging
import datetime
from date_formatter import DateFormatter
from bs4 import BeautifulSoup
from requests_html import HTMLSession
from urllib.parse import urljoin

class MaffPublicOffering:
    """農林水産省の公募情報を取得する"""
    __source_url = "https://www.maff.go.jp/j/supply/hozyo/"
    __offerring_collection_key = [
        'begin_date',
        'end_date',
        'public_offering_name'
    ]
    __public_offering = {}

    def __init__(self):

        logging.info("Accessing TO %s",self.__source_url)

        session = HTMLSession()

        self.__response = session.get(self.__source_url)

        self.__response.html.render()

    def make(self):
        """農林水産省のサイトにアクセスし、取得した値をdict型で格納"""

        soup = BeautifulSoup(self.__response.html.html,'html.parser')
        tbody = soup.select_one("table.datatable tbody")
        for tr_key,tr_context in enumerate(tbody.select("tr")):

            add_tr = {}
            for td_key,td_context in enumerate(tr_context.select("td")):

                if self.__offerring_collection_key[td_key] == "end_date" and self.__is_deadline_passed(td_context):
                    # 前回のループでadd_trにbegin_dateが入ったままのため、ここで初期化する
                    add_tr.clear()
                    break

                if self.__is_href_property(td_context):
                    add_tr['url'] = urljoin(self.__source_url,td_context.select_one("td a[href]")['href'])

                if self.__offerring_collection_key[td_key] == "public_offering_name":
                    add_tr[self.__offerring_collection_key[td_key]] = td_context.text
                else:
                    add_tr[self.__offerring_collection_key[td_key]] = DateFormatter(td_context.text).convert_japanese_calendar()

            # trのヘッダー(th)がある場合、空欄を追加しないように弾く
            if not add_tr:
                continue

            self.__public_offering[tr_key] = add_tr

    def get_public_offering(self):
        """処理結果を持つメンバ変数を返す"""
        return self.__public_offering

    def __is_deadline_passed(self,td_context):
        """期限日を過ぎているかチェック"""
        end_date = DateFormatter(td_context.text).convert_japanese_calendar()
        now = datetime.datetime.now()
        if  end_date < now :
            return True

        return False

    def __is_href_property(self,td_context):
        """href属性が存在するかチェック"""
        detail_link = td_context.select_one("td a[href]")
        if detail_link is None:
            return False

        return True
