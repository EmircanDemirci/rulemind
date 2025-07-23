# 🧠 RuleMind - AI-Powered Sigma Rule Similarity Engine

![RuleMind Logo](./media/logo.png)

**RuleMind**, siber güvenlik uzmanları için geliştirilmiş, **Sigma kuralları** üzerinde çalışan gelişmiş bir analiz ve benzerlik tespit sistemidir. Yeni oluşturulan Sigma kurallarını mevcut kural veritabanıyla karşılaştırarak, yinelenen kural yazımını önler ve analiz süreçlerini hızlandırır.

## 🚀 Özellikler

### 🔍 **Çok Katmanlı Benzerlik Analizi**
- **Yapısal Analiz**: YAML yapısı, field'lar ve değerler bazında karşılaştırma
- **Semantik Analiz**: MITRE ATT&CK teknikleri ve taktikleri bazında benzerlik
- **AI-Destekli Analiz**: Ollama LLM desteği ile mantıksal benzerlik tespiti

### 🛠️ **Sigma Kural Yönetimi**
- **Kural Oluşturucu**: AI destekli otomatik Sigma kural üretimi
- **Sigma to Splunk**: Sigma kurallarını SPL sorgularına dönüştürme(Geliştirme aşaması)
- **GitHub Entegrasyonu**: Sigma kurallarını otomatik olarak çekme ve veritabanına kaydetme(Geliştirme aşaması)

### 🖥️ **Modern Web Arayüzü**
- **Streamlit** tabanlı karanlık tema arayüz
- **Real-time** sonuç görüntüleme
- **Responsive** tasarım

### 🗄️ **Veritabanı Desteği**
- **MongoDB** entegrasyonu
- **Otomatik** kural indeksleme
- **Hızlı** arama ve filtreleme

## 📁 Proje Yapısı

```
RuleMind/
├── app.py                      # Ana Streamlit uygulaması
├── basic_api.py               # Flask API endpoint'leri
├── ollama_ai.py               # AI-destekli kural karşılaştırma
├── sigma_to_spl.py            # Sigma to Splunk dönüştürücü
├── similarity_algorithm.py    # Benzerlik algoritması
├── create_a_sigma_rule.py     # AI destekli kural oluşturucu
├── download_script.py         # GitHub'dan kural indirici
├── mongodb_connection.py      # MongoDB bağlantı yöneticisi
├── page/                      # Streamlit sayfaları
│   ├── Home.py               # Ana sayfa
│   ├── check_ai.py           # AI kontrol sayfası
│   ├── sigma_rule.py         # Kural oluşturma sayfası
│   ├── sigtospl.py          # Sigma-SPL dönüştürme sayfası
│   └── similarity.py         # Benzerlik analizi sayfası
└── media/
    └── logo.png              # Proje logosu
```

## 🛠️ Kurulum

### Gereksinimler

- Python 3.8+
- MongoDB
- Ollama (AI modeli için)

### Adım 1: Depoyu Klonlayın

```bash
git clone <repository-url>
cd RuleMind
```

### Adım 2: Python Bağımlılıklarını Yükleyin

```bash
pip install streamlit
pip install pymongo
pip install pyyaml
pip install requests
pip install python-dotenv
pip install fastapi
pip install uvicorn
pip install sigma-cli
pip install tqdm
pip install difflib
```

### Adım 3: Ortam Değişkenlerini Ayarlayın

`.env` dosyası oluşturun:

```env
MONGO_URI=mongodb://localhost:27017
OLLAMA_URL=http://localhost:11434/api/generate
OLLAMA_MODEL=ALIENTELLIGENCE/cybersecuritythreatanalysisv2
GITHUB_TOKEN=your_github_token_here
```

### Adım 4: MongoDB'yi Başlatın

```bash
# MongoDB servisini başlatın
sudo systemctl start mongod

# Veya Docker ile
docker run -d -p 27017:27017 --name mongodb mongo:latest
```

### Adım 5: Ollama'yı Kurun ve Başlatın

```bash
# Ollama'yı indirin ve kurun
curl -fsSL https://ollama.ai/install.sh | sh

# LLaMA3 modelini indirin
ollama pull llama3
ollama pull ALIENTELLIGENCE/cybersecuritythreatanalysisv2

# Ollama servisini başlatın
ollama serve
```

## 🚀 Kullanım

### Web Arayüzünü Başlatma

```bash
streamlit run app.py
```

Tarayıcınızda `http://localhost:8501` adresine gidin.

### API Servisini Başlatma

```bash
python basic_api.py
```

API `http://localhost:5000` adresinde çalışacaktır.

### Sigma-to-SPL Dönüştürücüyü Başlatma

```bash
uvicorn sigma_to_spl:app --host 0.0.0.0 --port 8000
```

API dokümantasyonu: `http://localhost:8000/docs`

### Sigma Kurallarını İndirme

```bash
python download_script.py
```

Bu komut GitHub'dan Sigma kurallarını indirecek ve MongoDB'ye kaydetecektir.

## 📖 Kullanım Kılavuzu

### 1. 🏠 **Ana Sayfa (Overview)**
- Proje hakkında genel bilgiler
- Sistem özelliklerinin özeti

### 2. 🤖 **AI Checker**
- Oluşturulan kuralların AI destekli analizi
- LLM tabanlı kalite kontrolü

### 3. 🔍 **Similarity Check**
- Yeni kuralların mevcut kurallarla benzerlik analizi
- Çok katmanlı karşılaştırma sonuçları
- Görsel benzerlik skorları

### 4. ✍️ **Create a Sigma Rule**
- AI destekli otomatik kural oluşturma
- İdea'dan Sigma kuralına dönüştürme
- MITRE ATT&CK entegrasyonu

### 5. 🔄 **Sigma to Splunk**
- Sigma kurallarını SPL sorgularına dönüştürme
- Batch dönüştürme desteği
- Hata kontrollü çıktı

## 🧮 Algoritma Detayları

### Benzerlik Hesaplama Yöntemi

RuleMind, üç farklı analiz katmanı kullanır:

1. **Strukturel Benzerlik**: YAML yapısı, field adları, değer türleri
2. **Semantik Benzerlik**: Log kaynakları, detection logic, MITRE teknikleri
3. **AI Benzerlik**: LLM tabanlı derin analiz

```python
total_score = (structural_score * 0.3) + (semantic_score * 0.4) + (ai_score * 0.3)
```

### Desteklenen Sigma Fields

- `title`, `description`, `author`
- `logsource` (category, product, service)
- `detection` (selection, condition)
- `tags` (MITRE ATT&CK)
- `level`, `status`

## 🔧 API Referansı

### Sigma to SPL API

**POST** `/convert`
```json
{
  "sigma_rule": "title: Test Rule\ndetection:\n  selection:\n    CommandLine: '*powershell*'\n  condition: selection",
  "metadata": {}
}
```

**GET** `/search/{query}`
- GitHub'dan Sigma kuralları arama

## 🤝 Katkıda Bulunma

1. Bu depoyu fork edin
2. Yeni bir feature branch oluşturun (`git checkout -b feature/amazing-feature`)
3. Değişikliklerinizi commit edin (`git commit -m 'Add amazing feature'`)
4. Branch'inizi push edin (`git push origin feature/amazing-feature`)
5. Pull Request oluşturun

## 📝 Lisans

Bu proje MIT lisansı altında lisanslanmıştır. Detaylar için `LICENSE` dosyasına bakınız.

## 🛟 Destek

Herhangi bir sorun yaşarsanız:

1. GitHub Issues'da yeni bir konu açın
2. Detaylı hata loglarını paylaşın
3. Sistem bilgilerinizi belirtin

## 🔮 Gelecek Özellikler

- [ ] Machine Learning tabanlı otomatik kural önerisi - SigFinder
- [ ] SIEM platformları için direct export
- [ ] Advanced visualization dashboard
- [ ] Geniş kütüphane desteği

## 👨‍💻 Geliştirici

Bu proje siber güvenlik toplumu için geliştirilmiştir. Amacım, güvenlik analistlerinin iş yükünü azaltmak ve daha etkili detection rule'ları oluşturmalarına yardımcı olmaktır.

---

**⚡ RuleMind ile siber güvenlik kurallarınızı yeni nesil AI teknolojisiyle güçlendirin!**
