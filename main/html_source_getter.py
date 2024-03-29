"""seleniumを使ってページ内の対象をクリックする"""
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import logging

class HtmlSourceGetter:
    """クリックした対象のhtnlを取得する"""
    __driver_path = 'main/chromedriver'

    def __init__(self,url):
        options = Options()
        options.add_argument('--disable-gpu')#GPUハードウェアアクセラレーションを無効
        options.add_argument('--disable-extensions')#全ての拡張機能を無効
        options.add_argument('--proxy-server="direct://"')#プロキシ経由せず直接接続
        options.add_argument('--proxy-bypass-list=*')#プロキシサーバー経由しない
        options.add_argument('--start-maximized')#初期のウィンドウサイズ最大化
        options.add_argument('--headless')#ヘッドレスモードで起動

        self.__driver = webdriver.Chrome(executable_path=self.__driver_path,chrome_options=options)
        self.__driver.get(url)

    def clicked_html(self,xpath: list,wait_tag = "body"):
        """クリックする順番をxpathで指定してhtmlを取得"""

        try:
            # フォームの「補助金・助成金・融資」を選択
            for val in xpath:
                element = self.__driver.find_element_by_xpath(val)
                element.click()

            # 取得先のページが非同期のため、要素が取得できる状態になるまで待つ
            WebDriverWait(self.__driver,10).until(
                EC.presence_of_element_located((By.TAG_NAME,"body"))
            )
            return self.__driver.page_source
        except NoSuchElementException as error_msg:
            print(error_msg)
            logging.error(error_msg)
        finally:
            self.__driver.quit()
