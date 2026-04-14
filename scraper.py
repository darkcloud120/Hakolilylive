import requests
from bs4 import BeautifulSoup
import json
import re

def scrape_hakolili():
    url = "https://hakoniwalily.jp/news/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept-Language": "ja,en-US;q=0.9,en;q=0.8"
    }
    
    print(f"開始連線: {url}")
    session = requests.Session() # 使用 Session 模擬更像真人
    response = session.get(url, headers=headers)
    response.encoding = 'utf-8'
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # 直接抓取所有 a 標籤，並過濾出 href 包含 'post-' 的連結
    all_links = soup.find_all('a', href=True)
    news_links = []
    for l in all_links:
        href = l['href']
        # 根據截圖，活動網址格式通常含有 /news/post-xxx
        if '/news/post-' in href and l.get_text(strip=True):
            news_links.append(l)

    print(f"掃描完畢，找到疑似新聞連結數量: {len(news_links)}")

    events = []
    processed_urls = set() # 避免重複抓取

    for a_tag in news_links:
        full_link = a_tag['href']
        if not full_link.startswith('http'):
            full_link = f"https://hakoniwalily.jp{full_link}"
            
        if full_link in processed_urls: continue
        processed_urls.add(full_link)

        raw_title = a_tag.get_text(strip=True)
        
        # 只要標題含有「開催決定」
        if "開催決定" in raw_title:
            print(f"🎯 發現活動: {raw_title}")
            
            inner_res = session.get(full_link, headers=headers)
            inner_res.encoding = 'utf-8'
            inner_soup = BeautifulSoup(inner_res.text, 'html.parser')
            
            inner_text = inner_soup.get_text()
            lines = [l.strip() for l in inner_text.split('\n') if l.strip()]
            
            final_title = raw_title
            event_date = ""

            for i, line in enumerate(lines):
                # 尋找【 タイトル 】
                if "タイトル" in line:
                    # 往下找第一行非空的文字作為標題
                    curr = i + 1
                    while curr < len(lines):
                        if lines[curr].strip() and "【" not in lines[curr]:
                            final_title = lines[curr].strip()
                            break
                        curr += 1
                
                # 尋找日期格式
                if not event_date:
                    date_match = re.search(r'(\d{4})年(\d{1,2})月(\d{1,2})日', line)
                    if date_match:
                        event_date = f"{date_match.group(1)}-{int(date_match.group(2)):02d}-{int(date_match.group(3)):02d}"

            # 移除標題中多餘的空格或雜質
            final_title = final_title.replace('\u3000', ' ').strip()
                
                # 尋找日期格式
                if not event_date:
                    date_match = re.search(r'(\d{4})年(\d{1,2})月(\d{1,2})日', line)
                    if date_match:
                        event_date = f"{date_match.group(1)}-{int(date_match.group(2)):02d}-{int(date_match.group(3)):02d}"

            events.append({
                "title": final_title,
                "start": event_date if event_date else "2026-06-28", # 沒日期就放預設
                "url": full_link,
                "allDay": True
            })
            print(f"   ﹂ 成功解析: {final_title} / 日期: {event_date}")

    with open('events.json', 'w', encoding='utf-8') as f:
        json.dump(events, f, ensure_ascii=False, indent=4)
    
    print(f"任務完成！存入 {len(events)} 筆資料到 events.json")

if __name__ == "__main__":
    scrape_hakolili()
