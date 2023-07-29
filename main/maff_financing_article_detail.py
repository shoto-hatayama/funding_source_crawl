"""
農林水産省の融資の詳細を管理
使い方：
１、set_sourceでsourceを取得
２、retrive_articleで項目を取得
"""
import logging
import time
import requests
from requests.exceptions import HTTPError
from bs4 import BeautifulSoup
class MaffFinancingArticleDetail:
    """農林水産省の記事詳細を取得するクラス"""

    def __init__(self):
        self.__selector = ".content p"
        self.__article = {
            'title': "",#融資名
            'outline':"",#概要
            'target': "",#対象者,
            'interest': "",#金利,
            'borrowing_limit': "",#借入限度額,
            'term_of_redemption':"",#償還期限:
            'remarks': "",#備考,
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
            'title': soup.select_one(".content h1").get_text(),#融資名
            'outline':soup.select_one(".content .datatable tbody tr td").get_text(),#概要
            'target': content[0].get_text(),#対象者,
            'interest': content[1].get_text(),#金利,
            'borrowing_limit': content[2].get_text(),#借入限度額,
            'term_of_redemption':content[3].get_text(),#償還期限:
            'remarks': content[4].get_text(),#備考,
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