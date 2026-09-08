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

BASE_STREAM = "https://corestream.ardastream.live"

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

    ("tabii1", "tabii1"),
    ("tabii2", "tabii2"),
    ("tabii3", "tabii3"),
    ("tabii4", "tabii4"),
    ("tabii5", "tabii5"),
    ("tabii6", "tabii6"),
    ("tabii7", "tabii7"),
    ("tabii8", "tabii8"),
]


def create_m3u8(channel_id, file_name):
    """
    Yeni sistem:

    https://corestream.ardastream.live/bein1/tracks-v1a1/mono.m3u8

    https://corestream.ardastream.live/tabii1/tracks-v1a1/mono.m3u8
    """

    stream_url = (
        f"{BASE_STREAM}/{channel_id}/tracks-v1a1/mono.m3u8"
    )

    file_path = os.path.join(
        OUTPUT_FOLDER,
        f"{file_name}.m3u8"
    )

    content = (
        "#EXTM3U\n"
        "#EXT-X-VERSION:3\n"
        "#EXT-X-STREAM-INF:"
        "BANDWIDTH=5500000,"
        "AVERAGE-BANDWIDTH=8976000,"
        "RESOLUTION=1920x1080,"
        'CODECS="avc1.640028,mp4a.40.2",'
        "FRAME-RATE=25\n"
        f"{stream_url}\n"
    )

    with open(
        file_path,
        "w",
        encoding="utf-8"
    ) as f:
        f.write(content)

    print(f"[+] {file_name}.m3u8")
    print(f"    {stream_url}")


def check_stream(channel_id):
    """
    Kanalın yeni M3U8 adresine ulaşılıp
    ulaşılamadığını kontrol eder.
    """

    url = (
        f"{BASE_STREAM}/{channel_id}/"
        f"tracks-v1a1/mono.m3u8"
    )

    headers = HEADERS.copy()
    headers["Referer"] = BASE_STREAM + "/"

    try:
        r = requests.get(
            url,
            headers=headers,
            timeout=8
        )

        if r.status_code == 200:
            if "#EXTM3U" in r.text:
                return True

        return False

    except requests.RequestException:
        return False


def main():

    print("=" * 65)
    print("CORESTREAM M3U8 BOT")
    print("=" * 65)

    os.makedirs(
        OUTPUT_FOLDER,
        exist_ok=True
    )

    print()
    print(f"Sunucu : {BASE_STREAM}")
    print(f"Klasör : {OUTPUT_FOLDER}")
    print(f"Kanal  : {len(CHANNEL_MAP)}")
    print()

    successful = 0
    failed = 0

    for channel_id, file_name in CHANNEL_MAP:

        print(f"[>] Kontrol: {channel_id}")

        if check_stream(channel_id):

            create_m3u8(
                channel_id,
                file_name
            )

            successful += 1

        else:

            print(
                f"[-] Yayın kontrolü başarısız: "
                f"{channel_id}"
            )

            # Kontrol başarısız olsa bile dosyayı
            # oluşturmak istersen aşağıdaki satırları
            # aktif bırakıyoruz.
            create_m3u8(
                channel_id,
                file_name
            )

            failed += 1

        print()

    print("=" * 65)
    print("İŞLEM TAMAMLANDI")
    print("=" * 65)
    print(f"Başarılı kontrol : {successful}")
    print(f"Başarısız kontrol: {failed}")
    print(f"Toplam           : {len(CHANNEL_MAP)}")
    print(f"Klasör           : {OUTPUT_FOLDER}/")
    print("=" * 65)


if __name__ == "__main__":
    main()
