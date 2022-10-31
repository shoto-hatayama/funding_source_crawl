#  firestore保存のためのJSONファイル名
FIREBASE_JSON_NAME = 'fundingsourceview-firebase-adminsdk-tq58w-82d2be4281.json'

# コレクションの保存先
MAFF_SUBSIDES = 'MAFF_SUBSIDES'
MAFF_FINANCING = 'MAFF_FINANCING'
MAFF_PUBLIC_OFFERING = 'MAFF_PUBLIC_OFFERING'

# 各年号の元年を定義
ERADICT = {
    "明治": 1868,
    "大正": 1912,
    "昭和": 1926,
    "平成": 1989,
    "令和": 2019,
}

#
OFFERRING_COLLECTION_KEY = [
    'begin_date',
    'end_date',
    'public_offering_name'
]