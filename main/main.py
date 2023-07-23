import time
import datetime
from urllib.parse import urljoin
import const
import requests
import logging
import os
import traceback
from bs4 import BeautifulSoup
import chromedriver_binary
import sys
from maff_public_offering import MaffPublicOffering
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from requests_html import HTMLSession
from date_formatter import DateFormatter
from firestore_collections_delete import FirestoreCollectionsDelete
from firestore_collections_save import FirestoreCollectionsSave
from html_source_getter import HtmlSourceGetter

def parse_funding_source_list_page(html,source_name):
    """"
    一覧画面をパースしてデータを取得する

    Parameters
    ----------
    html:string
        一覧画面のURL
    """
    soup = BeautifulSoup(html,'html.parser')

    # TODO:関数を作成し処理を外に出すか検討
    # JNEX21から取得するリンクが相対リンクのため他と処理を分ける
    next_page_link = None
    if source_name == const.JNET21_SUBSIDES_AND_FINANCING:
        selector = "main#contents article div.HL-result ul.HL-resultList li div.title-meta > a"
        next_page_link = soup.select_one("div.HL-result .HL-pagenation .nextBox li > a[href]")
        return {
            'funding_source_url_list': [urljoin('https://j-net21.smrj.go.jp',a["href"])for a in soup.select(selector)],
            'next_page_link': next_page_link["href"] if next_page_link else None
        }

    if source_name == const.MAFF_SUBSIDES:
        selector = "table.hojyokin_case tbody tr td > a"
    elif source_name == const.MAFF_FINANCING:
        selector = "table.yushi_case tbody tr td > a"

    return {
        'funding_source_url_list': [a["href"]for a in soup.select(selector)],
        'next_page_link': next_page_link["href"] if next_page_link else None
    }
from url_list_generator import UrlListGenerator
from jnet21_article_detail import Jnet21ArticleDetail

def crawl_funding_source_list_page(source_name,source_url):
    """"
    一覧ページをクロールして詳細ページのURLを全て取得する

    Parameters
    -----------
    start_url:string
        一覧画面のURL
    """

    logging.info(f"Accessing TO {source_url}...")
    if source_name == const.JNET21_SUBSIDES_AND_FINANCING:
        # JNET21はフォームのクリックにseleniumを使っているため処理を分ける
        click_target = [
            '//*[@id="categorySelect"]/div/label[1]',#「補助金・助成金・融資」
            '//*[@id="searchForm"]/div[9]/button[1]' #「検索実行」
        ]
        html_source_getter = HtmlSourceGetter(source_url)
        page_source = html_source_getter.clicked_html(click_target)
    else:
        session = HTMLSession()

        response = session.get(source_url)

        response.html.render(timeout=20)
        page_source = response.html.html

    time.sleep(8)

    page_data = parse_funding_source_list_page(page_source,source_name)
    funding_source_url_list = page_data["funding_source_url_list"]

    while page_data["next_page_link"]:
        # MEMO:現状JNET21のみこのループに入るためbase_urlはここに直書き
        base_url = "https://j-net21.smrj.go.jp/"
        logging.info(f"Accessing TO {urljoin(base_url,page_data['next_page_link'])}")
        page_source = requests.get(urljoin(base_url,page_data["next_page_link"])).text
        time.sleep(8)
        page_data = parse_funding_source_list_page(page_source,source_name)
        funding_source_url_list += page_data["funding_source_url_list"]

    return funding_source_url_list

def parse_funding_source_detail(source_name,html,url):
    """
    詳細ページの情報を取得する

    Parameters
    -----------
    html:string
        詳細ページのhtml
    url:string
        詳細ページのURL
    """

    soup = BeautifulSoup(html,'html.parser')

    #TODO:関数を作成し処理を外に出すか検討
    if source_name in [const.MAFF_SUBSIDES,const.MAFF_FINANCING]:
        selector = ".content p"
        content = soup.select(selector)


    if source_name == const.MAFF_SUBSIDES:
        # 農林水産省補助金情報
        return {
            'title': soup.select_one(".content h1").get_text(),#補助金名
            'outline':soup.select_one(".content .datatable tbody tr td").get_text(),#概要
            'season':content[0].get_text(),#公募時期
            'rate':content[1].get_text(),#補助率
            'target':content[2].get_text(),#対象者
            'remarks':content[3].get_text(),#備考
            'url':url
        }
    elif source_name == const.MAFF_FINANCING:
        # 農林水産省融資情報
        return {
            'title': soup.select_one(".content h1").get_text(),#融資名
            'outline':soup.select_one(".content .datatable tbody tr td").get_text(),#概要
            'target': content[0].get_text(),#公募時期,
            'interest': content[1].get_text(),#公募時期,
            'borrowing_limit': content[2].get_text(),#公募時期,
            'term_of_redemption':content[3].get_text(),#公募時期:
            'remarks': content[4].get_text(),#公募時期,
            'url':url
        }
    elif source_name == const.JNET21_SUBSIDES_AND_FINANCING:
        #JNET21補助金公募情報

        recruitment_period = soup.select_one("article div.section .HL-desc dd")
        # 融資情報で募集期間がない場合があるためNoneで弾く
        # firestoreで設定している型の関係でNoneを受け付けないためとりあえずの値を入れる
        if recruitment_period is None:
            before_marge_date = {
                "start_date":datetime.datetime(2000,1,1),
                "end_date":datetime.datetime(2000,1,1)
            }
        else:
            before_marge_date = DateFormatter(recruitment_period).date_split()

        before_add_data_to_firestore = {
            'industry':'',#業種
            'executing_agency':'',#実施機関
            'area':'',#地域
            'type':''#種類
        }
        for hldesc in soup.select('article section .HL-desc'):
            hldesc_item_label = hldesc.select_one('dt').get_text()
            hldesc_item_data = hldesc.select_one('dd').get_text()
            try:
                # 取得しない項目はkeyに存在しないためエラーさせている
                key = const.JNET21_FIRESTORE_KEY[hldesc_item_label]
                before_add_data_to_firestore[key] = hldesc_item_data
            except:
                continue

        merge_add_data_to_firestore = {
            'title':soup.select_one("article h1").get_text(),
            'executing_agency_info':soup.select_one("article section p").get_text(),
            'detail_url_name':soup.select_one("article section ul li a").get_text(),
            'detail_url':soup.select_one("article section ul li > a[href]").get('href')
        }

        return dict(
            **before_marge_date,
            **before_add_data_to_firestore,
            **merge_add_data_to_firestore
            )

def crawl_funding_source_list_detail(source_name,url):
    """"
    詳細ページをクロールして補助金情報を取得する

    Parameters
    -----------
    url:string
        詳細ページのURL
    """

    # 詳細ページにアクセス
    logging.info(f"Accessing to {url}")
    response = requests.get(url)
    # ページが存在しない場合がある
    if response.status_code != 200:
        return False

    response.raise_for_status()
    time.sleep(8)
    # HTMLからデータを取得する
    return parse_funding_source_detail(source_name,response.text,url)

def crawl_funding_source_add(source_name,source_url):
    """
    各サイトの補助金・融資情報をfirestoreに保存する

    Parameters
    ----------
    start_url:string
        一覧画面のURL
    """

    logging.basicConfig(
        filename="../log.txt",
        level=logging.INFO,
        format="%(asctime)s - %(message)s",
        datefmt="%m/%d/%Y %I:%M:%S %p"
    )
    logging.info("Start crawl")
    try:
        FirestoreCollectionsDelete().all_clear()
        if source_name in [const.MAFF_SUBSIDES,const.MAFF_FINANCING,const.JNET21_SUBSIDES_AND_FINANCING]:
            funding_source_url_list = crawl_funding_source_list_page(source_name,source_url)
            for funding_source_url in funding_source_url_list:
                funding_source_data = crawl_funding_source_list_detail(source_name,funding_source_url)
                if not funding_source_data: continue
                FirestoreCollectionsSave().add(funding_source_data,source_name)

        elif source_name == const.MAFF_PUBLIC_OFFERING:
            public_offering = MaffPublicOffering()
            public_offering.make()

            for add_data in public_offering.get_public_offering().values():
                FirestoreCollectionsSave().add(add_data,source_name)
    except Exception as err_msg:
        logging.error("エラーが発生しました。",exc_info=True)
        logging.error(err_msg)
    logging.info("completed crawl!")

source_names = {
    const.MAFF_SUBSIDES:"https://www.gyakubiki.maff.go.jp/appmaff/input/result.html?domain=M&tab=tab2&nen=A7&area=00",
    const.MAFF_FINANCING:"https://www.gyakubiki.maff.go.jp/appmaff/input/result.html?domain=M&tab=tab3&riyo=MA%2CMB%2CMC%2CMD%2CME%2CMF%2CMG&area=00",
    const.MAFF_PUBLIC_OFFERING:"https://www.maff.go.jp/j/supply/hozyo/",
    const.JNET21_SUBSIDES_AND_FINANCING:"https://j-net21.smrj.go.jp/snavi/articles"
}
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
            source = requests.get(url_list_generator.get_next_url()).text
            url_list_generator.make(source,"main#contents article div.HL-result ul.HL-resultList li div.title-meta > a")
            url_list_generator.set_next_url(page_source,"div.HL-result .HL-pagenation .nextBox li > a[href]",'https://j-net21.smrj.go.jp')

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

if __name__ == "__main__":
    main()