from main.url_list_generator import UrlListGenerator
from main.html_source_getter import HtmlSourceGetter
import requests

def test_make_listexist():
    """正常にリンクが取得できているかチェック"""
    click_target = [
        '//*[@id="categorySelect"]/div/label[1]',#「補助金・助成金・融資」
        '//*[@id="searchForm"]/div[9]/button[1]' #「検索実行」
    ]
    url_selector =  "main#contents article div.HL-result ul.HL-resultList li div.title-meta > a"
    base_url = "https://j-net21.smrj.go.jp/"
    html_source_getter = HtmlSourceGetter("https://j-net21.smrj.go.jp/snavi/articles")
    page_source = html_source_getter.clicked_html(click_target)

    url_list_generator = UrlListGenerator()
    url_list_generator.make(page_source,url_selector,base_url)
    assert url_list_generator.get_url_list()

def test_make_listnotexist():
    """xpathが存在しない時にNoneを返すかチェック"""
    click_target = [
        '//*[@id="categorySelect"]/div/label[1]',#「補助金・助成金・融資」
        '//*[@id="searchForm"]/div[9]/button[1]' #「検索実行」
    ]
    url_selector =  "main#contents article div.HL-result ul.HL-resultList li div.title-meta > a"
    base_url = "https://j-net21.smrj.go.jp/"
    html_source_getter = HtmlSourceGetter("https://j-net21.smrj.go.jp/snavi")
    page_source = html_source_getter.clicked_html(click_target)

    url_list_generator = UrlListGenerator()
    url_list_generator.make(page_source,url_selector,base_url)
    assert not url_list_generator.get_url_list()

def test_setnexturl_exists():
    """next_urlが取得できているかチェック"""
    click_target = [
        '//*[@id="categorySelect"]/div/label[1]',#「補助金・助成金・融資」
        '//*[@id="searchForm"]/div[9]/button[1]' #「検索実行」
    ]
    base_url = "https://j-net21.smrj.go.jp/articles"
    next_url = "div.HL-result .HL-pagenation .nextBox li > a[href]"

    html_source_getter = HtmlSourceGetter("https://j-net21.smrj.go.jp/snavi/articles")
    page_source = html_source_getter.clicked_html(click_target)

    url_list_generator = UrlListGenerator()
    url_list_generator.set_next_url(page_source,next_url,base_url)

    assert url_list_generator.get_next_url()

def test_setnexturl_notexists():
    """引数に次ページのセレクターが渡されない時は空を返す"""
    source = requests.get("https://www.gyakubiki.maff.go.jp/appmaff/input/result.html?domain=M&tab=tab2&nen=A7&area=00").text
    url_list_generator = UrlListGenerator()
    url_list_generator.set_next_url(source)

    assert not url_list_generator.get_next_url()

