"""firestoreの接続を管理する"""
from firebase_admin import firestore
import firebase_admin
from firebase_admin import credentials

class FirestoreConnection:
    """firestoreの接続"""

    __firebase_json_name = './fundingsourceview-firebase-adminsdk-tq58w-82d2be4281.json'

    def __init__(self):
        if not firebase_admin._apps:
            cred = credentials.Certificate(self.__firebase_json_name)
            firebase_admin.initialize_app(cred)
        self.__client = firestore.client().from_service_account_json(self.__firebase_json_name)

    def get_client(self):
        """接続情報を返す"""
        return self.__client