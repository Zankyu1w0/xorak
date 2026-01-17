import requests
from bs4 import BeautifulSoup
import re
import os
import urllib3
import warnings

# --- AYARLAR ---
warnings.filterwarnings('ignore')
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
}

# --- SABİT M3U8 BAŞLIĞI ---
M3U8_HEADER = """#EXTM3U
#EXT-X-VERSION:3
#EXT-X-STREAM-INF:BANDWIDTH=5500000,AVERAGE-BANDWIDTH=8976000,RESOLUTION=1920x1080,CODECS="avc1.640028,mp4a.40.2",FRAME-RATE=25"""

# --- YENİ PROXY ---
PROXY_PREFIX = "https://proxy.freecdn.workers.dev/?url="
START_SITE = "https://taraftariumizle.org"

# --- KLASÖR ADI ---
OUTPUT_FOLDER = "Emu"

# --- KANAL LİSTESİ ---
CHANNELS = [
    "androstreamlivebiraz1", "androstreamlivebs1", "androstreamlivebs2", "androstreamlivebs3",
    "androstreamlivebs4", "androstreamlivebs5", "androstreamlivebsm1", "androstreamlivebsm2",
    "androstreamlivess1", "androstreamlivess2", "androstreamlivets", "androstreamlivets1",
    "androstreamlivets2", "androstreamlivets3", "androstreamlivets4", "androstreamlivesm1",
    "androstreamlivesm2", "androstreamlivees1", "androstreamlivees2", "androstreamlivetb",
    "androstreamlivetb1", "androstreamlivetb2", "androstreamlivetb3", "androstreamlivetb4",
    "androstreamlivetb5", "androstreamlivetb6", "androstreamlivetb7", "androstreamlivetb8",
    "androstreamliveexn", "androstreamliveexn1", "androstreamliveexn2", "androstreamliveexn3",
    "androstreamliveexn4", "androstreamliveexn5", "androstreamliveexn6", "androstreamliveexn7",
    "androstreamliveexn8"
]

def get_src(u, ref=None):
    try:
        temp_headers = HEADERS.copy()
        if ref: temp_headers['Referer'] = ref
        r = requests.get(PROXY_PREFIX + u, headers=temp_headers, verify=False, timeout=20)
        return r.text if r.status_code == 200 else None
    except:
        return None

def main():
    if not os.path.exists(OUTPUT_FOLDER):
        os.makedirs(OUTPUT_FOLDER)

    print("--- Gelişmiş Yayın Tarayıcı Başlatıldı ---")
    
    # 1. ADIM: Aktif Sunucuyu Bul (Deep Link Scraping)
    print("🔍 Aktif yayın sunucusu aranıyor...")
    
    h1 = get_src(START_SITE)
    if not h1:
        print("❌ Ana siteye erişilemedi.")
        return

    s = BeautifulSoup(h1, 'html.parser')
    lnk = s.find('link', rel='amphtml')
    if not lnk:
        print("❌ AMP linki bulunamadı.")
        return
    amp_url = lnk.get('href')

    h2 = get_src(amp_url)
    if not h2: return

    m = re.search(r'\[src\]="appState\.currentIframe".*?src="(https?://[^"]+)"', h2, re.DOTALL)
    if not m:
        print("❌ Iframe bulunamadı.")
        return
    iframe_url = m.group(1)

    h3 = get_src(iframe_url, ref=amp_url)
    if not h3: return

    bm = re.search(r'baseUrls\s*=\s*\[(.*?)\]', h3, re.DOTALL)
    if not bm:
        print("❌ Base URL listesi alınamadı.")
        return

    cl = bm.group(1).replace('"', '').replace("'", "").replace("\n", "").replace("\r", "")
    srvs = [x.strip() for x in cl.split(',') if x.strip().startswith("http")]
    
    if not srvs:
        print("❌ Geçerli sunucu adresi bulunamadı.")
        return

    # 2. ADIM: Çalışan Sunucuyu Test Et
    active_server = None
    test_id = "androstreamlivebs1"
    
    print(f"⚡ {len(srvs)} sunucu test ediliyor...")
    for sv in srvs:
        sv = sv.rstrip('/')
        # Link yapısını düzelt
        turl = f"{sv}/{test_id}.m3u8" if "checklist" in sv else f"{sv}/checklist/{test_id}.m3u8"
        turl = turl.replace("checklist//", "checklist/")
        
        try:
            tr = requests.get(PROXY_PREFIX + turl, headers=HEADERS, verify=False, timeout=7)
            if tr.status_code == 200:
                active_server = sv
                print(f"✅ Çalışan Sunucu: {active_server}")
                break
        except:
            continue

    if not active_server:
        print("❌ Çalışan aktif bir sunucu bulunamadı.")
        return

    # 3. ADIM: Dosyaları Oluştur
    print(f"📂 Dosyalar '{OUTPUT_FOLDER}' klasörüne kaydediliyor...")
    
    count = 0
    for cid in CHANNELS:
        # Link formatını ayarla
        furl = f"{active_server}/{cid}.m3u8" if "checklist" in active_server else f"{active_server}/checklist/{cid}.m3u8"
        furl = furl.replace("checklist//", "checklist/")
        
        final_proxy_url = f"{PROXY_PREFIX}{furl}"
        file_content = f"{M3U8_HEADER}\n{final_proxy_url}"
        
        file_path = os.path.join(OUTPUT_FOLDER, f"{cid}.m3u8")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(file_content)
        
        count += 1
        print(f"💾 Güncellendi: {cid}.m3u8")

    print(f"\n✨ İŞLEM TAMAMLANDI!")
    print(f"📁 Konum: {os.path.abspath(OUTPUT_FOLDER)}")
    print(f"📊 Toplam: {count} kanal.")

if __name__ == "__main__":
    main()
            
