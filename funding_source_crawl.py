import time
import unicodedata
import re
import datetime
from urllib.parse import urljoin
import const
import requests
import logging
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
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

    return firestore.client().from_service_account_json(JSON_PATH)

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

    logging.info(f"Accessing TO {source_url}...")
    if source_name == const.JNET21_SUBSIDES_AND_FINANCING:
        # JNET21はフォームのクリックにseleniumを使っているため処理を分ける
        click_target = [
            '//*[@id="categorySelect"]/div/label[1]',#「補助金・助成金・融資」
            '//*[@id="searchForm"]/div[9]/button[1]' #「検索実行」
        ]
        page_source = source_of_page_clicked(source_url,click_target)
    else:
        session = HTMLSession()

        response = session.get(source_url)

        response.html.render()
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
    elif source_name == const.JNET21_SUBSIDES_AND_FINANCING:
        #JNET21補助金公募情報

        recruitment_period = soup.select_one("article div.section .HL-desc dd")
        before_marge_date = date_split(recruitment_period)

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
        filename="log.txt",
        level=logging.INFO,
        format="%(asctime)s - %(message)s",
        datefmt="%m/%d/%Y %I:%M:%S %p"
    )
    logging.info("Start crawl")
    try:
        db = firestore_connection()
        deleted_collection(db,source_name)
        if source_name in [const.MAFF_SUBSIDES,const.MAFF_FINANCING,const.JNET21_SUBSIDES_AND_FINANCING]:
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
    except:
        logging.error("エラーが発生しました。",exc_info=True)
    logging.info("completed crawl!")

def deleted_collection(db,collection_name):
    """
    指定した名前のコレクションを削除する

    Parametrers:
        db : firestoreの接続情報
        collection_name string: コレクションの名前
    """
    collections = db.collection(collection_name).stream()
    for collection in collections:
        firestore_document = db.collection(collection_name).document(collection.id)
        firestore_document.delete()

def source_of_page_clicked(url,xpath):
    """
     ページ内部の要素をクリック後、ソースを取得

     Parametrers
     -----------
     url
        ページのURL
     xpath
        対象要素のxpath
    """

    driver_path = 'chromedriver'
    options = Options()
    options.add_argument('--disable-gpu')#GPUハードウェアアクセラレーションを無効
    options.add_argument('--disable-extensions')#全ての拡張機能を無効
    options.add_argument('--proxy-server="direct://"')#プロキシ経由せず直接接続
    options.add_argument('--proxy-bypass-list=*')#プロキシサーバー経由しない
    options.add_argument('--start-maximized')#初期のウィンドウサイズ最大化
    options.add_argument('--headless')#ヘッドレスモードで起動

    driver = webdriver.Chrome(executable_path=driver_path,chrome_options=options)
    driver.get(url)


    # フォームの「補助金・助成金・融資」を選択
    for val in xpath:
        element = driver.find_element_by_xpath(val)
        element.click()

    source = driver.page_source
    # ブラウザとウィンドウを共に閉じる
    driver.close
    driver.quit

    return source


def date_split(recruitment_period):
    """
    波ダッシュで区切られた年月日をstart_dateとend_dateに分ける
    Parameter:
        recruitment_period String : 波ダッシュで区切られた年月日

    Returns:
        before_merge_date dict: 開始日と終了日
    """
    # 融資情報で募集期間がない場合があるためNoneで弾く
    if recruitment_period == None:
        return {
            "start_date":"",
            "end_date":""
        }

    normalized_text = unicodedata.normalize("NFKC",recruitment_period.get_text())

    # 取得先のサイトで開始日または終了日を「〜」で表現している
    # 「〜」の位置で開始日か終了日を判定
    if normalized_text.find("~") == 0:
        # 開始日だけ指定されているケース
        before_marge_date ={
            "start_date":converted_datetime(normalized_text),
            "end_date":"~"
        }
    elif normalized_text.find("~") == 11 and len(normalized_text.split('~')) == 1:
        # 終了日だけ指定されているケース
        before_marge_date ={
            "start_date":"~",
            "end_date":converted_datetime(normalized_text),
        }

    splited_date = normalized_text.split("~")
    before_marge_date = {
        "start_date":converted_datetime(splited_date[0]),
        "end_date":converted_datetime(splited_date[len(splited_date)-1])
    }

    return before_marge_date

def converted_datetime(date):
    """
    XXXX年XX月XX日形式の日付をdatetimeに変換する

    Parameters:
        date String: XXXX年XX月XX日の日付
    """

    pattern = r"(?P<year>[0-9]{4})年(?P<month>[0-9]{1,2})月(?P<day>[0-9]{1,2})日"
    redate = re.search(pattern,date)

    return datetime.datetime(int(redate.group('year')),int(redate.group('month')),int(redate.group('day')))

def crawl_public_offering_list(source_url):
    """
     公募ページから開始日・終了日・公募名・urlを取得

     Parameter
     -----------
     source_url
        ページのURL
    """

    logging.info(f"Accessing TO {source_url}...")
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
    const.MAFF_PUBLIC_OFFERING:"https://www.maff.go.jp/j/supply/hozyo/",
    const.JNET21_SUBSIDES_AND_FINANCING:"https://j-net21.smrj.go.jp/snavi/articles"
}

for source_name,source_url in source_names.items():
    crawl_funding_source_add(source_name,source_url)
