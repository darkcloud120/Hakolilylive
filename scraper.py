import requests
from bs4 import BeautifulSoup
import json
import os
import time

def scrape_article_image(article_url):
    """點進新聞內頁抓取第一張大圖"""
    try:
        # 稍微延遲一下，當個有禮貌的爬蟲
        time.sleep(1) 
        response = requests.get(article_url)
        soup = BeautifulSoup(response.text, "html.parser")
        # 通常官網內頁的文章內容會放在 .content 或 article 標籤內
        # 這裡嘗試抓取第一張 img
        img_tag = soup.select_one(".post-content img") or soup.select_one("article img")
        if img_tag and img_tag.get("src"):
            img_url = img_tag["src"]
            # 處理相對路徑轉絕對路徑
            if img_url.startswith("/"):
                return "https://hakoniwalily.jp" + img_url
            return img_url
    except:
        return None
    return None

def scrape_hakoniwalily():
    url = "https://hakoniwalily.jp/news/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    try:
        response = requests.get(url, headers=headers)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, "html.parser")
        
        articles = soup.select("article")
        new_events = []

        for article in articles:
            date_raw = article.select_one(".date")
            title_raw = article.select_one(".title")
            link_raw = article.select_one("a")

            if date_raw and title_raw:
                date_str = date_raw.get_text(strip=True).replace(".", "-")
                title_str = title_raw.get_text(strip=True)
                link_url = link_raw["href"] if link_raw else "https://hakoniwalily.jp/news/"

                # --- 修正處：如果連結不是官網新聞，就不抓圖以免出錯 ---
                image_url = None
                if "hakoniwalily.jp" in link_url:
                    print(f"正在偵測圖片: {title_str}...")
                    image_url = scrape_article_image(link_url)

                new_events.append({
                    "title": title_str,
                    "start": date_str,
                    "url": link_url,
                    "description": title_str,
                    "image": image_url # 存入圖片網址
                })

        return new_events
    except Exception as e:
        print(f"爬取失敗: {e}")
        return []

def save_and_merge_events(new_events):
    file_name = 'events.json'
    if os.path.exists(file_name):
        try:
            with open(file_name, 'r', encoding='utf-8') as f:
                existing_events = json.load(f)
        except: existing_events = []
    else: existing_events = []

    existing_ids = {f"{ev['title']}_{ev['start']}" for ev in existing_events}

    added_count = 0
    for event in new_events:
        event_id = f"{event['title']}_{event['start']}"
        if event_id not in existing_ids:
            existing_events.append(event)
            added_count += 1
        else:
            # 如果已經存在，但舊資料沒圖片，新資料有，則更新圖片
            for ex_ev in existing_events:
                if f"{ex_ev['title']}_{ex_ev['start']}" == event_id and not ex_ev.get("image") and event.get("image"):
                    ex_ev["image"] = event["image"]

    existing_events.sort(key=lambda x: x['start'], reverse=True)

    with open(file_name, 'w', encoding='utf-8') as f:
        json.dump(existing_events, f, ensure_ascii=False, indent=2)
    
    print(f"成功合併！新增了 {added_count} 個新活動。")

if __name__ == "__main__":
    latest_news = scrape_hakoniwalily()
    if latest_news:
        save_and_merge_events(latest_news)
