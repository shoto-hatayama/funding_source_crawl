from main.html_source_getter import HtmlSourceGetter

def test_htmlsourcegetter_is_value():
    """htmlが取得できたかチェック"""
    click_target = [
        '//*[@id="categorySelect"]/div/label[1]',#「補助金・助成金・融資」
        '//*[@id="searchForm"]/div[9]/button[1]' #「検索実行」
    ]
    url = "https://j-net21.smrj.go.jp/snavi/articles"

    html_source_getter = HtmlSourceGetter(url)

    assert html_source_getter.clicked_html(click_target)

def test_htmlsourcegetter_not_value():
    """存在しないxpathを指定した時に返り値がNoneかチェック"""
    click_target = [
        '//*[@id="categorySelect"]/div/label[1]',#「補助金・助成金・融資」
        '//*[@id="searchForm"]/div[9]/button[1]' #「検索実行」
    ]
    url = "https://j-net21.smrj.go.jp/snavi/"

    html_source_getter = HtmlSourceGetter(url)

    assert html_source_getter.clicked_html(click_target) is None

