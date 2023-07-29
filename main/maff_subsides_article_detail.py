"""
農林水産省の補助金の詳細を管理
使い方：
１、set_sourceでsourceを取得
２、retrive_articleで項目を取得
"""
import logging
import time
import requests
from requests.exceptions import HTTPError
from bs4 import BeautifulSoup
class MaffSubsidesArticleDetail:
    """農林水産省の記事詳細を取得するクラス"""

    def __init__(self):
        self.__selector = ".content p"
        self.__article = {
            'title': "",#補助金名
            'outline':"",#概要
            'season':"",#公募時期
            'rate':"",#補助率
            'target':"",#対象者
            'remarks':"",#備考
            'url':""
        }

    def set_source(self,source_url):
        """アクセス先のhtmlを取得"""
        logging.info(f"Accessing to {source_url}")
        try:
            time.sleep(8)
            response = requests.get(source_url)
            response.raise_for_status()

            self.__source = response.text
            self.__url = source_url
        except HTTPError:
            logging.info("200以外のステータスが返されました。")


    def retrive_article(self):
        """記事の詳細を取得する"""
        soup = BeautifulSoup(self.__source,'html.parser')
        content = soup.select(self.__selector)

        self.__article.update({
            'title': soup.select_one(".content h1").get_text(),#補助金名
            'outline':soup.select_one(".content .datatable tbody tr td").get_text(),#概要
            'season':content[0].get_text(),#公募時期
            'rate':content[1].get_text(),#補助率
            'target':content[2].get_text(),#対象者
            'remarks':content[3].get_text(),#備考
            'url':self.__url
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