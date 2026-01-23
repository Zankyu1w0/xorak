import requests
import re
import os
import time
import urllib3
import warnings
from urllib.parse import urlparse

# SSL ve uyarıları kapat
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
warnings.filterwarnings('ignore')

# Çıktı klasörü
output_folder = "streams"
if not os.path.exists(output_folder):
    os.makedirs(output_folder)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1"
}

# TRGOALS ana domainini bul
def find_trgoals_domain():
    print("🎯 TRGOALS ana domaini aranıyor...")
    print("📡 Site taraması başladı (trgoals1495.xyz - trgoals2100.xyz)")
    
    base_site_name = "https://trgoals"
    active_domain = ""
    
    for i in range(1509, 2101):
        test_url = f"{base_site_name}{i}.xyz"
        try:
            response = requests.get(test_url, headers=HEADERS, timeout=2, verify=False)
            if response.status_code == 200:
                active_domain = test_url
                print(f"✅ Aktif domain bulundu: {active_domain}")
                return active_domain
            else:
                print(f"⏳ Denenen: {test_url} - Status: {response.status_code}")
        except Exception as e:
            print(f"❌ {test_url} - Hata: {type(e).__name__}")
            continue
    
    print("⚠️  Aktif domain bulunamadı!")
    return None

# JavaScript içinden baseUrl'i çıkar
def extract_baseurl_from_javascript(html_content):
    """
    JavaScript kodundan baseUrl'i çıkartır
    Örnek: baseUrl:'https://qq9.d72577a9dd0ec12.sbs/',
    """
    
    print("🔍 JavaScript içinde baseUrl aranıyor...")
    
    # 1. CONFIG objesini bul
    config_pattern = r'(?:const|let|var)?\s*CONFIG\s*=\s*{([^}]+(?:\{[^}]*\}[^}]*)*)}'
    match = re.search(config_pattern, html_content, re.DOTALL)
    
    if match:
        config_content = match.group(1)
        print("✅ CONFIG objesi bulundu")
        
        # baseUrl'i ara
        baseurl_patterns = [
            r"baseUrl\s*:\s*['\"](https?://[^'\"]+/)['\"]",
            r"baseUrl\s*=\s*['\"](https?://[^'\"]+/)['\"]",
            r"'baseUrl'\s*:\s*['\"](https?://[^'\"]+/)['\"]"
        ]
        
        for pattern in baseurl_patterns:
            base_match = re.search(pattern, config_content)
            if base_match:
                base_url = base_match.group(1)
                print(f"✅ Base URL bulundu: {base_url}")
                return base_url
    
    # 2. Direk baseUrl değişkenini ara
    direct_patterns = [
        r"baseUrl\s*=\s*['\"](https?://[^'\"]+/)['\"]",
        r"const\s+baseUrl\s*=\s*['\"](https?://[^'\"]+/)['\"]",
        r"let\s+baseUrl\s*=\s*['\"](https?://[^'\"]+/)['\"]",
        r"var\s+baseUrl\s*=\s*['\"](https?://[^'\"]+/)['\"]"
    ]
    
    for pattern in direct_patterns:
        match = re.search(pattern, html_content)
        if match:
            base_url = match.group(1)
            print(f"✅ Base URL bulundu: {base_url}")
            return base_url
    
    # 3. Tüm URL'leri tarayıp stream domaini olabilecekleri bul
    print("⚠️  Base URL direkt bulunamadı, alternatif tarama başlatılıyor...")
    
    # Tüm URL'leri topla
    all_urls = re.findall(r'https?://[a-zA-Z0-9\-_.]+(?:\.[a-zA-Z]{2,})+/', html_content)
    unique_urls = list(set(all_urls))
    
    # Stream domaini için adayları filtrele
    stream_candidates = []
    for url in unique_urls:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        
        # CDN/Analytics domainlerini filtrele
        blocked_keywords = ['google', 'facebook', 'cloudflare', 'cdn', 'analytics', 'jquery', 'bootstrap', 'gstatic']
        if any(keyword in domain for keyword in blocked_keywords):
            continue
        
        # Rakam ve harf karışımı olan domainleri önceliklendir (qq9.d72577a9dd0ec12.sbs gibi)
        if re.search(r'\d', domain) and '.' in domain:
            stream_candidates.append(url)
    
    if stream_candidates:
        # İlk adayı seç
        selected_url = stream_candidates[0]
        print(f"✅ Aday stream domain bulundu: {selected_url}")
        return selected_url
    
    print("❌ Stream domaini bulunamadı!")
    return None

# Ana işlem fonksiyonu
def main():
    print("=" * 50)
    print("🎬 TRGOALS STREAM BOT - Başlatılıyor")
    print("=" * 50)
    
    # 1. Ana domaini bul
    active_domain = find_trgoals_domain()
    if not active_domain:
        print("🚫 Program sonlandırılıyor...")
        return
    
    print(f"\n📊 Aktif Domain: {active_domain}")
    
    # 2. Kanal listesi
    channel_ids = [
        "yayinzirve", "yayininat", "yayin1", "yayinb2", "yayinb3", "yayinb4",
        "yayinb5", "yayinbm1", "yayinbm2", "yayinss", "yayinss2", "yayint1",
        "yayint2", "yayint3", "yayint4", "yayinsmarts", "yayinsms2", "yayinnbatv", 
        "yayinex1", "yayinex2", "yayinex3", "yayinex4", "yayinex5", "yayinex6",
        "yayinex7", "yayinex8", "yayineu1", "yayineu2"
    ]
    
    print(f"📺 Toplam {len(channel_ids)} kanal tarancak")
    print("-" * 50)
    
    # M3U8 header
    header_content = """#EXTM3U
#EXT-X-VERSION:3
#EXT-X-STREAM-INF:BANDWIDTH=5500000,AVERAGE-BANDWIDTH=8976000,RESOLUTION=1920x1080,CODECS="avc1.640028,mp4a.40.2",FRAME-RATE=25"""
    
    successful_channels = 0
    failed_channels = []
    
    # 3. Her kanal için işlem yap
    for idx, channel_id in enumerate(channel_ids, 1):
        print(f"\n[{idx}/{len(channel_ids)}] 🔄 {channel_id} işleniyor...")
        
        try:
            # Kanal sayfasını getir
            target_url = f"{active_domain}/channel.html?id={channel_id}"
            req_headers = HEADERS.copy()
            req_headers['Referer'] = active_domain
            
            response = requests.get(target_url, headers=req_headers, timeout=10, verify=False)
            
            if response.status_code != 200:
                print(f"   ❌ Sayfa yüklenemedi: HTTP {response.status_code}")
                failed_channels.append(channel_id)
                continue
            
            # Base URL'i çıkar
            base_url = extract_baseurl_from_javascript(response.text)
            
            if not base_url:
                print(f"   ❌ {channel_id} için stream domaini bulunamadı")
                failed_channels.append(channel_id)
                continue
            
            # M3U8 linkini oluştur
            if not base_url.endswith('/'):
                base_url += '/'
            
            stream_url = f"{base_url}{channel_id}.m3u8"
            print(f"   ✅ Stream URL: {stream_url}")
            
            # M3U8 dosyasını oluştur
            file_content = f"{header_content}\n{stream_url}"
            file_path = os.path.join(output_folder, f"{channel_id}.m3u8")
            
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(file_content)
            
            print(f"   💾 Dosya kaydedildi: {file_path}")
            successful_channels += 1
            
            # Küçük bekleme (rate limiting için)
            time.sleep(0.5)
            
        except requests.exceptions.Timeout:
            print(f"   ⏰ {channel_id} timeout hatası")
            failed_channels.append(channel_id)
        except Exception as e:
            print(f"   ❌ {channel_id} hatası: {type(e).__name__}")
            failed_channels.append(channel_id)
    
    # 4. Tüm kanalları birleştir
    print("\n" + "=" * 50)
    print("📦 Tüm kanalları birleştiriyorum...")
    
    master_file = os.path.join(output_folder, "ALL_CHANNELS.m3u")
    try:
        with open(master_file, "w", encoding="utf-8") as f:
            f.write("#EXTM3U\n")
            
            for channel_id in channel_ids:
                channel_file = os.path.join(output_folder, f"{channel_id}.m3u8")
                if os.path.exists(channel_file):
                    with open(channel_file, "r", encoding="utf-8") as cf:
                        content = cf.read().strip()
                        if content:
                            f.write(content + "\n\n")
        
        print(f"✅ Tüm kanallar birleştirildi: {master_file}")
    except Exception as e:
        print(f"❌ Birleştirme hatası: {e}")
    
    # 5. Sonuç raporu
    print("\n" + "=" * 50)
    print("📊 İŞLEM TAMAMLANDI - SONUÇ RAPORU")
    print("=" * 50)
    print(f"✅ Başarılı kanallar: {successful_channels}/{len(channel_ids)}")
    
    if failed_channels:
        print(f"❌ Başarısız kanallar: {len(failed_channels)}")
        print("   Hatalı kanallar:", ", ".join(failed_channels))
    
    print(f"\n📁 Çıktı klasörü: {os.path.abspath(output_folder)}")
    print("🎯 Her çalıştırmada güncel domainler otomatik bulunacak")
    print("⚡ Bot her çalıştığında yeni stream URL'leri alınır")
    print("=" * 50)
    
    # Klasörü aç (Windows için)
    if os.name == 'nt':
        try:
            os.startfile(os.path.abspath(output_folder))
        except:
            pass

# Ana program
if __name__ == "__main__":
    try:
        main()
        print("\n👋 Program sonlandı. Çıkmak için Enter'a basın...")
        input()
    except KeyboardInterrupt:
        print("\n\n⚠️  Program kullanıcı tarafından durduruldu!")
        print("👋 Güle güle...")
    except Exception as e:
        print(f"\n❌ Beklenmeyen hata: {e}")
        print("⚠️  Program sonlandırılıyor...")
        input()
