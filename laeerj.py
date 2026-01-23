import requests
import re
import os
import urllib3
import warnings
from urllib.parse import urlparse, urljoin

# SSL ve uyarıları kapat
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
warnings.filterwarnings('ignore')

output_folder = "streams"
if not os.path.exists(output_folder):
    os.makedirs(output_folder)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
}

# 1. BÖLÜM: Güncel Site Domainini Bul
base_site_name = "https://trgoals"
active_domain = ""

print("🔍 Ana site domaini aranıyor...")
for i in range(1495, 2101):
    test_url = f"{base_site_name}{i}.xyz"
    try:
        response = requests.get(test_url, headers=HEADERS, timeout=1.5, verify=False)
        if response.status_code == 200:
            active_domain = test_url
            print(f"✅ Güncel Domain: {active_domain}")
            break
    except:
        continue

if not active_domain:
    print("❌ Ana site bulunamadı.")
    exit()

# Kanal Listesi
channel_ids = [
    "yayinzirve", "yayininat", "yayin1", "yayinb2", "yayinb3", "yayinb4",
    "yayinb5", "yayinbm1", "yayinbm2", "yayinss", "yayinss2", "yayint1",
    "yayint2", "yayint3", "yayint4", "yayinsmarts", "yayinsms2", "yayinnbatv", 
    "yayinex1", "yayinex2", "yayinex3", "yayinex4", "yayinex5", "yayinex6",
    "yayinex7", "yayinex8", "yayineu1", "yayineu2"
]

header_content = """#EXTM3U
#EXT-X-VERSION:3
#EXT-X-STREAM-INF:BANDWIDTH=5500000,AVERAGE-BANDWIDTH=8976000,RESOLUTION=1920x1080,CODECS="avc1.640028,mp4a.40.2",FRAME-RATE=25"""

print("📂 Yayın linkleri ayıklanıyor...")

# ENGEL LİSTESİ - Bunları asla stream domaini olarak alma
BLOCKED_DOMAINS = [
    "googletagmanager.com",
    "google-analytics.com",
    "google.com",
    "facebook.com",
    "twitter.com",
    "doubleclick.net",
    "gstatic.com",
    "youtube.com",
    "cloudflare.com",
    "jquery.com",
    "cdnjs.cloudflare.com",
    "bootstrapcdn.com",
    "fontawesome.com",
    "gravatar.com",
    "wordpress.com",
    "w.org",
    "wp.com",
    "amazonaws.com",
    "cloudfront.net"
]

# İLGİLİ ANAHTAR KELİMELER - Stream domainlerinde genelde bunlar olur
STREAM_KEYWORDS = [
    'stream', 'live', 'tv', 'play', 'watch', 'channel', 
    'hls', 'm3u8', 'iptv', 'broadcast', 'video', 'cast',
    'atadan', 'trgoals', 'goals', 'sport', 'match', 'football'
]

def is_likely_stream_domain(url):
    """Bir domainin stream domaini olma ihtimalini kontrol et"""
    parsed = urlparse(url)
    domain = parsed.netloc.lower()
    
    # 1. Engel listesinde mi kontrol et
    for blocked in BLOCKED_DOMAINS:
        if blocked in domain:
            return False
    
    # 2. Domain çok kısa veya çok uzun mu?
    if len(domain) < 8 or len(domain) > 50:
        return False
    
    # 3. IP adresi mi? (192.168.1.1 gibi)
    if re.match(r'^\d+\.\d+\.\d+\.\d+$', domain.replace('/', '').split(':')[0]):
        return False
    
    # 4. Popüler CDN/analytics domainleri
    if any(x in domain for x in ['cdn.', 'analytics.', 'track.', 'stat.', 'metric.', 'tag.']):
        return False
    
    # 5. Stream domaininde olması muhtemel kelimeler
    if any(keyword in domain for keyword in STREAM_KEYWORDS):
        return True
    
    # 6. Domain uzantısı kontrolü
    valid_extensions = ['.com', '.net', '.xyz', '.live', '.me', '.org', '.tv', '.io', '.cc']
    if any(domain.endswith(ext) for ext in valid_extensions):
        # 7. Rakam içeriyor mu? (atadan28828282 gibi)
        if re.search(r'\d', domain):
            return True
        
        # 8. Kısa ve basit domain mi?
        if len(domain.split('.')[0]) <= 15:
            return True
    
    return False

def extract_stream_domain_from_page(html_content, channel_id):
    """Sayfadan stream domainini çıkar"""
    # ÖNCE: JavaScript kodlarındaki B_URL, BASE_URL gibi değişkenlere bak
    js_patterns = [
        r'B_URL\s*=\s*["\'](https?://[^"\']+/?)["\']',
        r'BASE_URL\s*=\s*["\'](https?://[^"\']+/?)["\']',
        r'stream_url\s*=\s*["\'](https?://[^"\']+/?)["\']',
        r'video_source\s*=\s*["\'](https?://[^"\']+/?)["\']',
        r'server\s*=\s*["\'](https?://[^"\']+/?)["\']',
        r'var\s+\w+\s*=\s*["\'](https?://[^"\']+/?)["\']\s*;'
    ]
    
    for pattern in js_patterns:
        match = re.search(pattern, html_content, re.IGNORECASE)
        if match:
            url = match.group(1)
            if is_likely_stream_domain(url):
                return url.rstrip('/') + '/'
    
    # SONRA: Tüm URL'leri topla ve filtrele
    all_urls = re.findall(r'https?://[a-zA-Z0-9_.\-]+(?:\.[a-zA-Z]{2,6})+/', html_content)
    
    # URL'leri temizle ve benzersiz yap
    clean_urls = []
    for url in all_urls:
        parsed = urlparse(url)
        clean_url = f"{parsed.scheme}://{parsed.netloc}/"
        if clean_url not in clean_urls:
            clean_urls.append(clean_url)
    
    # Stream domaini için olası adayları bul
    candidate_domains = []
    for url in clean_urls:
        if is_likely_stream_domain(url):
            candidate_domains.append(url)
    
    # TEST: Her aday domain için kanal M3U8'ini kontrol et
    for domain in candidate_domains:
        test_stream_url = f"{domain.rstrip('/')}/{channel_id}.m3u8"
        try:
            test_headers = HEADERS.copy()
            test_headers['Referer'] = active_domain
            test_response = requests.head(test_stream_url, headers=test_headers, 
                                        timeout=3, verify=False, allow_redirects=True)
            
            # Başarılı yanıt veya yönlendirme varsa
            if test_response.status_code in [200, 302, 307]:
                print(f"   ✓ Test başarılı: {test_stream_url}")
                return domain.rstrip('/') + '/'
        except:
            continue
    
    # Hiçbiri çalışmazsa, ilk uygun görünen domaini kullan
    if candidate_domains:
        return candidate_domains[0]
    
    return None

# 2. BÖLÜM: Yayın Sunucusunu ve Kanalları Bul
for channel_id in channel_ids:
    target_url = f"{active_domain}/channel.html?id={channel_id}"
    try:
        req_headers = HEADERS.copy()
        req_headers['Referer'] = active_domain + "/"
        
        print(f"\n📡 {channel_id} için tarama yapılıyor...")
        r = requests.get(target_url, headers=req_headers, timeout=5, verify=False)
        
        # Stream domainini bul
        stream_domain = extract_stream_domain_from_page(r.text, channel_id)
        
        if stream_domain:
            stream_link = f"{stream_domain.rstrip('/')}/{channel_id}.m3u8"
            
            # Linkin çalışıp çalışmadığını kontrol et
            try:
                test_resp = requests.head(stream_link, headers=req_headers, 
                                        timeout=3, verify=False, allow_redirects=True)
                status_ok = test_resp.status_code in [200, 302, 307]
            except:
                status_ok = False
            
            if status_ok:
                file_content = f"{header_content}\n{stream_link}"
                file_path = os.path.join(output_folder, f"{channel_id}.m3u8")
                
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(file_content)
                print(f"✅ {channel_id}.m3u8 -> {stream_domain}")
            else:
                print(f"⚠️ {channel_id}: Link çalışmıyor: {stream_link}")
        else:
            print(f"❌ {channel_id}: Stream domaini bulunamadı")
            
            # DEBUG: Sayfadaki tüm URL'leri göster
            all_urls = re.findall(r'https?://[a-zA-Z0-9_.\-]+(?:\.[a-zA-Z]{2,6})+/', r.text)
            clean_urls = list(set([f"{urlparse(u).scheme}://{urlparse(u).netloc}/" for u in all_urls]))
            print(f"   Sayfadaki URL'ler: {clean_urls[:10]}")
            
    except Exception as e:
        print(f"❌ {channel_id} hatası: {e}")

print("\n🏁 Tüm işlemler bitti. 'streams' klasörünü kontrol et.")

# 3. BÖLÜM: Çalışan kanalları birleştir
print("\n🔗 Çalışan kanalları birleştiriyorum...")
all_streams_file = os.path.join(output_folder, "all_streams.m3u")
try:
    with open(all_streams_file, "w", encoding="utf-8") as master_file:
        master_file.write("#EXTM3U\n")
        
        working_channels = 0
        for channel_id in channel_ids:
            channel_file = os.path.join(output_folder, f"{channel_id}.m3u8")
            if os.path.exists(channel_file):
                with open(channel_file, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                    if content:
                        master_file.write(content + "\n")
                        working_channels += 1
        
    print(f"✅ {working_channels} kanal birleştirildi: {all_streams_file}")
    
    # Çalışmayan kanalları göster
    total = len(channel_ids)
    print(f"📊 Durum: {working_channels}/{total} kanal çalışıyor")
    
except Exception as e:
    print(f"❌ Birleştirme hatası: {e}")
