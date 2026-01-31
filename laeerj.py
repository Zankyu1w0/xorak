import requests
import re
import os
import urllib3
import warnings

# SSL ve uyarıları kapat
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
warnings.filterwarnings('ignore')

output_folder = "streams"
if not os.path.exists(output_folder):
    os.makedirs(output_folder)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
}

def find_real_url(start_url):
    """Zincirleme yönlendirmeleri takip ederek asıl URL'yi bul"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    visited = set()
    current_url = start_url
    
    print("🔍 Zincirleme yönlendirme takip ediliyor...")
    
    while True:
        if current_url in visited:
            print("⚠️ Döngü tespit edildi")
            break
            
        visited.add(current_url)
        print(f"  → {current_url}")
        
        try:
            r = requests.get(
                current_url,
                headers=headers,
                allow_redirects=True,
                timeout=10,
                verify=False
            )
            
            # HTTP redirect varsa
            if r.url != current_url:
                current_url = r.url
                continue
            
            html = r.text
            
            # JS + META yönlendirme yakalama
            patterns = [
                r'window\.location\.href\s*=\s*[\'"](.*?)[\'"]',
                r'window\.location\s*=\s*[\'"](.*?)[\'"]',
                r'location\.replace\([\'"](.*?)[\'"]\)',
                r'<meta[^>]+url=([^\"]+)',
                r'http-equiv=["\']refresh["\'][^>]+url=["\'](.*?)["\']'
            ]
            
            found = False
            
            for p in patterns:
                m = re.search(p, html, re.IGNORECASE)
                if m:
                    next_url = m.group(1).strip()
                    if not next_url.startswith(('http://', 'https://')):
                        # Relative URL ise base ekle
                        from urllib.parse import urljoin
                        next_url = urljoin(current_url, next_url)
                    
                    print(f"  ↪ JS/META yönlendirme: {next_url}")
                    current_url = next_url
                    found = True
                    break
            
            if not found:
                # artık asıl yer burası
                print(f"\n✅ SON ANA URL BULUNDU: {current_url}")
                return current_url
                
        except Exception as e:
            print(f"❌ Hata: {e}")
            return None

# 1. BÖLÜM: Zincirleme Yönlendirme ile Güncel Site Domainini Bul
SHORT_URL = "https://t.co/6vPuUxO91F"  # Sabit kısaltılmış URL
active_domain = ""

print("🔍 Zincirleme yönlendirme ile aktif domain aranıyor...")
final_url = find_real_url(SHORT_URL)

if final_url:
    active_domain = final_url.rstrip('/')
    print(f"✅ Güncel Domain Bulundu: {active_domain}")
else:
    # Eski yöntemle domain bul (backup)
    print("⚠️ Zincirleme çalışmadı, eski yönteme geçiliyor...")
    base_site_name = "https://trgoals"
    for i in range(1509, 2101):
        test_url = f"{base_site_name}{i}.xyz"
        try:
            response = requests.get(test_url, headers=HEADERS, timeout=1, verify=False)
            if response.status_code == 200:
                active_domain = test_url
                print(f"✅ Güncel Domain Bulundu: {active_domain}")
                break
        except:
            continue

if not active_domain:
    print("❌ Ana site bulunamadı.")
    exit()

# Kanal Listesi
channel_ids = [
    "trgoals", "zirve", "inat", "yayin1", "b2", "b3", "b4",
    "b5", "bm1", "bm2", "ss", "ss2", "t1",
    "t2", "t3", "t4", "smarts", "sms2", "nbatv", 
    "ex1", "ex2", "ex3", "ex4", "ex5", "ex6",
    "ex7", "ex8", "eu1", "eu2"
]

# Kanal isimleri (isteğe bağlı, daha okunabilir çıktı için)
channel_names = {
    "trgoals/mono": "BeIN Sports 1",
    "zirve": "BeIN Sports 1",
    "yayin1": "BeIN Sports 1",
    "inat": "BeIN Sports 1",
    "b2": "BeIN Sports 2",
    "b3": "BeIN Sports 3",
    "b4": "BeIN Sports 4",
    "b5": "BeIN Sports 5",
    "bm1": "BeIN Sports Max 1",
    "bm2": "BeIN Sports Max 2",
    "ss": "S Sport",
    "ss2": "S Sport 2",
    "t1": "Tivibu Spor 1",
    "t2": "Tivibu Spor 2",
    "t3": "Tivibu Spor 3",
    "t4": "Tivibu Spor 4",
    "smarts": "Smart Spor",
    "sms2": "Smart Spor 2",
    "nbatv": "NBA TV",
    "ex1": "Exxen 1",
    "ex2": "Exxen 2",
    "ex3": "Exxen 3",
    "ex4": "Exxen 4",
    "ex5": "Exxen 5",
    "ex6": "Exxen 6",
    "ex7": "Exxen 7",
    "ex8": "Exxen 8",
    "eu1": "EuroSport 1",
    "eu2": "EuroSport 2"
}

header_content = """#EXTM3U
#EXT-X-VERSION:3
#EXT-X-STREAM-INF:BANDWIDTH=5500000,RESOLUTION=1920x1080,FRAME-RATE=25"""

print("📂 Base URL ayıklanıyor ve tüm kanallara uygulanıyor...")

# 2. BÖLÜM: SADECE BİR KANALDAN BASEURL AYIKLA VE TÜM KANALLARA UYGULA
found_base_url = None
success_count = 0
total_channels = len(channel_ids)

# Önce bir kanalda baseUrl'i bul
for idx, channel_id in enumerate(channel_ids[:5], 1):  # İlk 5 kanalda dene
    channel_name = channel_names.get(channel_id, channel_id)
    print(f"🔍 Test kanalı {channel_name} aranıyor...")
    
    target_url = f"{active_domain}/channel.html?id={channel_id}"
    try:
        req_headers = HEADERS.copy()
        req_headers['Referer'] = active_domain + "/"
        
        r = requests.get(target_url, headers=req_headers, timeout=5, verify=False)
        
        # baseUrl: "https://.../" formatını yakala
        patterns = [
            r'CONFIG\s*=\s*{[^}]*baseUrl\s*:\s*["\'](https?://[^"\']+)["\']',
            r'baseUrl\s*[:=]\s*["\'](https?://[^"\']+)["\']',
            r'const\s+baseUrl\s*=\s*["\'](https?://[^"\']+)["\']',
            r'let\s+baseUrl\s*=\s*["\'](https?://[^"\']+)["\']',
            r'var\s+baseUrl\s*=\s*["\'](https?://[^"\']+)["\']'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, r.text, re.IGNORECASE)
            if match:
                found_base_url = match.group(1)
                break
        
        if not found_base_url:
            # Yedek regex
            backup_match = re.findall(r'["\'](https?://[a-z0-9.]+\.(?:sbs|xyz|me|live|com|net|pw)/)["\']', r.text)
            if backup_match:
                found_base_url = backup_match[0]

        if found_base_url:
            # URL'yi temizle
            found_base_url = found_base_url.strip().rstrip('/') + '/'
            print(f"✅ Base URL bulundu: {found_base_url}")
            break
        else:
            print(f"  ⚠️ {channel_name} için baseUrl bulunamadı.")
            
    except Exception as e:
        print(f"  ❌ {channel_name} hatası: {str(e)[:50]}...")

# Eğer baseUrl bulunduysa, TÜM kanallara uygula
if found_base_url:
    print(f"\n🚀 Bulunan base URL tüm kanallara uygulanıyor...")
    
    for idx, channel_id in enumerate(channel_ids, 1):
        channel_name = channel_names.get(channel_id, channel_id)
        
        # Stream linkini oluştur
        stream_link = f"{found_base_url}{channel_id}.m3u8"
        
        # M3U8 dosyasını oluştur
        file_content = f"{header_content}\n{stream_link}"
        file_path = os.path.join(output_folder, f"{channel_id}.m3u8")
        
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(file_content)
            print(f"  ✅ [{idx}/{total_channels}] {channel_name} -> {found_base_url[:40]}...")
            success_count += 1
        except Exception as e:
            print(f"  ❌ [{idx}/{total_channels}] {channel_name} kayıt hatası: {str(e)[:30]}")
else:
    print("\n❌ Base URL bulunamadı! Her kanal ayrı ayrı kontrol ediliyor...")
    
    # Eski yöntemle her kanalı ayrı ayrı kontrol et
    for idx, channel_id in enumerate(channel_ids, 1):
        channel_name = channel_names.get(channel_id, channel_id)
        print(f"[{idx}/{total_channels}] {channel_name} aranıyor...")
        
        target_url = f"{active_domain}/channel.html?id={channel_id}"
        try:
            req_headers = HEADERS.copy()
            req_headers['Referer'] = active_domain + "/"
            
            r = requests.get(target_url, headers=req_headers, timeout=5, verify=False)
            
            found_url = None
            
            patterns = [
                r'CONFIG\s*=\s*{[^}]*baseUrl\s*:\s*["\'](https?://[^"\']+)["\']',
                r'baseUrl\s*[:=]\s*["\'](https?://[^"\']+)["\']',
                r'const\s+baseUrl\s*=\s*["\'](https?://[^"\']+)["\']',
                r'let\s+baseUrl\s*=\s*["\'](https?://[^"\']+)["\']',
                r'var\s+baseUrl\s*=\s*["\'](https?://[^"\']+)["\']'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, r.text, re.IGNORECASE)
                if match:
                    found_url = match.group(1)
                    break
            
            if not found_url:
                backup_match = re.findall(r'["\'](https?://[a-z0-9.]+\.(?:sbs|xyz|me|live|com|net|pw)/)["\']', r.text)
                if backup_match:
                    found_url = backup_match[0]

            if found_url:
                found_url = found_url.strip().rstrip('/') + '/'
                stream_link = f"{found_url}{channel_id}.m3u8"
                
                file_content = f"{header_content}\n{stream_link}"
                file_path = os.path.join(output_folder, f"{channel_id}.m3u8")
                
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(file_content)
                print(f"  ✅ {channel_name} -> {found_url[:50]}...")
                success_count += 1
            else:
                print(f"  ⚠️ {channel_name} için kaynak kodda baseUrl bulunamadı.")
                
        except Exception as e:
            print(f"  ❌ {channel_name} hatası: {str(e)[:50]}...")

print(f"\n🏁 İşlem tamamlandı.")
print(f"📊 Başarılı: {success_count}/{total_channels}")
print(f"💾 Dosyalar '{output_folder}' klasöründe.")
