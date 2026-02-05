import requests
import re

def get_m3u8():
    url = "https://teleontv.at.ua/"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        res = requests.get(url, headers=headers, timeout=15)
        raw = re.findall(r'https?://[^\s"\',<>]+(?:\.m3u8)', res.text)
        if not raw: return None
        
        links = []
        for r in raw:
            parts = r.split(',')
            for p in parts:
                if '.m3u8' in p:
                    links.append(re.sub(r'\[.*?\]', '', p).strip())
        
        best = ""
        for l in links:
            if "1080p" in l or "chunklist" in l:
                best = l
                break
        if not best and links: best = links[0]
        return best
    except:
        return None

def save_m3u8(link):
    content = f'#EXTM3U\n#EXT-X-VERSION:3\n#EXT-X-STREAM-INF:BANDWIDTH=5500000,AVERAGE-BANDWIDTH=8976000,RESOLUTION=1920x1080,CODECS="avc1.640028,mp4a.40.2",FRAME-RATE=25\n{link}'
    with open("tele.m3u8", "w") as f:
        f.write(content)
    print(f"Updated: {link}")

if __name__ == "__main__":
    m3u_link = get_m3u8()
    if m3u_link:
        save_m3u8(m3u_link)
        
