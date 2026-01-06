import requests
import re
import os
import urllib3
import warnings

# Gereksiz SSL uyarılarını kapatalım
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
warnings.filterwarnings('ignore')

# Dosyaların karışmaması için klasör (Değişmedi)
output_folder = "streams"
if not os.path.exists(output_folder):
    os.makedirs(output_folder)

# Header Ayarları (Referer ve User-Agent önemli, yoksa site engeller)
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
}

# 1. BÖLÜM: Domain Kontrol (Düzeltildi)
base = "https://trgoals"
domain = ""

print("🔍 Domain aranıyor...")
for i in range(1495, 2101):
    test_domain = f"{base}{i}.xyz"
    try:
        # verify=False ile SSL hatasını geçiyoruz, daha hızlı buluyor
        response = requests.get(test_domain, headers=HEADERS, timeout=1.5, verify=False)
        if response.status_code == 200:
            domain = test_domain
            print(f"✅ Güncel Domain Bulundu: {domain}")
            break
    except:
        continue

if not domain:
    print("❌ Çalışır bir domain bulunamadı.")
    exit()

# Kanal ID'leri (Senin listen)
channel_ids = [
    "yayinzirve", "yayininat", "yayin1",
    "yayinb2", "yayinb3", "yayinb4",
    "yayinb5", "yayinbm1", "yayinbm2",
    "yayinss", "yayinss2", "yayint1",
    "yayint2", "yayint3", "yayint4",
    "yayinsmarts", "yayinsms2", "yayinnbatv", 
    "yayinex1", "yayinex2", "yayinex3", 
    "yayinex4", "yayinex5", "yayinex6",
    "yayinex7", "yayinex8", "yayineu1", "yayineu2"
]

# İstenen Sabit Başlık (Değişmedi)
header_content = """#EXTM3U
#EXT-X-VERSION:3
#EXT-X-STREAM-INF:BANDWIDTH=5500000,AVERAGE-BANDWIDTH=8976000,RESOLUTION=1920x1080,CODECS="avc1.640028,mp4a.40.2",FRAME-RATE=25"""

print("📂 Dosyalar oluşturuluyor...")

# 2. BÖLÜM: Kanalları Çek ve Dosyaya Yaz (Düzeltildi)
for channel_id in channel_ids:
    channel_url = f"{domain}/channel.html?id={channel_id}"
    try:
        # ÖNEMLİ: Siteye "Ben senin ana sayfandan geldim" diyoruz (Referer)
        req_headers = HEADERS.copy()
        req_headers['Referer'] = domain + "/"
        
        r = requests.get(channel_url, headers=req_headers, timeout=5, verify=False)
        
        # DÜZELTME: Regex artık büyük/küçük harf (BASE_URL) ve tırnak işaretlerine duyarlı değil, hepsini yakalar.
        match = re.search(r'const\s+BASE_URL\s*=\s*["\'](.*?)["\']', r.text, re.IGNORECASE)
        
        if match:
            baseurl = match.group(1)
            full_url = f"{baseurl}{channel_id}.m3u8"
            
            # Dosya içeriğini hazırla
            file_content = f"{header_content}\n{full_url}"
            
            # Her kanal için ayrı dosya kaydet
            file_path = os.path.join(output_folder, f"{channel_id}.m3u8")
            
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(file_content)
                
            print(f"✅ {channel_id}.m3u8 oluşturuldu.")
        else:
            print(f"⚠️ {channel_id} için yayın linki (BASE_URL) bulunamadı.")
            
    except Exception as e:
        print(f"❌ {channel_id} hatası: {e}")
        continue

print("\n🏁 İşlem tamamlandı.")
