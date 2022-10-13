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

def parse_funding_source_list_page(html):
    """"
    一覧画面をパースしてデータを取得する

    Parameters
    ----------
    html:string
        一覧画面のURL
    """

    soup = BeautifulSoup(html,'html.parser')

    return {
        'funding_source_url_list': [a["href"]for a in soup.select("table.hojyokin_case tbody tr td > a")]
    }

def crawl_funding_source_list_page(start_url):
    """"
    一覧ページをクロールして詳細ページのURLを全て取得する

    Parameters
    -----------
    start_url:string
        一覧画面のURL
    """

    print("Accessing TO {start_url}...")
    session = HTMLSession()

    response = session.get(start_url)

    response.html.render()

    time.sleep(8)

    page_data = parse_funding_source_list_page(response.html.html)
    funding_source_url_list = page_data["funding_source_url_list"]

    return funding_source_url_list

def parse_funding_source_detail(html,url):
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
    content = soup.select(".content p")

    print(soup)
    return {
        'title': soup.select_one(".content h1").get_text(),#補助金名
        'outline':soup.select_one(".content .datatable tbody tr td").get_text(),#概要
        'season':content[0].get_text(),#公募時期
        'rate':content[1].get_text(),#補助率
        'target':content[2].get_text(),#対象者
        'remarks':content[3].get_text(),#備考
        'url':url
    }

def crawl_funding_source_list_detail(url):
    """"
    詳細ページをクロールして補助金情報を取得する

    Parameters
    -----------
    url:string
        詳細ページのURL
    """

    # 詳細ページにアクセス
    print("Accessing to {url}")
    response = requests.get(url)
    response.raise_for_status()
    time.sleep(8)
    # HTMLからデータを取得する
    return parse_funding_source_detail(response.text,url)

def crawl_funding_source_add(start_url):
    """
    各サイトの補助金・融資情報をfirestoreに保存する

    Parameters
    ----------
    start_url:string
        一覧画面のURL
    """

    print("Start crawl!")

    funding_source_url_list = crawl_funding_source_list_page(start_url)

    db = firestore_connection()
    for funding_source_url in funding_source_url_list:
        funding_source_data = crawl_funding_source_list_detail(funding_source_url)
        doc = db.collection('MAFF_SUBSIDES')
        doc.add(funding_source_data)

    print("completed crawl!")


# 農林水産省の補助金ページへアクセス
crawl_funding_source_add("https://www.gyakubiki.maff.go.jp/appmaff/input/result.html?domain=M&tab=tab2&nen=A7&area=00")