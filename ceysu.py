import requests
import re
import os
import warnings
warnings.filterwarnings("ignore")

# ============================================================
# AYARLAR
# ============================================================
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/121.0.0.0 Safari/537.36"
    ),
    "Referer": "https://www.google.com/"
}

OUTPUT_FOLDER = "yula"

# KANAL EŞLEMELERİ: (kaynak_id, çıktı_dosya_adı)
CHANNEL_MAP = [
    ("bein-sports-1", "ceydub1"),
    ("bein1", "arda"),
    ("bein-sports-2", "ceydub2"),
    ("bein-sports-3", "ceydub3"),
    ("bein-sports-4", "ceydub4"),
    ("s-sport", "ceydus1"),
    ("s-sport-2", "ceydus2"),
    ("tivibu-spor-1", "ceydut1"),
    ("tivibu-spor-2", "ceydut2"),
    ("tivibu-spor-3", "ceydut3"),
    ("tivibu-spor-4", "ceydut4"),
]

# ============================================================
# M3U8 HEADER
# ============================================================
M3U8_HEADER = """#EXTM3U
#EXT-X-VERSION:3
#EXT-X-STREAM-INF:BANDWIDTH=5500000,AVERAGE-BANDWIDTH=8976000,RESOLUTION=1920x1080,CODECS="avc1.640028,mp4a.40.2",FRAME-RATE=25"""

# ============================================================
# DOMAIN BUL
# ============================================================
def find_active_domain():
    print("🔍 Aktif AtomSporTV domaini aranıyor...")
    for i in range(501, 1000):
        url = f"https://www.atomsportv{i}.top"
        try:
            r = requests.head(url, headers=HEADERS, timeout=2, allow_redirects=True)
            if 200 <= r.status_code < 400:
                domain = r.url.rstrip("/")
                print(f"✅ Aktif Domain: {domain}")
                return domain
        except Exception:
            continue
    
    fallback = "https://www.atomsportv501.top"
    print(f"⚠️ Varsayılan domain: {fallback}")
    return fallback

# ============================================================
# M3U8 BUL - TEK KANAL
# ============================================================
def get_m3u8(channel_id, domain):
    headers = HEADERS.copy()
    headers["Referer"] = domain
    
    try:
        # Kanal sayfası
        page_url = f"{domain}/matches?id={channel_id}"
        print(f"🔎 Kaynak kanal açılıyor: {channel_id}")
        r = requests.get(page_url, headers=headers, timeout=10)
        r.raise_for_status()
        html = r.text
        
        # Fetch endpoint
        match = re.search(r'fetch\(\s*["\']([^"\']+)["\']', html, re.IGNORECASE)
        if not match:
            print("❌ Fetch endpoint bulunamadı.")
            return None
            
        fetch_url = match.group(1).strip()
        
        # Relative URL ise domain ekle
        if fetch_url.startswith("http"):
            full_url = fetch_url
        elif fetch_url.startswith("/"):
            full_url = domain + fetch_url
        else:
            full_url = domain + "/" + fetch_url
        
        # Kanal ID endpointte yoksa ekle
        if channel_id not in full_url:
            if "?" in full_url:
                full_url += f"&id={channel_id}"
            else:
                full_url += f"?id={channel_id}"
        
        print("🔗 Fetch kaynağı bulundu.")
        
        custom_headers = headers.copy()
        custom_headers["Origin"] = domain
        r2 = requests.get(full_url, headers=custom_headers, timeout=10)
        r2.raise_for_status()
        data = r2.text
        
        # M3U8 URL'sini bul
        m3u8 = re.search(r'"deismackanal"\s*:\s*"([^"]+)"', data, re.IGNORECASE)
        if m3u8:
            url = m3u8.group(1).replace("\\/", "/").replace("\\", "")
            return url
        
        # Alternatif
        m3u8 = re.search(r'"(?:stream|url|source)"\s*:\s*"([^"]*?\.m3u8[^"]*)"', data, re.IGNORECASE)
        if m3u8:
            url = m3u8.group(1).replace("\\/", "/").replace("\\", "")
            return url
        
        # Direkt URL
        m3u8 = re.search(r'https?://[^"\'\s\\]+\.m3u8[^"\'\s\\]*', data, re.IGNORECASE)
        if m3u8:
            return m3u8.group(0).replace("\\/", "/").replace("\\", "")
        
        print("❌ M3U8 bulunamadı.")
        return None
        
    except Exception as e:
        print(f"❌ Hata: {e}")
        return None

# ============================================================
# BASE URL'DEN M3U8 OLUŞTUR
# ============================================================
def create_m3u8_from_base(base_url, channel_id, file_name):
    """
    Base URL'deki ID'yi değiştirerek yeni m3u8 URL'si oluşturur
    Örnek: https://corestream.ardastream.live//beintv/tracks-v1a1/mono.m3u8
    -> https://corestream.ardastream.live//{channel_id}/tracks-v1a1/mono.m3u8
    """
    # Base URL'i parçala
    # URL'deki son "/" dan önceki kısmı al
    parts = base_url.rsplit("/", 2)
    if len(parts) >= 2:
        # Örnek: ["https://corestream.ardastream.live//", "beintv", "tracks-v1a1/mono.m3u8"]
        base_path = parts[0]  # https://corestream.ardastream.live//
        new_url = base_path + channel_id + "/" + parts[2]
    else:
        # Fallback: direkt ID'yi ekle
        new_url = base_url.replace("beintv", channel_id)
    
    # Dosyayı oluştur
    path = os.path.join(OUTPUT_FOLDER, f"{file_name}.m3u8")
    content = M3U8_HEADER + "\n" + new_url
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"💾 {file_name}.m3u8 oluşturuldu. -> {new_url}")

# ============================================================
# ANA
# ============================================================
def main():
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    print("\n--- Ceysu Bot Başlatıldı ---\n")
    
    # Domain
    domain = find_active_domain()
    print("\n🎯 SADECE 1 KANALDAN M3U8 ÇEKİLECEK:\n")
    
    # İlk kanaldan m3u8 çek
    first_channel = CHANNEL_MAP[0]
    source_id, first_file = first_channel
    
    print(f"🔴 Kaynak kanal: {source_id} -> {first_file}")
    m3u8_url = get_m3u8(source_id, domain)
    
    if not m3u8_url:
        print("\n❌ M3U8 alınamadı.")
        return
    
    print("\n✅ GERÇEK M3U8 BULUNDU:")
    print(m3u8_url)
    print("\n📋 Bu URL'deki ID'yi değiştirerek diğer kanallar oluşturuluyor...\n")
    
    # Base URL'i al (ID'yi çıkar)
    # Örnek: https://corestream.ardastream.live//beintv/tracks-v1a1/mono.m3u8
    # Buradan "beintv" kısmı ID
    
    # Tüm kanalları oluştur
    for channel_id, file_name in CHANNEL_MAP:
        create_m3u8_from_base(m3u8_url, channel_id, file_name)
    
    print("\n======================================")
    print("✅ TAMAMLANDI")
    print(f"📁 {OUTPUT_FOLDER}/")
    print(f"📺 {len(CHANNEL_MAP)} dosya oluşturuldu.")
    print("🔗 Her kanal kendi ID'si ile oluşturuldu.")
    print("======================================")

if __name__ == "__main__":
    main()
