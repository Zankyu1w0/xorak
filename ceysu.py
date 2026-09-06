import requests
import re
import os
import warnings

# --- AYARLAR ---
warnings.filterwarnings("ignore")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/121.0.0.0 Safari/537.36"
    ),
    "Referer": "https://www.google.com/"
}

# --- KLASÖR ADI ---
OUTPUT_FOLDER = "yula"

# --- SABİT M3U8 BAŞLIĞI ---
M3U8_HEADER = """#EXTM3U
#EXT-X-VERSION:3
#EXT-X-STREAM-INF:BANDWIDTH=5500000,AVERAGE-BANDWIDTH=8976000,RESOLUTION=1920x1080,CODECS="avc1.640028,mp4a.40.2",FRAME-RATE=25"""

# --- KANAL HARİTASI ---
# Site ID -> Senin istediğin dosya adı
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


# --- ATOMSPORTV DOMAIN TARAMA ---

def find_active_atomsportv_domain():
    print("🔍 Aktif AtomSporTV domaini aranıyor (501-999)...")

    for i in range(501, 1000):
        url = f"https://www.atomsportv{i}.top"

        try:
            response = requests.head(
                url,
                headers=HEADERS,
                timeout=2,
                allow_redirects=True
            )

            if 200 <= response.status_code < 400:
                final_url = response.url.rstrip("/")
                print(f"✅ Aktif Domain: {final_url}")
                return final_url

        except requests.RequestException:
            continue
        except Exception:
            continue

    fallback = "https://www.atomsportv501.top"

    print(
        f"❌ Domain bulunamadı, varsayılan deneniyor: {fallback}"
    )

    return fallback


# --- M3U8 BULMA ---

def get_channel_m3u8(channel_id, base_domain):
    local_headers = HEADERS.copy()
    local_headers["Referer"] = base_domain

    try:
        # 1. matches?id= endpoint
        matches_url = (
            f"{base_domain}/matches?id={channel_id}"
        )

        response = requests.get(
            matches_url,
            headers=local_headers,
            timeout=10
        )

        response.raise_for_status()

        html = response.text

        # 2. fetch URL'sini bul
        fetch_match = re.search(
            r'fetch\(\s*["\'](.*?)["\']',
            html,
            re.IGNORECASE
        )

        if not fetch_match:
            return None

        fetch_url_part = fetch_match.group(1).strip()

        custom_headers = local_headers.copy()
        custom_headers["Origin"] = base_domain

        # 3. Fetch URL oluştur
        if fetch_url_part.startswith("http"):
            fetch_url = fetch_url_part
        elif fetch_url_part.startswith("/"):
            fetch_url = f"{base_domain}{fetch_url_part}"
        else:
            fetch_url = f"{base_domain}/{fetch_url_part}"

        # Kanal ID URL'de yoksa ekle
        if not fetch_url.rstrip("/").endswith(channel_id):
            if "?" in fetch_url:
                fetch_url = f"{fetch_url}&id={channel_id}"
            else:
                fetch_url = (
                    f"{fetch_url.rstrip('/')}/{channel_id}"
                )

        # 4. Fetch isteği
        response2 = requests.get(
            fetch_url,
            headers=custom_headers,
            timeout=10
        )

        response2.raise_for_status()

        fetch_data = response2.text

        # 5. deismackanal alanını ara
        m3u8_match = re.search(
            r'"deismackanal"\s*:\s*"([^"]+)"',
            fetch_data,
            re.IGNORECASE
        )

        # 6. Alternatif alanları ara
        if not m3u8_match:
            m3u8_match = re.search(
                r'"(?:stream|url|source)"\s*:\s*"([^"]*?\.m3u8[^"]*)"',
                fetch_data,
                re.IGNORECASE
            )

        # 7. Herhangi bir .m3u8 URL'si ara
        if not m3u8_match:
            m3u8_match = re.search(
                r'https?://[^"\'\s\\]+\.m3u8(?:[^"\'\s\\]*)?',
                fetch_data,
                re.IGNORECASE
            )

            if m3u8_match:
                return m3u8_match.group(0).replace("\\", "")

        if m3u8_match:
            return m3u8_match.group(1).replace("\\", "")

        return None

    except requests.RequestException as e:
        print(f"   ⚠️ İstek hatası: {e}")
        return None

    except Exception as e:
        print(f"   ⚠️ Hata: {e}")
        return None


# --- ANA PROGRAM ---

def main():

    # Klasör oluştur
    os.makedirs(
        OUTPUT_FOLDER,
        exist_ok=True
    )

    print(
        "--- Ceysu Bot (AtomSporTV) Başlatıldı ---"
    )

    # 1. Aktif domain bul
    base_domain = find_active_atomsportv_domain()

    print(
        f"\n⚡ Linkler '{OUTPUT_FOLDER}' "
        "klasörüne yazılıyor...\n"
    )

    count = 0

    # 2. Kanalları tara
    for site_id, file_name in CHANNEL_MAP:

        print(
            f"🔎 Taranıyor: {site_id} -> {file_name}.m3u8"
        )

        m3u8_url = get_channel_m3u8(
            site_id,
            base_domain
        )

        if m3u8_url:

            # Dosya içeriği
            file_content = (
                f"{M3U8_HEADER}\n"
                f"{m3u8_url}"
            )

            # Dosya yolu
            file_path = os.path.join(
                OUTPUT_FOLDER,
                f"{file_name}.m3u8"
            )

            # Dosyayı yaz
            with open(
                file_path,
                "w",
                encoding="utf-8"
            ) as f:
                f.write(file_content)

            print(
                f"💾 Kaydedildi: {file_name}.m3u8"
            )

            count += 1

        else:
            print(
                f"⚠️ Bulunamadı: {file_name} "
                f"(Kaynak: {site_id})"
            )

    print(
        f"\n✅ İŞLEM TAMAM! "
        f"Toplam {count} dosya güncellendi."
    )


if __name__ == "__main__":
    main()
