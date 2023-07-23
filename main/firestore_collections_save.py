"""firestoreのコレクションの保存を管理"""
import logging
import traceback
from firestore_connection import FirestoreConnection
class FirestoreCollectionsSave:
    """firestoreのコレクションを保存"""

    def __init__(self):
        self.__client = FirestoreConnection().get_client()

    def add(self,crawl_data:dict,collection_name:str):
        """firestoreにクロールした情報を格納する"""
        try:
            collection = self.__client.collection(collection_name)
            collection.add(crawl_data)
        except Exception:
            logging.error(traceback.format_exc())