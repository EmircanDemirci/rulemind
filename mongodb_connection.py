from pymongo import MongoClient, errors
import logging
class MongoConnector:
    def __init__(self, uri: str, db_name: str, collection_name: str):
        self.uri = uri
        self.db_name = db_name
        self.collection_name = collection_name

        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s"
        )
        
    def connect(self):
        try:
            # Bağlantıyı başlat
            self.client = MongoClient(self.uri, serverSelectionTimeoutMS=5000)
            # Ping atarak bağlantıyı test et
            self.client.admin.command('ping')
            logging.info("[+] MongoDB bağlantısı başarılı")

            # Database ve collection objesini al
            db = self.client[self.db_name]
            self.collection = db[self.collection_name]
            return self.collection

        except errors.ServerSelectionTimeoutError as e:
            logging.error("[-] MongoDB bağlantı hatası: %s" , str(e))
            return None
        except Exception as e:
            logging.exception("[-] Bilinmeyen bir hata oluştu!")
            return None
    def close(self):
        if self.client:
            self.client.close()