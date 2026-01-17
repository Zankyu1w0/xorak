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

M3U8_HEADER = """#EXTM3U
#EXT-X-VERSION:3
#EXT-X-STREAM-INF:BANDWIDTH=5500000,AVERAGE-BANDWIDTH=8976000,RESOLUTION=1920x1080,CODECS="avc1.640028,mp4a.40.2",FRAME-RATE=25"""

START_SITE = "https://taraftariumizle.org"
OUTPUT_FOLDER = "Emu"

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

def get_clean_text(url, ref=None):
    try:
        headers = HEADERS.copy()
        if ref: headers['Referer'] = ref
        # Proxy olmadan direkt çekiyoruz
        r = requests.get(url, headers=headers, verify=False, timeout=15)
        return r.text if r.status_code == 200 else None
    except:
        return None

def main():
    if not os.path.exists(OUTPUT_FOLDER):
        os.makedirs(OUTPUT_FOLDER)

    print("🔍 En güncel domain aranıyor...")
    
    # 1. Kaynak siteden AMP ve Iframe linkini bul
    html1 = get_clean_text(START_SITE)
    if not html1: return
    
    soup = BeautifulSoup(html1, 'html.parser')
    amp_tag = soup.find('link', rel='amphtml')
    if not amp_tag: return
    amp_url = amp_tag.get('href')

    html2 = get_clean_text(amp_url)
    if not html2: return

    iframe_match = re.search(r'src="(https?://[^"]+)"', html2)
    if not iframe_match: return
    iframe_url = iframe_match.group(1)

    # 2. Iframe içinden baseUrls listesini çek
    html3 = get_clean_text(iframe_url, ref=amp_url)
    if not html3: return

    urls_match = re.search(r'baseUrls\s*=\s*\[(.*?)\]', html3, re.DOTALL)
    if not urls_match: return

    # URL listesini temizle
    raw_urls = urls_match.group(1).replace('"', '').replace("'", "").replace("\n", "").split(',')
    clean_urls = [u.strip().rstrip('/') for u in raw_urls if "http" in u]

    if not clean_urls:
        print("❌ Domain listesi boş.")
        return

    # 3. SAYISI EN BÜYÜK OLAN DOMAINI SEÇ
    # Örn: 'androstream14' > 'androstream12'
    # Sayısal değerleri bulup sıralıyoruz
    def extract_number(url):
        nums = re.findall(r'\d+', url)
        return int(nums[-1]) if nums else 0

    best_domain = max(clean_urls, key=extract_number)
    print(f"✅ En güncel domain seçildi: {best_domain}")

    # 4. Dosyaları oluştur (Proxy yok, direkt link)
    count = 0
    for cid in CHANNELS:
        # Link formatı (checklist kontrolüyle)
        final_link = f"{best_domain}/{cid}.m3u8" if "checklist" in best_domain else f"{best_domain}/checklist/{cid}.m3u8"
        final_link = final_link.replace("checklist//", "checklist/")
        
        file_content = f"{M3U8_HEADER}\n{final_link}"
        file_path = os.path.join(OUTPUT_FOLDER, f"{cid}.m3u8")
        
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(file_content)
        count += 1

    print(f"🚀 İşlem tamam! {count} dosya '{best_domain}' domaini ile güncellendi.")

if __name__ == "__main__":
    main()
