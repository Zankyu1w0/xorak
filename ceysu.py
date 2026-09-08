import requests
import re
import os
import warnings

warnings.filterwarnings("ignore")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/121.0.0.0 Safari/537.36",
    "Referer": "https://www.google.com/"
}

OUTPUT_FOLDER = "yula"

CHANNEL_MAP = [
    # Bein Sports
    ("bein-sports-1", "ceydub1"),
    ("bein1", "arda"),
    ("bein-sports-2", "ceydub2"),
    ("bein-sports-3", "ceydub3"),
    ("bein-sports-4", "ceydub4"),

    # S Sport
    ("s-sport", "ceydus1"),
    ("s-sport-2", "ceydus2"),

    # Tivibu Spor
    ("tivibu-spor-1", "ceydut1"),
    ("tivibu-spor-2", "ceydut2"),
    ("tivibu-spor-3", "ceydut3"),
    ("tivibu-spor-4", "ceydut4"),

    # Tabii
    ("tabii1", "tabii1"),
    ("tabii2", "tabii2"),
    ("tabii3", "tabii3"),
    ("tabii4", "tabii4"),
    ("tabii5", "tabii5"),
    ("tabii6", "tabii6"),
    ("tabii7", "tabii7"),
    ("tabii8", "tabii8"),
]

M3U8_HEADER = """#EXTM3U
#EXT-X-VERSION:3
#EXT-X-STREAM-INF:BANDWIDTH=5500000,AVERAGE-BANDWIDTH=8976000,RESOLUTION=1920x1080,CODECS="avc1.640028,mp4a.40.2",FRAME-RATE=25"""


def find_active_domain():
    print("Aktif domain aranıyor...")

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
                active = r.url.rstrip("/")
                print(f"[+] Aktif domain: {active}")
                return active

        except requests.RequestException:
            continue

    fallback = "https://www.atomsportv501.top"
    print(f"[-] Aktif domain bulunamadı, varsayılan kullanılıyor: {fallback}")

    return fallback


def get_m3u8(channel_id, domain):
    headers = HEADERS.copy()
    headers["Referer"] = domain

    try:
        page_url = f"{domain}/matches?id={channel_id}"

        print(f"[>] {channel_id} aranıyor...")

        r = requests.get(
            page_url,
            headers=headers,
            timeout=10
        )

        r.raise_for_status()

        html = r.text

        # fetch("...")
        match = re.search(
            r'fetch\(\s*["\']([^"\']+)["\']',
            html,
            re.IGNORECASE
        )

        if not match:
            print(f"[-] {channel_id}: fetch URL bulunamadı")
            return None

        fetch_url = match.group(1).strip()

        if fetch_url.startswith("http"):
            full_url = fetch_url

        elif fetch_url.startswith("/"):
            full_url = domain + fetch_url

        else:
            full_url = domain + "/" + fetch_url

        if channel_id not in full_url:

            if "?" in full_url:
                full_url += f"&id={channel_id}"
            else:
                full_url += f"?id={channel_id}"

        custom_headers = headers.copy()
        custom_headers["Origin"] = domain

        r2 = requests.get(
            full_url,
            headers=custom_headers,
            timeout=10
        )

        r2.raise_for_status()

        data = r2.text

        # deismackanal
        m3u8_match = re.search(
            r'"deismackanal"\s*:\s*"([^"]+)"',
            data,
            re.IGNORECASE
        )

        if m3u8_match:
            url = (
                m3u8_match.group(1)
                .replace("\\/", "/")
                .replace("\\", "")
            )

            print(f"[+] {channel_id}: M3U8 bulundu")
            return url

        # stream / url / source
        m3u8_match = re.search(
            r'"(?:stream|url|source)"\s*:\s*"([^"]*?\.m3u8[^"]*)"',
            data,
            re.IGNORECASE
        )

        if m3u8_match:
            url = (
                m3u8_match.group(1)
                .replace("\\/", "/")
                .replace("\\", "")
            )

            print(f"[+] {channel_id}: M3U8 bulundu")
            return url

        # Direkt .m3u8 URL
        m3u8_match = re.search(
            r'https?://[^"\'\s\\]+\.m3u8[^"\'\s\\]*',
            data,
            re.IGNORECASE
        )

        if m3u8_match:
            url = (
                m3u8_match.group(0)
                .replace("\\/", "/")
                .replace("\\", "")
            )

            print(f"[+] {channel_id}: M3U8 bulundu")
            return url

        print(f"[-] {channel_id}: M3U8 bulunamadı")
        return None

    except requests.RequestException as e:
        print(f"[-] {channel_id}: HTTP hatası: {e}")
        return None

    except Exception as e:
        print(f"[-] {channel_id}: Hata: {e}")
        return None


def create_m3u8_from_base(base_url, channel_id, file_name):
    try:
        domain_match = re.match(
            r'(https?://[^/]+)',
            base_url
        )

        if not domain_match:
            print(f"[-] {channel_id}: Domain alınamadı")
            return

        domain = domain_match.group(1)

        new_url = f"{domain}/hls/{channel_id}.m3u8"

        path = os.path.join(
            OUTPUT_FOLDER,
            f"{file_name}.m3u8"
        )

        content = M3U8_HEADER + "\n" + new_url + "\n"

        with open(
            path,
            "w",
            encoding="utf-8"
        ) as f:
            f.write(content)

        print(f"[+] Oluşturuldu: {path}")

    except Exception as e:
        print(f"[-] {channel_id}: Dosya oluşturma hatası: {e}")


def main():
    print("=" * 60)
    print("M3U8 OLUŞTURUCU")
    print("=" * 60)

    os.makedirs(
        OUTPUT_FOLDER,
        exist_ok=True
    )

    # Önce aktif domaini bul
    domain = find_active_domain()

    print()
    print(f"Domain: {domain}")
    print(f"Kanal sayısı: {len(CHANNEL_MAP)}")
    print()

    # İlk kanaldan temel M3U8 adresini al
    source_id = CHANNEL_MAP[0][0]

    m3u8_url = get_m3u8(
        source_id,
        domain
    )

    if not m3u8_url:
        print()
        print("[-] Temel M3U8 alınamadı.")
        print("[-] İşlem durduruldu.")
        return

    print()
    print(f"[+] Temel M3U8:")
    print(m3u8_url)
    print()

    # Listedeki bütün kanallar için dosya oluştur
    for channel_id, file_name in CHANNEL_MAP:

        create_m3u8_from_base(
            m3u8_url,
            channel_id,
            file_name
        )

    print()
    print("=" * 60)
    print("İŞLEM TAMAMLANDI")
    print("=" * 60)
    print(f"Klasör: {OUTPUT_FOLDER}/")
    print(f"Toplam kanal: {len(CHANNEL_MAP)}")


if __name__ == "__main__":
    main()
