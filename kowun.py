import requests
import re
import os
import urllib3
import warnings

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
                base_domain = r2.headers['location'].strip().rstrip('/')
                return base_domain
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
            cust_headers = HEADERS.copy()
            cust_headers['Origin'] = base_domain
            cust_headers['Referer'] = base_domain
            r2 = requests.get(fetch_url, headers=cust_headers, timeout=10, verify=False)
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
    # Ana kanalları çekmek için liste
    main_channels = [
        {"id": "bein-sports-1", "name": "beIN Sports 1"},
        {"id": "bein-sports-2", "name": "beIN Sports 2"},
        {"id": "s-sport", "name": "S Sport 1"},
        {"id": "trt-spor", "name": "TRT Spor"}
    ]
    
    # Tabii kanalları (Tam istediğin isimlerle)
    tabii_list = ["tabii", "tabii1", "tabii2", "tabii3", "tabii4", "tabii5", "tabii6"]

    template_url = None
    template_id = None

    print(f"🚀 Kanallar taranıyor...")

    for ch in main_channels:
        url = get_channel_m3u8(ch['id'], base_domain)
        if url:
            # Şablonu yakala (Örn: içinden bein-sports-1 geçen linki al)
            if not template_url:
                template_url = url
                template_id = ch['id']
            
            with open(f"{OUTPUT_FOLDER}/{ch['id']}.m3u8", "w") as f:
                f.write(f"{M3U8_HEADER}\n{url}")
            print(f"✅ {ch['id']} kaydedildi.")

    # --- TABİİ KANALLARINI ÜRET ---
    if template_url:
        print(f"\n⚡ Tabii kanalları üretiliyor (Rakam hatası düzeltildi)...")
        for t_id in tabii_list:
            # ÖNEMLİ: Burada direkt replace(template_id, t_id) yapıyoruz 
            # template_id "bein-sports-1" olduğu için komple o metni silip "tabii1" yazar.
            final_url = template_url.replace(template_id, t_id)
            
            with open(f"{OUTPUT_FOLDER}/{t_id}.m3u8", "w") as f:
                f.write(f"{M3U8_HEADER}\n{final_url}")
            print(f"✨ {t_id}.m3u8 oluşturuldu -> Link: .../{t_id}.m3u8")

    print(f"\nİşlem bitti. 'tabii11' gibi hatalar temizlendi.")

if __name__ == "__main__":
    main()
