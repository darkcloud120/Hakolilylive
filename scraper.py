import requests
from bs4 import BeautifulSoup
import json
import re

def scrape_hakolili():
    url = "https://hakoniwalily.jp/news/"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    
    print("🚀 啟動標題精鍊計畫...")
    try:
        res = requests.get(url, headers=headers)
        res.encoding = 'utf-8'
        soup = BeautifulSoup(res.text, 'html.parser')
        
        links = [a for a in soup.find_all('a', href=True) if '/news/post-' in a['href']]
        events = []
        unique_urls = set()

        for a in links:
            full_url = a['href'] if a['href'].startswith('http') else f"https://hakoniwalily.jp{a['href']}"
            if full_url in unique_urls or "開催決定" not in a.get_text(): continue
            unique_urls.add(full_url)

            inner_res = requests.get(full_url, headers=headers)
            inner_res.encoding = 'utf-8'
            inner_soup = BeautifulSoup(inner_res.text, 'html.parser')
            
            lines = [l.strip() for l in inner_soup.get_text().split('\n') if l.strip()]
            
            event_title = ""
            event_date = ""

            for i, line in enumerate(lines):
                # 抓取標題
                if "タイトル" in line and i + 1 < len(lines):
                    potential = lines[i+1]
                    if "▼" not in potential and "【" not in potential:
                        # 清洗邏輯：刪除日期數字、NEWSEVENT、EVENT等字眼
                        clean_title = re.sub(r'\d{2}\.\d{2}\.\d{4}', '', potential) # 刪日期
                        clean_title = clean_title.replace('NEWSEVENT', '').replace('{NEWS}{EVENT}', '').strip()
                        event_title = clean_title
                
                # 抓取日期
                if not event_date:
                    match = re.search(r'(\d{4})年(\d{1,2})月(\d{1,2})日', line)
                    if match:
                        event_date = f"{match.group(1)}-{int(match.group(2)):02d}-{int(match.group(3)):02d}"

            # 如果內文沒抓到乾淨標題，就用列表標題並清洗
            if not event_title:
                event_title = a.get_text(strip=True).split('開催決定')[0]
                event_title = re.sub(r'\d{2}\.\d{2}\.\d{4}', '', event_title).strip()

            events.append({
                "title": event_title,
                "start": event_date if event_date else "2026-04-14",
                "url": full_url,
                "allDay": True,
                "className": "fc-event-auto"
            })

        with open('events.json', 'w', encoding='utf-8') as f:
            json.dump(events, f, ensure_ascii=False, indent=4)
        print(f"✨ 任務完成！已存入 {len(events)} 個乾淨的活動。")

    except Exception as e:
        print(f"❌ 錯誤: {e}")

if __name__ == "__main__":
    scrape_hakolili()
