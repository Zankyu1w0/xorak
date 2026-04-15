import requests
import re
import os
import urllib3
import warnings

# --- YAPILANDIRMA VE SSL UYARILARINI GİZLEME ---
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
warnings.filterwarnings('ignore')

START_URL = "https://url24.link/AtomSporTV"
OUTPUT_FOLDER = "atom"
GREEN = "\033[92m"
RESET = "\033[0m"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    'Referer': 'https://url24.link/'
}

M3U8_HEADER = """#EXTM3U
#EXT-X-VERSION:3
#EXT-X-STREAM-INF:BANDWIDTH=5500000,AVERAGE-BANDWIDTH=8976000,RESOLUTION=1920x1080,CODECS="avc1.640028,mp4a.40.2",FRAME-RATE=25"""

def get_base_domain():
    base_domain = "https://www.atomsportv480.top"
    try:
        r = requests.get(START_URL, headers=HEADERS, allow_redirects=False, timeout=10, verify=False)
        if 'location' in r.headers:
            loc = r.headers['location']
            r2 = requests.get(loc, headers=HEADERS, allow_redirects=False, timeout=10, verify=False)
            if 'location' in r2.headers:
                return r2.headers['location'].strip().rstrip('/')
        return base_domain
    except:
        return base_domain

def get_channel_m3u8(channel_id, base_domain):
    try:
        matches_url = f"{base_domain}/matches?id={channel_id}"
        r = requests.get(matches_url, headers=HEADERS, timeout=10, verify=False)
        fetch_match = re.search(r'fetch\(\s*["\'](.*?)["\']', r.text)
        if fetch_match:
            fetch_url = fetch_match.group(1).strip()
            if not fetch_url.endswith(channel_id): fetch_url += channel_id
            r2 = requests.get(fetch_url, headers=HEADERS, timeout=10, verify=False)
            m3u8_match = re.search(r'"(?:stream|url|source|deismackanal)":\s*"(.*?\.m3u8|.*?)"', r2.text)
            if m3u8_match:
                return m3u8_match.group(1).replace('\\', '')
        return None
    except:
        return None

def main():
    if not os.path.exists(OUTPUT_FOLDER):
        os.makedirs(OUTPUT_FOLDER)

    base_domain = get_base_domain()
    main_channels = [
        {"id": "bein-sports-1", "name": "beIN Sports 1"},
        {"id": "bein-sports-2", "name": "beIN Sports 2"},
        {"id": "trt-spor", "name": "TRT Spor"}
    ]
    
    # Senin istediğin tam liste
    tabii_list = ["tabii", "tabii1", "tabii2", "tabii3", "tabii4", "tabii5", "tabii6"]

    template_url = None

    print(f"🚀 Kanallar taranıyor...")

    for ch in main_channels:
        url = get_channel_m3u8(ch['id'], base_domain)
        if url:
            # Şablonu alırken URL'nin sonundaki /hls/ kısmına kadar olan yeri alacağız
            if not template_url:
                template_url = url
            
            with open(f"{OUTPUT_FOLDER}/{ch['id']}.m3u8", "w") as f:
                f.write(f"{M3U8_HEADER}\n{url}")
            print(f"✅ {ch['id']} kaydedildi.")

    # --- TABİİ KANALLARI ÜRETİMİ (KESİN ÇÖZÜM) ---
    if template_url:
        print(f"\n⚡ Tabii kanalları tertemiz oluşturuluyor...")
        
        # Örn: https://.../hls/bein-sports-1.m3u8 linkini / ile parçalıyoruz
        url_parts = template_url.split('/')
        # Son parçayı (bein-sports-1.m3u8 kısmını) atıyoruz, kalanları geri birleştiriyoruz
        # Böylece elimizde sadece "https://.../hls" kısmı kalıyor
        base_hls_url = "/".join(url_parts[:-1])

        for t_id in tabii_list:
            # Tertemiz link oluşturuyoruz: "https://.../hls" + "/" + "tabii1" + ".m3u8"
            final_url = f"{base_hls_url}/{t_id}.m3u8"
            
            with open(f"{OUTPUT_FOLDER}/{t_id}.m3u8", "w") as f:
                f.write(f"{M3U8_HEADER}\n{final_url}")
            print(f"✨ {t_id}.m3u8 -> İçerik: {t_id}.m3u8 (Hata Giderildi)")

    print(f"\n✅ İşlem bitti. 'tabii11' gibi saçmalıklar artık yok.")

if __name__ == "__main__":
    main()
