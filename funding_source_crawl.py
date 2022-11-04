import time

import unicodedata
import re
import datetime
from urllib.parse import urljoin
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

def japanese_colendar_to_ad(text):
    """
    和暦を西暦のdatetimeに変換数

    Parameters
    -----------
    test:string
        和暦の年月日
    -----------
    """

    # 正規化
    normalized_text = unicodedata.normalize("NFKC",text)

    # 年月日抽出
    pattern = r"(?P<era>{eraList})(?P<year>[0-9]{{1,2}}|元)年(?P<month>[0-9]{{1,2}})月(?P<day>[0-9]{{1,2}})日".format(eraList="|".join( const.ERADICT.keys()))
    date = re.search(pattern,normalized_text)

    # 秀出できなければ正規化したテキストを返す
    if date is None:
        return normalized_text

    # 年を変換
    for era,start_year in const.ERADICT.items():
        if date.group("era") == era:
            if date.group("year") == "元":
                year = start_year
            else:
                year = start_year + int(date.group("year")) -1

    return datetime.datetime(year,int(date.group("month")),int(date.group("day")))

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

    db = firestore_connection()
    if source_name in [const.MAFF_SUBSIDES,const.MAFF_FINANCING]:
        funding_source_url_list = crawl_funding_source_list_page(source_name,source_url)
        for funding_source_url in funding_source_url_list:
            funding_source_data = crawl_funding_source_list_detail(source_name,funding_source_url)
            doc = db.collection(source_name)
            doc.add(funding_source_data)
    elif source_name == const.MAFF_PUBLIC_OFFERING:
        public_offering_list = crawl_public_offering_list(source_url)
        for public_offering_data in public_offering_list.values():
            doc = db.collection(source_name)
            doc.add(public_offering_data)

    print("completed crawl!")

def crawl_public_offering_list(source_url):
    """
     公募ページから開始日・終了日・公募名・urlを取得

     Parametrers
     -----------
     source_url
        ページのURL
    """

    print(f"Accessing TO {source_url}...")
    session = HTMLSession()

    response = session.get(source_url)

    response.html.render()

    time.sleep(8)

    soup = BeautifulSoup(response.html.html,'html.parser')

    base_url = "https://www.maff.go.jp/j/supply/hozyo/"

    crawl_data = []
    for tr in soup.select("table.datatable tbody tr"):

        add_crawl_data ={}
        index = 0
        for val in tr.select("td"):

            # frestore保存用の項目作成と和暦の変換
            add_crawl_data[const.OFFERRING_COLLECTION_KEY[index]] = japanese_colendar_to_ad(val.text)
            # print(add_crawl_data)
            # sys.exit()

            # hrefが存在するタグの場合のみリンク作成
            detail_link = val.select_one("td a[href]")
            if detail_link :
                # 公募詳細URLの作成
                add_crawl_data['url'] = urljoin(base_url,detail_link['href'])

            index +=1

        # 空の配列を追加しない
        if not add_crawl_data:
            continue

        # 辞書型の場合、階層作って保存が複雑になるため、list型に保存
        crawl_data.append(add_crawl_data)

    after_crawl_data = {}
    for key,before_crawl_data in enumerate(crawl_data) :

        # 不要な公募名の情報が取得されていれば処理を抜ける
        if type(before_crawl_data['end_date']) is str: break

        # 期限内のものだけ取得
        if before_crawl_data["end_date"] > datetime.datetime.today():
            after_crawl_data[key] = before_crawl_data

    return after_crawl_data

source_names = {
    const.MAFF_SUBSIDES:"https://www.gyakubiki.maff.go.jp/appmaff/input/result.html?domain=M&tab=tab2&nen=A7&area=00",
    const.MAFF_FINANCING:"https://www.gyakubiki.maff.go.jp/appmaff/input/result.html?domain=M&tab=tab3&riyo=MA%2CMB%2CMC%2CMD%2CME%2CMF%2CMG&area=00",
    const.MAFF_PUBLIC_OFFERING:"https://www.maff.go.jp/j/supply/hozyo/"
}

for source_name,source_url in source_names.items():
    crawl_funding_source_add(source_name,source_url)
