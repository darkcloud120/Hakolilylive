import requests
from bs4 import BeautifulSoup
import json
import re

def scrape_hakolili():
    url = "https://hakoniwalily.jp/news/"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    
    print("🚀 開始連線官網...")
    try:
        res = requests.get(url, headers=headers)
        res.encoding = 'utf-8'
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # 抓取所有連結，找出符合新聞格式的
        links = [a for a in soup.find_all('a', href=True) if '/news/post-' in a['href']]
        events = []
        unique_urls = set()

        for a in links:
            full_url = a['href'] if a['href'].startswith('http') else f"https://hakoniwalily.jp{a['href']}"
            if full_url in unique_urls or "開催決定" not in a.get_text(): continue
            unique_urls.add(full_url)

            print(f"🔎 進入內文: {full_url}")
            inner_res = requests.get(full_url, headers=headers)
            inner_res.encoding = 'utf-8'
            inner_soup = BeautifulSoup(inner_res.text, 'html.parser')
            
            # 取得所有純文字行
            lines = [l.strip() for l in inner_soup.get_text().split('\n') if l.strip()]
            
            event_title = a.get_text(strip=True).replace("開催決定！", "").replace("開催決定", "")
            event_date = ""

            for i, line in enumerate(lines):
                # 策略 A: 找【 タイトル 】的下一行，但排除掉常見的標籤
                if "タイトル" in line and i + 1 < len(lines):
                    potential_title = lines[i+1]
                    if "▼" not in potential_title and "【" not in potential_title:
                        event_title = potential_title
                
                # 策略 B: 找日期 (2026年6月28日)
                if not event_date:
                    match = re.search(r'(\d{4})年(\d{1,2})月(\d{1,2})日', line)
                    if match:
                        event_date = f"{match.group(1)}-{int(match.group(2)):02d}-{int(match.group(3)):02d}"

            events.append({
                "title": event_title.strip(),
                "start": event_date if event_date else "2026-04-14",
                "url": full_url,
                "allDay": True,
                "className": "fc-event-auto"
            })

        with open('events.json', 'w', encoding='utf-8') as f:
            json.dump(events, f, ensure_ascii=False, indent=4)
        print(f"✅ 成功抓取 {len(events)} 筆資料")

    except Exception as e:
        print(f"❌ 錯誤: {e}")

if __name__ == "__main__":
    scrape_hakolili()
