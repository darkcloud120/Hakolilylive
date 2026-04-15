import requests
from bs4 import BeautifulSoup
import json
import os
import time

def scrape_article_image(article_url):
    """深度掃描內頁，尋找所有可能的圖片來源"""
    try:
        time.sleep(1.5) 
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        }
        response = requests.get(article_url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, "html.parser")
        
        # 1. 針對官網常見的 WordPress 區塊結構進行精確搜尋
        # 依序尋找：文章內的第一個圖片、文章特色圖、或是任何在內容區的圖
        img_target = soup.select_one(".post-content img") or \
                     soup.select_one(".entry-content img") or \
                     soup.select_one(".wp-block-image img") or \
                     soup.select_one("article img")
        
        if img_target:
            # 優先抓取可能存放真實網址的屬性 (處理懶加載)
            src = img_target.get("data-lazy-src") or \
                  img_target.get("data-src") or \
                  img_target.get("src")
            
            if src:
                # 排除小圖或裝飾圖
                if any(x in src.lower() for x in ["icon", "logo", "avatar", "sns", "facebook", "twitter"]):
                    return None
                
                # 轉換為絕對路徑
                full_url = src if src.startswith("http") else "https://hakoniwalily.jp" + src
                print(f"成功抓取圖片網址: {full_url}") # 讓 Actions 的 Log 看得到
                return full_url

    except Exception as e:
        print(f"抓取內頁失敗: {e}")
    return None

def scrape_hakoniwalily():
    url = "https://hakoniwalily.jp/news/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    }

    try:
        response = requests.get(url, headers=headers)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, "html.parser")
        
        # 抓取列表中的所有文章
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

                # 初始化 image 欄位為 None
                image_url = None
                
                # 只在確實有連結且是新聞內頁時才去抓圖
                if link_url and "hakoniwalily.jp" in link_url and link_url != "https://hakoniwalily.jp/news/":
                    print(f"正在分析內頁圖片: {title_str}")
                    image_url = scrape_article_image(link_url)

                new_events.append({
                    "title": title_str,
                    "start": date_str,
                    "url": link_url,
                    "description": title_str,
                    "image": image_url
                })

        return new_events
    except Exception as e:
        print(f"列表抓取失敗: {e}")
        return []

def save_and_merge_events(new_events):
    file_name = 'events.json'
    
    # 讀取現有資料
    if os.path.exists(file_name):
        try:
            with open(file_name, 'r', encoding='utf-8') as f:
                existing_events = json.load(f)
        except:
            existing_events = []
    else:
        existing_events = []

    # 建立現有資料的檢索字典
    # 用標題 + 日期 當 Key
    db = {f"{ev['title']}_{ev['start']}": ev for ev in existing_events}

    for ne in new_events:
        eid = f"{ne['title']}_{ne['start']}"
        if eid not in db:
            # 全新活動
            existing_events.append(ne)
            db[eid] = ne
        else:
            # 活動已存在，檢查是否需要補上圖片
            if not db[eid].get("image") and ne.get("image"):
                db[eid]["image"] = ne["image"]
                print(f"已為舊活動補上圖片: {ne['title']}")

    # 排序
    existing_events.sort(key=lambda x: x['start'], reverse=True)

    with open(file_name, 'w', encoding='utf-8') as f:
        json.dump(existing_events, f, ensure_ascii=False, indent=2)
    
    print(f"資料存檔完成，目前總數: {len(existing_events)}")

if __name__ == "__main__":
    latest = scrape_hakoniwalily()
    if latest:
        save_and_merge_events(latest)
