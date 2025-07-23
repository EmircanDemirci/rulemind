from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sigma.rule import SigmaRule
from sigma.collection import SigmaCollection
from sigma.backends.splunk import SplunkBackend
import yaml
from typing import List, Dict, Any, Optional
import logging
import urllib.request
import json
import re
import time
import uuid

# Logging yapılandırması
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI uygulaması oluştur
app = FastAPI(
    title="Sigma to Splunk Converter API",
    description="Sigma kurallarını Splunk sorgularına dönüştüren ve GitHub'dan Sigma kuralları arayan REST API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware ekle
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request modeli
class SigmaConvertRequest(BaseModel):
    sigma_rule: str
    metadata: Dict[str, Any] = {}

    class Config:
        schema_extra = {
            "example": {
                "sigma_rule": """title: Test Rule
description: A test detection rule
status: test
author: Test Author
date: 2023/01/01
logsource:
    category: process_creation
    product: windows
detection:
    selection:
        Image|endswith: '\\cmd.exe'
        CommandLine|contains: 'whoami'
    condition: selection
falsepositives:
    - Unknown
level: medium""",
                "metadata": {
                    "request_id": "12345",
                    "user": "test_user"
                }
            }
        }

# Sigma search request modeli
class SigmaSearchRequest(BaseModel):
    target_id: str
    metadata: Dict[str, Any] = {}

    class Config:
        schema_extra = {
            "example": {
                "target_id": "7efd2c8d-8b18-45b7-947d-adfe9ed04f61",
                "metadata": {
                    "request_id": "search-123",
                    "user": "analyst"
                }
            }
        }

# Response modeli
class SigmaConvertResponse(BaseModel):
    success: bool
    message: str
    queries: List[str] = []
    rule_info: Dict[str, Any] = {}
    metadata: Dict[str, Any] = {}

# Sigma search response modeli
class SigmaSearchResponse(BaseModel):
    success: bool
    message: str
    found_rule: Optional[Dict[str, Any]] = None
    search_stats: Dict[str, Any] = {}
    metadata: Dict[str, Any] = {}

# UUID kontrol modelleri
class UUIDCheckRequest(BaseModel):
    value: str
    metadata: Dict[str, Any] = {}

    class Config:
        schema_extra = {
            "example": {
                "value": "7efd2c8d-8b18-45b7-947d-adfe9ed04f61",
                "metadata": {
                    "request_id": "uuid-check-123",
                    "user": "analyst"
                }
            }
        }

class UUIDCheckResponse(BaseModel):
    is_valid_uuid: bool
    message: str
    value: str
    uuid_version: Optional[int] = None
    metadata: Dict[str, Any] = {}

# Basit UUID request modeli (kullanıcının eklediği)
class UUIDRequest(BaseModel):
    value: str

# Internal UUID kontrol fonksiyonu (helper)
def is_valid_uuid(value: str) -> bool:
    """Internal helper: String'in geçerli UUID olup olmadığını kontrol eder"""
    try:
        uuid.UUID(value)
        return True
    except ValueError:
        return False

# GitHub'dan dosya listesi alma fonksiyonu
def get_github_files(repo_path: str = "rules/windows/process_creation"):
    """GitHub API'sini kullanarak dosya listesi al"""
    api_url = f"https://api.github.com/repos/SigmaHQ/sigma/contents/{repo_path}"
    
    try:
        with urllib.request.urlopen(api_url) as response:
            data = json.loads(response.read().decode('utf-8'))
            
        files = []
        for item in data:
            if item['type'] == 'file' and item['name'].endswith('.yml'):
                files.append({
                    "name": item['name'],
                    "download_url": item['download_url'],
                    "size": item['size']
                })
        
        return files
    except Exception as e:
        logger.error(f"GitHub API hatası: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"GitHub'dan dosya listesi alınamadı: {str(e)}"
        )

# Sigma kuralında ID arama fonksiyonu
def extract_id_from_content(content: str) -> Optional[str]:
    """Sigma kural içeriğinden ID'yi çıkar"""
    for line in content.splitlines():
        line = line.strip()
        if line.startswith("id:"):
            # ID'yi çıkar (yml formatında olabilir)
            id_part = line.split("id:")[1].strip()
            # Tırnak işaretlerini ve boşlukları temizle
            id_part = id_part.strip('\'"').strip()
            return id_part
    return None

# Dosya indirme ve analiz fonksiyonu
def download_and_check_file(file_info: Dict[str, Any], target_id: str) -> Optional[Dict[str, Any]]:
    """Dosyayı indir ve target ID'yi ara"""
    try:
        with urllib.request.urlopen(file_info["download_url"]) as response:
            content = response.read().decode("utf-8")
            
        current_id = extract_id_from_content(content)
        if current_id and current_id.lower() == target_id.lower():
            return {
                "filename": file_info["name"],
                "download_url": file_info["download_url"],
                "content": content,
                "id": current_id,
                "file_size": file_info.get("size", 0)
            }
    except Exception as e:
        logger.warning(f"Dosya indirilemedi {file_info['name']}: {str(e)}")
    
    return None

# Health check endpoint
@app.get("/health")
async def health_check():
    """API sağlık durumu kontrolü"""
    return {"status": "healthy", "service": "sigma-to-splunk-converter"}

# Ana dönüştürme endpoint'i
@app.post("/convert", response_model=SigmaConvertResponse)
async def convert_sigma_to_splunk(request: SigmaConvertRequest):
    """
    Sigma kuralını Splunk sorgusuna dönüştür
    
    Args:
        request: SigmaConvertRequest - Sigma kuralı ve metadata içeren istek
        
    Returns:
        SigmaConvertResponse - Dönüştürülmüş Splunk sorguları ve bilgiler
    """
    
    logger.info(f"Sigma dönüştürme isteği alındı. Metadata: {request.metadata}")
    
    try:
        # YAML parse et
        try:
            sigma_dict = yaml.safe_load(request.sigma_rule)
            if not sigma_dict:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Boş veya geçersiz YAML formatı"
                )
        except yaml.YAMLError as e:
            logger.error(f"YAML parse hatası: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"YAML parse hatası: {str(e)}"
            )
        
        # SigmaRule objesi oluştur
        try:
            sigma_rule = SigmaRule.from_dict(sigma_dict)
        except Exception as e:
            logger.error(f"SigmaRule oluşturma hatası: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Geçersiz Sigma kuralı formatı: {str(e)}"
            )
        
        # SigmaCollection oluştur
        collection = SigmaCollection([sigma_rule])
        
        # Splunk backend oluştur
        backend = SplunkBackend()
        
        # Sigma'yı Splunk'a dönüştür
        try:
            queries = backend.convert(collection)
            splunk_queries = [str(query) for query in queries]
        except Exception as e:
            logger.error(f"Sigma dönüştürme hatası: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Sigma dönüştürme hatası: {str(e)}"
            )
        
        # Kural bilgilerini topla
        rule_info = {
            "title": getattr(sigma_rule, 'title', 'N/A'),
            "description": getattr(sigma_rule, 'description', 'N/A'),
            "author": getattr(sigma_rule, 'author', 'N/A'),
            "status": getattr(sigma_rule, 'status', 'N/A'),
            "level": getattr(sigma_rule, 'level', 'N/A'),
            "logsource": getattr(sigma_rule, 'logsource', {}).__dict__ if hasattr(getattr(sigma_rule, 'logsource', {}), '__dict__') else str(getattr(sigma_rule, 'logsource', {})),
            "tags": getattr(sigma_rule, 'tags', [])
        }
        
        logger.info(f"Başarıyla {len(splunk_queries)} Splunk sorgusu oluşturuldu")
        
        return SigmaConvertResponse(
            success=True,
            message=f"Sigma kuralı başarıyla {len(splunk_queries)} Splunk sorgusuna dönüştürüldü",
            queries=splunk_queries,
            rule_info=rule_info,
            metadata=request.metadata
        )
        
    except HTTPException:
        # HTTPException'ları tekrar fırlat
        raise
    except Exception as e:
        logger.error(f"Beklenmeyen hata: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Sunucu hatası: {str(e)}"
        )

# Sigma kural arama endpoint'i
@app.post("/search-sigma", response_model=SigmaSearchResponse)
async def search_sigma_rule(request: SigmaSearchRequest):
    """
    GitHub'dan Sigma kurallarını çekip ID'ye göre arama yap
    
    Args:
        request: SigmaSearchRequest - Aranacak ID ve metadata
        
    Returns:
        SigmaSearchResponse - Bulunan kural bilgileri
    """
    
    logger.info(f"Sigma kural arama isteği: {request.target_id}")
    
    # Timeout kontrolü için başlangıç zamanı
    start_time = time.time()
    timeout_seconds = 60
    
    try:
        # Önce target_id'nin geçerli UUID olup olmadığını kontrol et
        if not is_valid_uuid(request.target_id.strip()):
            return SigmaSearchResponse(
                success=False,
                message=f"Geçersiz UUID formatı: {request.target_id}",
                found_rule=None,
                search_stats={"target_id": request.target_id, "error": "invalid_uuid"},
                metadata=request.metadata
            )
        
        # GitHub'dan dosya listesi al
        files = get_github_files()
        
        search_stats = {
            "total_files": len(files),
            "searched_files": 0,
            "skipped_files": 0,
            "target_id": request.target_id,
            "timeout_seconds": timeout_seconds
        }
        
        found_rule = None
        
        # Her dosyayı kontrol et
        for file_info in files:
            # Timeout kontrolü
            elapsed_time = time.time() - start_time
            if elapsed_time > timeout_seconds:
                logger.warning(f"Arama timeout'a uğradı: {elapsed_time:.2f} saniye")
                search_stats["timeout"] = True
                search_stats["elapsed_time"] = elapsed_time
                
                raise HTTPException(
                    status_code=status.HTTP_408_REQUEST_TIMEOUT,
                    detail=f"Arama işlemi {timeout_seconds} saniye timeout'ına uğradı. {search_stats['searched_files']}/{search_stats['total_files']} dosya tarandı."
                )
            
            try:
                result = download_and_check_file(file_info, request.target_id.strip())
                search_stats["searched_files"] += 1
                
                if result:
                    found_rule = result
                    logger.info(f"Kural bulundu: {file_info['name']} ({elapsed_time:.2f} saniyede)")
                    break
                    
            except Exception as e:
                search_stats["skipped_files"] += 1
                logger.warning(f"Dosya atlandı {file_info['name']}: {str(e)}")
                continue
        
        # Toplam süre bilgisi
        total_elapsed = time.time() - start_time
        search_stats["elapsed_time"] = total_elapsed
        search_stats["timeout"] = False
        
        if found_rule:
            return SigmaSearchResponse(
                success=True,
                message=f"Kural bulundu: {found_rule['filename']} ({total_elapsed:.2f} saniyede)",
                found_rule=found_rule,
                search_stats=search_stats,
                metadata=request.metadata
            )
        else:
            return SigmaSearchResponse(
                success=False,
                message=f"ID '{request.target_id}' ile eşleşen kural bulunamadı ({total_elapsed:.2f} saniyede, {search_stats['searched_files']} dosya tarandı)",
                found_rule=None,
                search_stats=search_stats,
                metadata=request.metadata
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Arama sırasında hata: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Arama hatası: {str(e)}"
        )

# Sigma arama ve dönüştürme kombinasyonu
@app.post("/search-and-convert")
async def search_and_convert_sigma(request: SigmaSearchRequest):
    """
    Sigma kuralını ID'ye göre bul ve Splunk sorgusuna dönüştür
    
    Args:
        request: SigmaSearchRequest - Aranacak ID ve metadata
        
    Returns:
        Combined response - Bulunan kural ve Splunk sorgusu
    """
    
    # Önce kuralı ara
    search_result = await search_sigma_rule(request)
    
    if not search_result.success or not search_result.found_rule:
        return {
            "success": False,
            "message": search_result.message,
            "search_result": search_result.dict(),
            "conversion_result": None
        }
    
    # Bulunan kuralı dönüştür
    try:
        convert_request = SigmaConvertRequest(
            sigma_rule=search_result.found_rule["content"],
            metadata=request.metadata
        )
        
        conversion_result = await convert_sigma_to_splunk(convert_request)
        
        return {
            "success": True,
            "message": f"Kural bulundu ve başarıyla dönüştürüldü",
            "search_result": search_result.dict(),
            "conversion_result": conversion_result.dict()
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"Kural bulundu ancak dönüştürülemedi: {str(e)}",
            "search_result": search_result.dict(),
            "conversion_result": None
        }

# GitHub dosya listesi endpoint'i
@app.get("/list-sigma-files")
async def list_sigma_files():
    """GitHub'daki Sigma dosyalarının listesini döndür"""
    try:
        files = get_github_files()
        return {
            "success": True,
            "message": f"{len(files)} dosya bulundu",
            "files": files,
            "total_count": len(files)
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Dosya listesi alınamadı: {str(e)}"
        )

# Batch dönüştürme endpoint'i
@app.post("/convert-batch", response_model=List[SigmaConvertResponse])
async def convert_batch_sigma_to_splunk(requests: List[SigmaConvertRequest]):
    """
    Birden fazla Sigma kuralını toplu olarak Splunk sorgularına dönüştür
    
    Args:
        requests: List[SigmaConvertRequest] - Sigma kuralları listesi
        
    Returns:
        List[SigmaConvertResponse] - Dönüştürülmüş Splunk sorguları listesi
    """
    
    logger.info(f"Toplu dönüştürme isteği alındı. {len(requests)} kural")
    
    results = []
    
    for i, request in enumerate(requests):
        try:
            result = await convert_sigma_to_splunk(request)
            results.append(result)
        except HTTPException as e:
            # Hatalı kurallar için hata response'u ekle
            error_response = SigmaConvertResponse(
                success=False,
                message=f"Kural {i+1} dönüştürme hatası: {e.detail}",
                queries=[],
                rule_info={},
                metadata=request.metadata
            )
            results.append(error_response)
        except Exception as e:
            error_response = SigmaConvertResponse(
                success=False,
                message=f"Kural {i+1} beklenmeyen hata: {str(e)}",
                queries=[],
                rule_info={},
                metadata=request.metadata
            )
            results.append(error_response)
    
    return results

# Basit UUID kontrol endpoint'i (kullanıcının eklediği)
@app.post("/check-uuid")
def check_is_uuid(request: UUIDRequest):
    """Basit UUID kontrol endpoint'i"""
    try:
        uuid.UUID(request.value)
        return {"is_uuid": True, "sigmatext": request.value}
    except ValueError:
        return {"is_uuid": False, "sigmatext": request.value}

# UUID kontrol endpoint'i
@app.post("/is-uuid", response_model=UUIDCheckResponse)
async def is_uuid_endpoint(request: UUIDCheckRequest):
    """
    Gelen değerin geçerli bir UUID olup olmadığını kontrol et
    
    Args:
        request: UUIDCheckRequest - Kontrol edilecek değer ve metadata
        
    Returns:
        UUIDCheckResponse - UUID geçerliliği ve detay bilgileri
    """
    
    logger.info(f"UUID kontrol isteği: {request.value}")
    
    try:
        # UUID kontrolü yap
        parsed_uuid = uuid.UUID(request.value)
        
        # UUID versiyonunu belirle
        uuid_version = parsed_uuid.version
        
        logger.info(f"Geçerli UUID bulundu: {request.value} (Version: {uuid_version})")
        
        return UUIDCheckResponse(
            is_valid_uuid=True,
            message=f"Geçerli UUID (Version {uuid_version})",
            value=request.value,
            uuid_version=uuid_version,
            metadata=request.metadata
        )
        
    except ValueError as e:
        logger.info(f"Geçersiz UUID: {request.value} - {str(e)}")
        
        return UUIDCheckResponse(
            is_valid_uuid=False,
            message=f"Geçersiz UUID formatı: {str(e)}",
            value=request.value,
            uuid_version=None,
            metadata=request.metadata
        )
    except Exception as e:
        logger.error(f"UUID kontrol hatası: {str(e)}")
        
        return UUIDCheckResponse(
            is_valid_uuid=False,
            message=f"UUID kontrol sırasında hata: {str(e)}",
            value=request.value,
            uuid_version=None,
            metadata=request.metadata
        )

# Supported backends listesi
@app.get("/backends")
async def get_supported_backends():
    """Desteklenen backend'leri listele"""
    return {
        "supported_backends": ["splunk"],
        "default_backend": "splunk",
        "description": "Bu API şu anda yalnızca Splunk backend'ini desteklemektedir"
    }

# Örnek Sigma kuralı endpoint'i
@app.get("/example")
async def get_example_sigma_rule():
    """Örnek Sigma kuralı döndür"""
    example_rule = """title: Suspicious Process Creation
description: Detects suspicious process creation events
status: experimental
author: Security Team
date: 2023/01/01
logsource:
    category: process_creation
    product: windows
detection:
    selection:
        Image|endswith: 
            - '\\cmd.exe'
            - '\\powershell.exe'
        CommandLine|contains: 
            - 'whoami'
            - 'net user'
            - 'tasklist'
    condition: selection
falsepositives:
    - Administrative activities
level: medium
tags:
    - attack.discovery
    - attack.t1057"""
    
    return {
        "example_sigma_rule": example_rule,
        "description": "Bu örnekte Windows'ta şüpheli process oluşturma olayları tespit edilir"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)