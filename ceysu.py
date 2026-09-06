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

# SADECE BU KANALDAN GERÇEK M3U8 ÇEKİLECEK
SOURCE_CHANNEL = "bein-sports-1"

# ÇIKACAK DOSYALAR
CHANNEL_FILES = [
    "ceydub1",
    "arda",
    "ceydub2",
    "ceydub3",
    "ceydub4",
    "ceydus1",
    "ceydus2",
    "ceydut1",
    "ceydut2",
    "ceydut3",
    "ceydut4",
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
            r = requests.head(
                url,
                headers=HEADERS,
                timeout=2,
                allow_redirects=True
            )

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
# M3U8 BUL
# ============================================================

def get_m3u8(channel_id, domain):

    headers = HEADERS.copy()
    headers["Referer"] = domain

    try:

        # Kanal sayfası
        page_url = f"{domain}/matches?id={channel_id}"

        print(f"🔎 Kaynak kanal açılıyor: {channel_id}")

        r = requests.get(
            page_url,
            headers=headers,
            timeout=10
        )

        r.raise_for_status()

        html = r.text

        # Fetch endpoint
        match = re.search(
            r'fetch\(\s*["\']([^"\']+)["\']',
            html,
            re.IGNORECASE
        )

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

        r2 = requests.get(
            full_url,
            headers=custom_headers,
            timeout=10
        )

        r2.raise_for_status()

        data = r2.text

        # ----------------------------------------------------
        # M3U8 BUL
        # ----------------------------------------------------

        m3u8 = re.search(
            r'"deismackanal"\s*:\s*"([^"]+)"',
            data,
            re.IGNORECASE
        )

        if m3u8:

            url = m3u8.group(1)

            url = (
                url
                .replace("\\/", "/")
                .replace("\\", "")
            )

            return url

        # Alternatif
        m3u8 = re.search(
            r'"(?:stream|url|source)"\s*:\s*"([^"]*?\.m3u8[^"]*)"',
            data,
            re.IGNORECASE
        )

        if m3u8:

            url = m3u8.group(1)

            url = (
                url
                .replace("\\/", "/")
                .replace("\\", "")
            )

            return url

        # Direkt URL
        m3u8 = re.search(
            r'https?://[^"\'\s\\]+\.m3u8[^"\'\s\\]*',
            data,
            re.IGNORECASE
        )

        if m3u8:

            return (
                m3u8.group(0)
                .replace("\\/", "/")
                .replace("\\", "")
            )

        print("❌ M3U8 bulunamadı.")

        return None

    except Exception as e:

        print(f"❌ Hata: {e}")

        return None


# ============================================================
# DOSYA OLUŞTUR
# ============================================================

def create_file(file_name, m3u8_url):

    path = os.path.join(
        OUTPUT_FOLDER,
        f"{file_name}.m3u8"
    )

    content = (
        M3U8_HEADER
        + "\n"
        + m3u8_url
    )

    with open(
        path,
        "w",
        encoding="utf-8"
    ) as f:

        f.write(content)

    print(f"💾 {file_name}.m3u8 oluşturuldu.")


# ============================================================
# ANA
# ============================================================

def main():

    os.makedirs(
        OUTPUT_FOLDER,
        exist_ok=True
    )

    print(
        "\n--- Ceysu Bot Başlatıldı ---\n"
    )

    # Domain
    domain = find_active_domain()

    print(
        "\n🎯 SADECE TEK KANALDAN M3U8 ÇEKİLECEK:"
    )

    print(
        f"   {SOURCE_CHANNEL}\n"
    )

    # --------------------------------------------------------
    # SADECE 1 KEZ M3U8 ÇEK
    # --------------------------------------------------------

    m3u8_url = get_m3u8(
        SOURCE_CHANNEL,
        domain
    )

    if not m3u8_url:

        print(
            "\n❌ M3U8 alınamadı."
        )

        return

    print(
        "\n✅ GERÇEK M3U8 BULUNDU:"
    )

    print(
        m3u8_url
    )

    print(
        "\n📋 Aynı URL bütün dosyalara yazılıyor...\n"
    )

    # --------------------------------------------------------
    # AYNI URL'Yİ HER DOSYAYA YAZ
    # --------------------------------------------------------

    for file_name in CHANNEL_FILES:

        create_file(
            file_name,
            m3u8_url
        )

    print(
        "\n======================================"
    )

    print(
        "✅ TAMAMLANDI"
    )

    print(
        f"📁 {OUTPUT_FOLDER}/"
    )

    print(
        f"📺 {len(CHANNEL_FILES)} dosya oluşturuldu."
    )

    print(
        "🔗 Hepsinde AYNI M3U8 URL kullanılıyor."
    )

    print(
        "======================================"
    )


if __name__ == "__main__":
    main()
