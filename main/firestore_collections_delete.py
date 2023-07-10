"""firestoreのコレクションの削除を管理"""
import logging
from firestore_connection import FirestoreConnection
class FirestoreCollectionsDelete:
    """firestoreのコレクションを削除"""
    __collection_names = {
        'MAFF_SUBSIDES',
        'MAFF_FINANCING',
        'MAFF_PUBLIC_OFFERING',
        'JNET21_SUBSIDES_AND_FINANCING'
    }

    def __init__(self):
        self.__client=  FirestoreConnection().get_client()

    def all_clear(self) -> None:
        """firestore内の全てのコレクションを削除する"""
        try:
            for collection_name in self.__collection_names:
                collections = self.__client.collection(collection_name).stream()
                for collection in collections:
                    firestore_document = self.__client.collection(collection_name).document(collection.id)
                    firestore_document.delete()

                print(collection_name + 'の削除が完了しました。')
                logging.info("%s delete completed",collection_name)
        except Exception as error_msg:
            logging.error('★★★★★ここからエラー文★★★★★')
            logging.error(error_msg)
            logging.error('★★★★★ここまで★★★★★')

