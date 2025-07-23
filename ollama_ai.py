import yaml
import os
import requests
from dotenv import load_dotenv
from mongodb_connection import MongoConnector
import re
import time
load_dotenv()

class OllamaAI:
    def __init__(
        self,
        mongo_uri=None,
        db_name="sigmaDB",
        collection_name="rules",
        ollama_url="http://localhost:11434/api/generate",
        ollama_model=None,
    ):
        self.mongo_uri = mongo_uri or os.getenv("MONGO_URI")
        self.db_name = db_name
        self.collection_name = collection_name
        self.ollama_url = ollama_url
        self.ollama_model = ollama_model or os.getenv("OLLAMA_MODEL")

    def load_yaml(self, file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    def fetch_latest_rules(self, limit=10):
        connector = MongoConnector(self.mongo_uri, self.db_name, self.collection_name)
        collection = connector.connect()
        rules = list(collection.find())
        connector.close()
        return rules[-limit:]

    def compare_rules_with_ai(self, rule1, rule2):
        prompt = self._generate_prompt(rule1, rule2)
        response = requests.post(self.ollama_url, json={
            "model": self.ollama_model,
            "prompt": prompt,
            "stream": False
        })

        response.raise_for_status()
        full_response = response.json().get("response")
        print(full_response)

        score = self._extract_score(full_response)

        return {
            "score": score,
            "explanation": full_response,
            "rule1" : yaml.dump(rule1),
            "rule2" : yaml.dump(rule2)
        }

    def _generate_prompt(self, rule1, rule2):
        return f"""Sen bir siber güvenlik uzmanısın. Aşağıda iki farklı Sigma kuralı veriliyor. Görevin şu:

1. **TEKNİK BENZERLİKLERİ** listele. Aşağıdaki kriterlere göre değerlendir:
   - Aynı logsource (örn. sysmon, zeek, powershell)
   - Aynı veya benzer MITRE ATT&CK teknikleri/taktikleri (örn. T1047, TA0006)
   - Aynı servisler veya modüller (örn. WMI, SMB, Kerberos, PowerShell)
   - Benzer EventID, path, process, image, signature, detection pattern

2. **TEKNİK FARKLILIKLARI** listele:
   - Farklı teknikler, farklı detection mantıkları, farklı log kaynakları, farklı kullanım bağlamları

3. En sonunda bu iki kuralın teknik olarak ne kadar benzer olduğunu **0 ile 100 arasında bir skorla** puanla.

4. Son olarak her bir kuralın `title` alanını kullanarak ortak noktalarına göre kısa bir **başlık listesi** üret. Bu başlıklar, bu iki kuralın hangi alanda benzer olduğunu ifade etsin. (örn. "WMI üzerinden DLL yükleme", "Sysmon ile credential access tespiti", vb.)

Yalnızca aşağıdaki formatta cevap ver:

---

**Teknik Benzerlikler:**
- [madde 1]
- [madde 2]
...

**Teknik Farklılıklar:**
- [madde 1]
- [madde 2]
...

**Benzerlik Skoru:** XX / 100
...

---

Aşağıda karşılaştırılacak Sigma kuralları bulunmaktadır:

### Kural 1:
{yaml.dump(rule1)}

### Kural 2:
{yaml.dump(rule2)}

"""


    def _extract_score(self, text):
        # 0-100 arası sayı arar
        patterns = [
    r"Benzerlik Skoru.*?:\s*(\d{1,3})",   # Benzerlik Skoru (0-100 arası sayı): 75
    r"benzerlik skoru.*?:\s*(\d{1,3})",   # aynı ama küçük harf
    r"skoru.*?(\d{1,3})",                 # genel fallback
    r"(\d{1,3})/100",                     # 85/100 gibi
    r"(\d{1,3})\s*dir",                   # 50'dir gibi
    r"(\d{1,3})\s*puan",                  # 60 puan
    r"(\d{1,3})$"                         # sadece sayı
]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                score = int(match.group(1))
                if 0 <= score <= 100:
                    return score
        return 0

# Bu eşik skoru geçmeyen karşılaştırmalar atlanacak
THRESHOLD_SCORE = 50

def main():
    ai = OllamaAI()

    yaml_path = input("Karşılaştırmak istediğin Sigma YAML dosyasının yolunu gir: ").strip()

    if not os.path.exists(yaml_path):
        print(f"❌ Dosya bulunamadı: {yaml_path}")
        return

    try:
        rule_from_file = ai.load_yaml(yaml_path)
    except Exception as e:
        print(f"❌ YAML dosyası okunamadı: {e}")
        return

    rules_from_mongo = ai.fetch_latest_rules(limit=10)
    if not rules_from_mongo:
        print("MongoDB'den hiç kural alınamadı.")
        return

    print(f"\nMongoDB'den {len(rules_from_mongo)} kural alındı. Skoru {THRESHOLD_SCORE} üzerindekiler açıklanacak.\n")

    for idx, rule in enumerate(rules_from_mongo, start=1):
        try:
            result = ai.compare_rules_with_ai(rule_from_file, rule)
            score = result["score"]

            if score is None or score == 0:
                print(f"Kural #{idx}: ⚠️ Skor bulunamadı, atlanıyor.")
                continue

            if score >= THRESHOLD_SCORE:
                print(f"✅ Kural #{idx} Benzerlik Skoru: {score}/100")
                print("Açıklama:")
                print(result["explanation"])
                print("\n" + "=" * 60 + "\n")
            else:
                print(f"⏭️  Kural #{idx} skoru {score}, eşik değerin altında ({THRESHOLD_SCORE}), atlandı.\n")

            time.sleep(1)
            
        except Exception as e:
            print(f"❌ Kural #{idx} işlenirken hata: {e}")
            continue

if __name__ == "__main__":
    main()