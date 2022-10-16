import time

import const
import requests
from bs4 import BeautifulSoup
from requests_html import HTMLSession
from firebase_admin import firestore
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db


def firestore_connection():
    """
    firestoreの接続設定
    """

    JSON_PATH = const.FIREBASE_JSON_NAME
    cred = credentials.Certificate(JSON_PATH)
    firebase_admin.initialize_app(cred)

    return firestore.client()

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
    if source_name == const.MAFF_SUBSIDES:
        selector = "table.hojyokin_case tbody tr td > a"
    elif source_name == const.MAFF_FINANCING:
        selector = "table.yushi_case tbody tr td > a"

    return {
        'funding_source_url_list': [a["href"]for a in soup.select(selector)]#切り替え必要
    }

def crawl_funding_source_list_page(source_name,source_url):
    """"
    一覧ページをクロールして詳細ページのURLを全て取得する

    Parameters
    -----------
    start_url:string
        一覧画面のURL
    """

    print(f"Accessing TO {source_url}...")
    session = HTMLSession()

    response = session.get(source_url)

    response.html.render()

    time.sleep(8)

    page_data = parse_funding_source_list_page(response.html.html,source_name)
    funding_source_url_list = page_data["funding_source_url_list"]

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

    #TODO:関数を作成し処理を外に出すか検討
    if source_name in [const.MAFF_SUBSIDES,const.MAFF_FINANCING]:
        selector = ".content p"

    soup = BeautifulSoup(html,'html.parser')
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

def crawl_funding_source_list_detail(source_name,url):
    """"
    詳細ページをクロールして補助金情報を取得する

    Parameters
    -----------
    url:string
        詳細ページのURL
    """

    # 詳細ページにアクセス
    print(f"Accessing to {url}")
    response = requests.get(url)
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

    print("Start crawl!")

    funding_source_url_list = crawl_funding_source_list_page(source_name,source_url)

    db = firestore_connection()
    for funding_source_url in funding_source_url_list:
        funding_source_data = crawl_funding_source_list_detail(source_name,funding_source_url)
        doc = db.collection(source_name)
        doc.add(funding_source_data)

    print("completed crawl!")


source_names = {
    const.MAFF_SUBSIDES:"https://www.gyakubiki.maff.go.jp/appmaff/input/result.html?domain=M&tab=tab2&nen=A7&area=00",
    const.MAFF_FINANCING:"https://www.gyakubiki.maff.go.jp/appmaff/input/result.html?domain=M&tab=tab3&riyo=MA%2CMB%2CMC%2CMD%2CME%2CMF%2CMG&area=00"
}

for source_name,source_url in source_names.items():
    crawl_funding_source_add(source_name,source_url)
