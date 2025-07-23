import os
import requests
from dotenv import load_dotenv

load_dotenv()

class SigmaRuleGenerator:
    def __init__(self, ollama_url=None, ollama_model=None):
        self.ollama_url = ollama_url or os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
        self.ollama_model = ollama_model or os.getenv("OLLAMA_MODEL", "llama3")

    def generate(self, idea_text):
        """
        Verilen fikir üzerinden Sigma kuralı oluşturur.
        """
        prompt = f"""
Sen bir siber güvenlik uzmanısın ve Sigma kuralı yazmakla görevlisin.
Aşağıda verilen fikir, tespit edilmek istenen şüpheli bir davranışa dairdir.
Bu fikre uygun Sigma kuralını YAML formatında yaz. Kural MITRE ATT&CK teknikleriyle uyumlu olmalı.

Ayrıca bu kuralın Splunk (SPL) query karşılığını da üret.

Sadece aşağıdaki sırayla çıktı ver:

1. Sigma kuralı (YAML formatında, eksiksiz ve düzgün yapılandırılmış)
2. Ardından yalnızca altına tek başına `# SPL Query:` başlığı
3. Ve onun altında SPL query

Başka hiçbir açıklama, yorum ya da metin olmasın. Çıktı şu şekilde olmalı:

```yaml
<sigma_yaml_kurali>

"""
        response = requests.post(self.ollama_url, json={
            "model": self.ollama_model,
            "prompt": prompt,
            "stream": False
        })

        response.raise_for_status()
        return response.json().get("response", "Yanıt alınamadı")


# Örnek kullanım
if __name__ == "__main__":
    idea = input("Sigma kuralı için fikri girin (örn: PowerShell ile base64 kodlu komut çalıştırılması):\n> ")
    generator = SigmaRuleGenerator()
    sigma_yaml = generator.generate(idea)
    print("\n✅ Oluşturulan Sigma Kuralı:\n")
    print(sigma_yaml)
