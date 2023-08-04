"""
セレクターを指定して、html内からリンクの取得を行う
備考：
makeとset_next_urlのbase_urlは取得するリンクが相対参照している時、
絶対参照で取得できるように補完するもの
"""
from bs4 import BeautifulSoup
from urllib.parse import urljoin
class UrlListGenerator:
    """html内のリンクの取得を行う"""

    def __init__(self):
        self.__url_list = []
        self.__next_url = ""

    def make(self,source:str,url_selector:str,base_url = ""):
        """html内のリンクのリストを配列に格納"""
        soup = BeautifulSoup(source,'html.parser')
        for a in soup.select(url_selector):

            if base_url:
                self.__url_list.append(urljoin(base_url,a['href']))
            else:
                self.__url_list.append(a['href'])

    def set_next_url(self,source:str,next_url_selector:str="",base_url:str = ""):
        """htmlから取得したリンクを変数にセット"""
        if not next_url_selector:
            return
        soup = BeautifulSoup(source,'html.parser')
        next_url = soup.select_one(next_url_selector)

        if base_url and next_url:
            self.__next_url = urljoin(base_url,next_url['href'])
        else:
            try:
                self.__next_url = next_url['href']
            except TypeError:
                self.__next_url = ""


    def get_next_url(self):
        """メンバ変数next_urlを取得"""
        return self.__next_url

    def get_url_list(self):
        """メンバ変数url_listを取得"""
        return self.__url_list
