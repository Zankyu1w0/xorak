import requests
import re
import os
import warnings
from urllib.parse import urljoin

# ============================================================
# AYARLAR
# ============================================================

warnings.filterwarnings("ignore")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/121.0.0.0 Safari/537.36"
    ),
    "Referer": "https://www.google.com/"
}

OUTPUT_FOLDER = "yula"

# ============================================================
# SABİT M3U8 HEADER
# ============================================================

M3U8_HEADER = """#EXTM3U
#EXT-X-VERSION:3
#EXT-X-STREAM-INF:BANDWIDTH=5500000,AVERAGE-BANDWIDTH=8976000,RESOLUTION=1920x1080,CODECS="avc1.640028,mp4a.40.2",FRAME-RATE=25"""

# ============================================================
# KANAL HARİTASI
# ============================================================

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
# AKTİF DOMAIN BUL
# ============================================================

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

        except Exception:
            continue

    fallback = "https://www.atomsportv501.top"

    print(
        f"❌ Domain bulunamadı, varsayılan deneniyor: {fallback}"
    )

    return fallback


# ============================================================
# İLK KANALDAN KAYNAK ŞABLONU ÖĞREN
# ============================================================

def discover_source(channel_id, base_domain):

    print(f"\n🧠 Kaynak şablonu öğreniliyor: {channel_id}")

    local_headers = HEADERS.copy()
    local_headers["Referer"] = base_domain

    matches_url = f"{base_domain}/matches?id={channel_id}"

    try:

        response = requests.get(
            matches_url,
            headers=local_headers,
            timeout=10
        )

        response.raise_for_status()

        html = response.text

        # ----------------------------------------------------
        # FETCH URL
        # ----------------------------------------------------

        fetch_match = re.search(
            r'fetch\(\s*["\']([^"\']+)["\']',
            html,
            re.IGNORECASE
        )

        if not fetch_match:

            print("❌ Fetch endpoint bulunamadı.")

            return None

        fetch_url_part = fetch_match.group(1).strip()

        # ----------------------------------------------------
        # FETCH URL'Yİ TAM URL'YE ÇEVİR
        # ----------------------------------------------------

        if fetch_url_part.startswith("http"):

            fetch_url = fetch_url_part

        else:

            fetch_url = urljoin(
                base_domain + "/",
                fetch_url_part
            )

        # ----------------------------------------------------
        # KANAL ID'SİNİN URL'DEKİ YERİNİ BELİRLE
        # ----------------------------------------------------

        if channel_id in fetch_url:

            template_url = fetch_url.replace(
                channel_id,
                "{CHANNEL_ID}"
            )

        else:

            separator = "&" if "?" in fetch_url else "?"

            template_url = (
                f"{fetch_url}"
                f"{separator}id={{CHANNEL_ID}}"
            )

        print(f"✅ Kaynak şablonu bulundu:")
        print(f"   {template_url}")

        # ----------------------------------------------------
        # İLK KANAL İÇİN VERİYİ AL
        # ----------------------------------------------------

        test_url = template_url.replace(
            "{CHANNEL_ID}",
            channel_id
        )

        custom_headers = local_headers.copy()
        custom_headers["Origin"] = base_domain

        response2 = requests.get(
            test_url,
            headers=custom_headers,
            timeout=10
        )

        response2.raise_for_status()

        data = response2.text

        m3u8_url = extract_m3u8(data)

        if m3u8_url:

            print("✅ İlk kanalın M3U8 kaynağı bulundu.")

            return {
                "template": template_url,
                "headers": custom_headers,
                "first_url": m3u8_url
            }

        print("❌ İlk kanalın M3U8 adresi bulunamadı.")

        return None

    except Exception as e:

        print(f"❌ Kaynak keşif hatası: {e}")

        return None


# ============================================================
# M3U8 ÇIKAR
# ============================================================

def extract_m3u8(data):

    # --------------------------------------------------------
    # deismackanal
    # --------------------------------------------------------

    match = re.search(
        r'"deismackanal"\s*:\s*"([^"]+)"',
        data,
        re.IGNORECASE
    )

    if match:

        return (
            match.group(1)
            .replace("\\/", "/")
            .replace("\\", "")
        )

    # --------------------------------------------------------
    # stream / url / source
    # --------------------------------------------------------

    match = re.search(
        r'"(?:stream|url|source)"\s*:\s*"([^"]+?\.m3u8[^"]*)"',
        data,
        re.IGNORECASE
    )

    if match:

        return (
            match.group(1)
            .replace("\\/", "/")
            .replace("\\", "")
        )

    # --------------------------------------------------------
    # Direkt M3U8 URL
    # --------------------------------------------------------

    match = re.search(
        r'https?://[^"\'\s\\]+\.m3u8(?:[^"\'\s\\]*)?',
        data,
        re.IGNORECASE
    )

    if match:

        return (
            match.group(0)
            .replace("\\/", "/")
            .replace("\\", "")
        )

    return None


# ============================================================
# ŞABLON İLE KANAL BUL
# ============================================================

def get_channel_from_template(
    channel_id,
    source_template,
    headers,
    base_domain
):

    try:

        url = source_template.replace(
            "{CHANNEL_ID}",
            channel_id
        )

        print(f"   🔗 {url}")

        response = requests.get(
            url,
            headers=headers,
            timeout=10
        )

        response.raise_for_status()

        data = response.text

        m3u8_url = extract_m3u8(data)

        if m3u8_url:

            return m3u8_url

        return None

    except Exception as e:

        print(
            f"   ⚠️ {channel_id} hata: {e}"
        )

        return None


# ============================================================
# DOSYA KAYDET
# ============================================================

def save_m3u8(file_name, m3u8_url):

    file_path = os.path.join(
        OUTPUT_FOLDER,
        f"{file_name}.m3u8"
    )

    content = (
        f"{M3U8_HEADER}\n"
        f"{m3u8_url}"
    )

    with open(
        file_path,
        "w",
        encoding="utf-8"
    ) as f:

        f.write(content)

    print(
        f"💾 Kaydedildi: {file_name}.m3u8"
    )


# ============================================================
# ANA PROGRAM
# ============================================================

def main():

    os.makedirs(
        OUTPUT_FOLDER,
        exist_ok=True
    )

    print(
        "\n--- Ceysu Bot (AtomSporTV) Başlatıldı ---\n"
    )

    # --------------------------------------------------------
    # DOMAIN
    # --------------------------------------------------------

    base_domain = find_active_atomsportv_domain()

    print(
        f"\n⚡ Linkler '{OUTPUT_FOLDER}' "
        "klasörüne yazılıyor..."
    )

    # --------------------------------------------------------
    # İLK ÇALIŞAN KANALDAN ŞABLON ÖĞREN
    # --------------------------------------------------------

    source = None
    source_channel = None

    for channel_id, file_name in CHANNEL_MAP:

        print(
            f"\n🔎 Kaynak aranıyor: "
            f"{channel_id} -> {file_name}.m3u8"
        )

        source = discover_source(
            channel_id,
            base_domain
        )

        if source:

            source_channel = channel_id

            # İlk kanalın kendi M3U8 adresini kaydet
            save_m3u8(
                file_name,
                source["first_url"]
            )

            break

    # --------------------------------------------------------
    # HİÇBİR KAYNAK BULUNAMADI
    # --------------------------------------------------------

    if not source:

        print(
            "\n❌ Hiçbir kanal için kaynak bulunamadı."
        )

        return

    # --------------------------------------------------------
    # DİĞER KANALLARI AYNI ŞABLONLA BUL
    # --------------------------------------------------------

    print(
        f"\n🚀 Kaynak şablonu '{source_channel}' "
        "kanalından alındı."
    )

    print(
        "🚀 Diğer kanallar aynı kaynak yapısıyla deneniyor...\n"
    )

    count = 1

    for channel_id, file_name in CHANNEL_MAP:

        # İlk kanalı tekrar isteme
        if channel_id == source_channel:
            continue

        print(
            f"🔎 {channel_id} -> {file_name}.m3u8"
        )

        m3u8_url = get_channel_from_template(
            channel_id,
            source["template"],
            source["headers"],
            base_domain
        )

        if m3u8_url:

            save_m3u8(
                file_name,
                m3u8_url
            )

            count += 1

        else:

            print(
                f"⚠️ Bulunamadı: {file_name}"
            )

    # --------------------------------------------------------
    # SONUÇ
    # --------------------------------------------------------

    print(
        "\n========================================"
    )

    print(
        f"✅ İŞLEM TAMAM!"
    )

    print(
        f"📁 Klasör: {OUTPUT_FOLDER}"
    )

    print(
        f"📺 Güncellenen dosya: {count}"
    )

    print(
        "========================================"
    )


# ============================================================
# ÇALIŞTIR
# ============================================================

if __name__ == "__main__":
    main()
