import requests
from bs4 import BeautifulSoup
import json
import re

def scrape_hakolili():
    url = "https://hakoniwalily.jp/news/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    }
    
    print(f"開始連線: {url}")
    session = requests.Session()
    try:
        response = session.get(url, headers=headers)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')
        
        all_links = soup.find_all('a', href=True)
        news_links = []
        for l in all_links:
            href = l['href']
            if '/news/post-' in href and l.get_text(strip=True):
                news_links.append(l)

        print(f"找到新聞連結數量: {len(news_links)}")

        events = []
        processed_urls = set()

        for a_tag in news_links:
            full_link = a_tag['href']
            if not full_link.startswith('http'):
                full_link = f"https://hakoniwalily.jp{full_link}"
            
            if full_link in processed_urls: continue
            processed_urls.add(full_link)

            raw_title = a_tag.get_text(strip=True)
            
            if "開催決定" in raw_title:
                print(f"🎯 處理中: {raw_title}")
                
                inner_res = session.get(full_link, headers=headers)
                inner_res.encoding = 'utf-8'
                inner_soup = BeautifulSoup(inner_res.text, 'html.parser')
                
                inner_text = inner_soup.get_text()
                lines = [l.strip() for l in inner_text.split('\n') if l.strip()]
                
                final_title = raw_title
                event_date = ""

                # 精準解析內文
                for i, line in enumerate(lines):
                    # 抓取標題：尋找包含「タイトル」的括號行
                    if "【" in line and "タイトル" in line:
                        curr = i + 1
                        while curr < len(lines):
                            if lines[curr] and "【" not in lines[curr]:
                                final_title = lines[curr]
                                break
                            curr += 1
                    
                    # 抓取日期
                    if not event_date:
                        date_match = re.search(r'(\d{4})年(\d{1,2})月(\d{1,2})日', line)
                        if date_match:
                            event_date = f"{date_match.group(1)}-{int(date_match.group(2)):02d}-{int(date_match.group(3)):02d}"

                events.append({
                    "title": final_title,
                    "start": event_date if event_date else "2026-04-14",
                    "url": full_link,
                    "allDay": True
                })
                print(f"   ﹂ 成功: {final_title} / 日期: {event_date}")

        with open('events.json', 'w', encoding='utf-8') as f:
            json.dump(events, f, ensure_ascii=False, indent=4)
        
        print(f"任務完成！共存入 {len(events)} 筆資料。")

    except Exception as e:
        print(f"發生錯誤: {e}")

if __name__ == "__main__":
    scrape_hakolili()
