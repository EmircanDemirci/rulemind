import os
import requests
from tqdm import tqdm
from dotenv import load_dotenv
from pymongo import MongoClient
import yaml
from datetime import date

load_dotenv()

class SigmaFetcher:
    def __init__(
        self,
        db_name="sigmaDB",
        collection_name="rules",
        mongo_url=os.getenv("MONGO_URI"),
        owner="EmircanDemirci",
        repo="sigma",
        branch="main",
        save_dir="downloaded_sigma_rules"
    ):
        load_dotenv()
        self.token = os.getenv("GITHUB_TOKEN")
        self.headers = {"Authorization": f"token {self.token}"}

        self.repo_owner = owner
        self.repo_name = repo
        self.branch = branch
        self.save_dir = save_dir
        self.api_base_url = f"https://api.github.com/repos/{self.repo_owner}/{self.repo_name}/contents/rules"

        self.mongo_client = MongoClient(mongo_url)
        self.db = self.mongo_client[db_name]
        self.collection = self.db[collection_name]

    def fetch_file_list(self, api_url=None):
        if api_url is None:
            api_url = self.api_base_url

        try:
            response = requests.get(api_url, headers=self.headers)
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"[HATA] Github API isteği başarısız: {e}")
            return []

        files = response.json()
        all_files = []

        for file in files:
            if file["type"] == "file" and file["name"].endswith(".yml"):
                all_files.append(file["download_url"])
            elif file["type"] == "dir":
                sub_files = self.fetch_file_list(file["url"])
                if sub_files:
                    all_files.extend(sub_files)

        return all_files

    def convert_dates(self, obj):
        if isinstance(obj, dict):
            return {k: self.convert_dates(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self.convert_dates(i) for i in obj]
        elif isinstance(obj, date):
            return obj.isoformat()
        return obj

    def download_and_store_to_mongo(self, urls):
        for url in tqdm(urls, desc="Sigma kural dosyaları indiriliyor ve MongoDB'ye kaydediliyor..."):
            try:
                response = requests.get(url, headers=self.headers)
                response.raise_for_status()

                yaml_data = yaml.safe_load(response.text)

                if yaml_data:
                    yaml_data = self.convert_dates(yaml_data)  # Tarih formatlarını düzelt
                    doc_id = url.split("/")[-1]
                    yaml_data["_id"] = doc_id
                    yaml_data["source_url"] = url

                    self.collection.replace_one({"_id": doc_id}, yaml_data, upsert=True)
            except requests.RequestException as e:
                print(f"[HATA] Dosya indirilemedi: {url} -> {e}")
            except yaml.YAMLError as ye:
                print(f"[HATA] YAML ayrıştırılamadı: {url} -> {ye}")
            except Exception as ex:
                print(f"[HATA] MongoDB'ye kayıt yapılamadı: {url} -> {ex}")

    def run(self):
        print("[INFO] Sigma kuralları toplanıyor...")
        rule_urls = self.fetch_file_list()
        print(f"[INFO] Toplam {len(rule_urls)} dosya bulundu.")
        self.download_and_store_to_mongo(rule_urls)
        print(f"[BİTTİ] Tüm kurallar MongoDB'ye kaydedildi.")

if __name__ == "__main__":
    fetcher = SigmaFetcher()
    fetcher.run()
