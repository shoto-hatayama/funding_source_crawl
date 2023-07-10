"""firestoreのコレクションの保存を管理"""
import logging
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
            print(crawl_data + 'の保存が完了しました。')
            logging.info("%s delete completed",collection_name)
        except Exception as error_msg:
            logging.error('★★★★★ここからエラー文★★★★★')
            logging.error(error_msg)
            logging.error('★★★★★ここまで★★★★★')

