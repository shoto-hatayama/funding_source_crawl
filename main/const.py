#  firestore保存のためのJSONファイル名
FIREBASE_JSON_NAME = '../fundingsourceview-firebase-adminsdk-tq58w-82d2be4281.json'

# コレクションの保存先
MAFF_SUBSIDES = 'MAFF_SUBSIDES'
MAFF_FINANCING = 'MAFF_FINANCING'
MAFF_PUBLIC_OFFERING = 'MAFF_PUBLIC_OFFERING'
JNET21_SUBSIDES_AND_FINANCING = "JNET21_SUBSIDES_AND_FINANCING"

# crawl_public_offering_listで使用する保存用のカラム名
OFFERRING_COLLECTION_KEY = [
    'begin_date',
    'end_date',
    'public_offering_name'
]

# JNET21データ保存用のカラム名
# TODO:定数名は要検討
JNET21_FIRESTORE_KEY = {
    '業種':'industry',
    '実施機関':'executing_agency',
    '地域':'area',
    '種類':'type'
}
