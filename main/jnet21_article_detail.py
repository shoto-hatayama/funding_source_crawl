"""
jnet21の記事詳細を管理
使い方：
１、set_sourceでsourceを取得
２、retrive_articleで項目を取得
"""
import logging
import requests
import time
import datetime
from date_formatter import DateFormatter
from requests.exceptions import HTTPError
from bs4 import BeautifulSoup
class Jnet21ArticleDetail:
    """jnet21の記事詳細を取得するクラス"""

    def __init__(self):
        self.__source = ""
        self.__selector = "article div.section .HL-desc dd"
        self.__hldesc_key = {
            '業種':'industry',
            '実施機関':'executing_agency',
            '地域':'area',
            '種類':'type'
        }
        self.__article = {
            'title':'',#タイトル
            'executing_agency_info':'',#実施機関からのお知らせ
            'detail_url_name':'',#詳細urlの名前
            'detail_url':'',#詳細url
            'industry':'',#業種
            'executing_agency':'',#実施機関
            'area':'',#地域
            'type':'',#種類
            "start_date":datetime.datetime(2000,1,1),#開始時期
            "end_date":datetime.datetime(2000,1,1)#終了時期
        }


    def set_source(self, source_url):
        """アクセス先のhtmlを取得"""
        logging.info(f"Accessing to {source_url}")
        try:
            time.sleep(8)
            response = requests.get(source_url)
            response.raise_for_status()

            self.__source = response.text
        except HTTPError:
            logging.info("200以外のステータスが返されました。")

    def retrive_article(self):
        """記事の詳細を取得する"""

        soup = BeautifulSoup(self.__source,'html.parser')
        recruitment_period = soup.select_one(self.__selector)

        # 募集期間は公募のみの項目のため募集期間がない時は値を書き換えない
        if recruitment_period is not None:
            self.__article.update(DateFormatter(recruitment_period.text).date_split())

        for hldesc in soup.select('article section .HL-desc'):
            hldesc_item_label = hldesc.select_one('dt').get_text()
            hldesc_item_data = hldesc.select_one('dd').get_text()
            try:
                # 取得しない項目はkeyに存在しないためエラーさせている
                key = self.__hldesc_key[hldesc_item_label]
                self.__article[key] = hldesc_item_data
            except Exception:
                continue

        self.__article.update({
            'title':soup.select_one("article h1").get_text(),
            'executing_agency_info':soup.select_one("article section p").get_text(),
            'detail_url_name':soup.select_one("article section ul li a").get_text(),
            'detail_url':soup.select_one("article section ul li > a[href]").get('href')
        })

    def get_article(self):
        """メンバ変数のarticleを取得"""
        return self.__article

    def is_not_source(self):
        """記事が取得できていないかチェック"""
        if self.__source:
            return False
        else:
            return True