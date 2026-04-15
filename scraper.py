import requests
from bs4 import BeautifulSoup
import json
import os

def scrape_hakoniwalily():
    url = "https://hakoniwalily.jp/news/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    try:
        response = requests.get(url, headers=headers)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, "html.parser")
        
        # 抓取新聞列表區塊
        articles = soup.select("article")
        new_events = []

        for article in articles:
            # 抓取日期 (格式通常是 YYYY.MM.DD)
            date_raw = article.select_one(".date")
            # 抓取標題
            title_raw = article.select_one(".title")
            # 抓取連結
            link_raw = article.select_one("a")

            if date_raw and title_raw:
                date_str = date_raw.get_text(strip=True).replace(".", "-")
                title_str = title_raw.get_text(strip=True)
                link_url = link_raw["href"] if link_raw else "https://hakoniwalily.jp/news/"

                new_events.append({
                    "title": title_str,
                    "start": date_str,
                    "url": link_url,
                    "description": title_str
                })

        return new_events
    except Exception as e:
        print(f"爬取失敗: {e}")
        return []

def save_and_merge_events(new_events):
    file_name = 'events.json'
    
    # 1. 讀取現有資料
    if os.path.exists(file_name):
        try:
            with open(file_name, 'r', encoding='utf-8') as f:
                existing_events = json.load(f)
        except:
            existing_events = []
    else:
        existing_events = []

    # 2. 建立現有活動的「唯一識別集」 (用 標題 + 日期 判斷)
    # 這樣可以防止重複抓取相同的活動
    existing_ids = {f"{ev['title']}_{ev['start']}" for ev in existing_events}

    # 3. 合併資料
    added_count = 0
    for event in new_events:
        event_id = f"{event['title']}_{event['start']}"
        if event_id not in existing_ids:
            existing_events.append(event)
            added_count += 1

    # 4. 排序 (讓最新的活動在 JSON 裡也保持整齊，可選)
    existing_events.sort(key=lambda x: x['start'], reverse=True)

    # 5. 寫回檔案
    with open(file_name, 'w', encoding='utf-8') as f:
        json.dump(existing_events, f, ensure_ascii=False, indent=2)
    
    print(f"成功合併！新增了 {added_count} 個新活動，目前總計有 {len(existing_events)} 個歷史活動。")

if __name__ == "__main__":
    print("開始爬取ハコリリ官網...")
    latest_news = scrape_hakoniwalily()
    if latest_news:
        save_and_merge_events(latest_news)
    else:
        print("未抓取到任何新資料。")
