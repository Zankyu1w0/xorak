import requests
import re
import os

# Dosyaların karışmaması için bir klasör oluşturalım (İsteğe bağlı, kök dizine de atabilirsin)
output_folder = "streams"
if not os.path.exists(output_folder):
    os.makedirs(output_folder)

# Trgoals domain kontrol
base = "https://trgoals"
domain = ""

print("Domain aranıyor...")
for i in range(1393, 2101):
    test_domain = f"{base}{i}.xyz"
    try:
        response = requests.head(test_domain, timeout=2)
        if response.status_code == 200:
            domain = test_domain
            print(f"Güncel Domain Bulundu: {domain}")
            break
    except:
        continue

if not domain:
    print("Çalışır bir domain bulunamadı.")
    exit()

# Kanal ID'leri (Sadece ID'ler dosya adı için yeterli, isimleri sildik)
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

# İstenen Sabit Başlık
header_content = """#EXTM3U
#EXT-X-VERSION:3
#EXT-X-STREAM-INF:BANDWIDTH=5500000,AVERAGE-BANDWIDTH=8976000,RESOLUTION=1920x1080,CODECS="avc1.640028,mp4a.40.2",FRAME-RATE=25"""

print("Dosyalar oluşturuluyor...")

# Kanalları çek ve ayrı dosyalara yaz
for channel_id in channel_ids:
    channel_url = f"{domain}/channel.html?id={channel_id}"
    try:
        r = requests.get(channel_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=5)
        
        # Base URL'i yakala
        match = re.search(r'const baseurl = "(.*?)"', r.text)
        
        if match:
            baseurl = match.group(1)
            # Proxy yok, direkt link oluşturuluyor
            full_url = f"{baseurl}{channel_id}.m3u8"
            
            # Dosya içeriğini hazırla
            file_content = f"{header_content}\n{full_url}"
            
            # Her kanal için ayrı dosya kaydet (örn: streams/yayinzirve.m3u8)
            file_path = os.path.join(output_folder, f"{channel_id}.m3u8")
            
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(file_content)
                
            print(f"{channel_id}.m3u8 oluşturuldu.")
            
    except Exception as e:
        print(f"{channel_id} hatası: {e}")
        continue

print("İşlem tamamlandı.")
