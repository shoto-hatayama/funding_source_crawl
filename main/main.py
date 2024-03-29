import time
import requests
import logging
import traceback
from requests_html import HTMLSession
from bs4 import BeautifulSoup
import sys
from maff_public_offering import MaffPublicOffering
from firestore_collections_delete import FirestoreCollectionsDelete
from firestore_collections_save import FirestoreCollectionsSave
from html_source_getter import HtmlSourceGetter
from url_list_generator import UrlListGenerator
from jnet21_article_detail import Jnet21ArticleDetail
from maff_subsides_article_detail import MaffSubsidesArticleDetail
from maff_financing_article_detail import MaffFinancingArticleDetail

def main():
    logging.basicConfig(
        filename="./log.txt",
        level=logging.INFO,
        format="%(asctime)s - %(message)s",
        datefmt="%m/%d/%Y %I:%M:%S %p"
    )

    FirestoreCollectionsDelete().all_clear()

    exec_public_offerring()
    exec_jnet21()
    exec_maff_subsidy()
    exec_maff_financing()

def exec_public_offerring():
    """農林水産省の公募取得用関数"""
    logging.info("農林水産省から公募内容を取得する処理を開始します。")
    collection_name = "MAFF_PUBLIC_OFFERING"
    try:
        public_offering = MaffPublicOffering()
        public_offering.make()

        for val in public_offering.get_public_offering().values():
            FirestoreCollectionsSave().add(val,collection_name)
        logging.info("処理が正常に終了しました。")
    except Exception:
        logging.error(traceback.format_exc())
        sys.exit()

def exec_jnet21():
    """jnet21の補助金・融資取得用関数"""
    logging.info("Jnet21から補助金・融資内容を取得する処理を開始します。")
    collection_name = "JNET21_SUBSIDES_AND_FINANCING"
    click_target = [
            '//*[@id="categorySelect"]/div/label[1]',#「補助金・助成金・融資」
            '//*[@id="searchForm"]/div[9]/button[1]' #「検索実行」
        ]
    source_url = "https://j-net21.smrj.go.jp/snavi/articles"
    base_url = 'https://j-net21.smrj.go.jp'
    url_selector = 'main#contents article div.HL-result ul.HL-resultList li div.title-meta > a'
    next_url_selector = 'div.HL-result .HL-pagenation .nextBox li > a[href]'

    try:
        html_source_getter = HtmlSourceGetter(source_url)
        page_source = html_source_getter.clicked_html(click_target)

        url_list_generator = UrlListGenerator()
        url_list_generator.make(page_source,url_selector,base_url)
        url_list_generator.set_next_url(page_source,next_url_selector,base_url)
        while url_list_generator.get_next_url():
            time.sleep(8)
            logging.info(f"Accessing to {url_list_generator.get_next_url()}")
            source = requests.get(url_list_generator.get_next_url()).text
            url_list_generator.make(source,url_selector,base_url)
            url_list_generator.set_next_url(source,next_url_selector,base_url)

        article_detail = Jnet21ArticleDetail()
        for article_url in url_list_generator.get_url_list():
            article_detail.set_source(article_url)
            if article_detail.is_not_source():
                continue
            article_detail.retrive_article()
            FirestoreCollectionsSave().add(article_detail.get_article(),collection_name)
        logging.info("処理が正常に終了しました。")
    except Exception:
        logging.error(traceback.format_exc())
        sys.exit()

def exec_maff_subsidy():
    """農林水産省の補助金取得用関数"""
    logging.info("農林水産省から補助金内容を取得する処理を開始します。")

    source_url = "https://www.gyakubiki.maff.go.jp/appmaff/input/result.html?domain=M&tab=tab2&nen=A9&area=00"
    url_selector = "table.hojyokin_case tbody tr td > a"
    collection_name = "MAFF_SUBSIDES"

    try:
        session = HTMLSession()
        response = session.get(source_url)
        response.html.render(timeout=20)
        page_source = response.html.html

        url_list_generator = UrlListGenerator()
        url_list_generator.make(page_source,url_selector)

        article_detail = MaffSubsidesArticleDetail()
        for article_url in url_list_generator.get_url_list():
            article_detail.set_source(article_url)
            # リンクが切れている時の対策
            if article_detail.is_not_source():
                continue
            article_detail.retrive_article()
            FirestoreCollectionsSave().add(article_detail.get_article(),collection_name)
        logging.info("処理が正常に終了しました。")

    except Exception:
        logging.error(traceback.format_exc())
        sys.exit()

def exec_maff_financing():
    """農林水産省の融資取得用関数"""
    logging.info("農林水産省から融資内容を取得する処理を開始します。")

    source_url = "https://www.gyakubiki.maff.go.jp/appmaff/input/result.html?domain=M&tab=tab3&riyo=MA%2CMB%2CMC%2CMD%2CME%2CMF%2CMG&area=00"
    url_selector = "table.yushi_case tbody tr td > a"
    collection_name = "MAFF_FINANCING"

    try:
        session = HTMLSession()
        response = session.get(source_url)
        response.html.render(timeout=20)
        page_source = response.html.html

        url_list_generator = UrlListGenerator()
        url_list_generator.make(page_source,url_selector)

        article_detail = MaffFinancingArticleDetail()
        for article_url in url_list_generator.get_url_list():
            article_detail.set_source(article_url)
            # リンクが切れている時の対策
            if article_detail.is_not_source():
                continue
            article_detail.retrive_article()
            FirestoreCollectionsSave().add(article_detail.get_article(),collection_name)
        logging.info("処理が正常に終了しました。")

    except Exception:
        logging.error(traceback.format_exc())
        sys.exit()

if __name__ == "__main__":
    main()