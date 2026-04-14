
import requests
from bs4 import BeautifulSoup
import json
import re

def scrape_hakolili():
    url = "https://hakoniwalily.jp/news/"
    headers = {"User-Agent": "Mozilla/5.0"}
    
    response = requests.get(url, headers=headers)
    response.encoding = 'utf-8'
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # 1. 抓取新聞列表
    articles = soup.select('ul.p-news-list li') 
    events = []

    for item in articles:
        title_el = item.select_one('.p-news-list__item-title')
        if not title_el: continue
        title = title_el.get_text(strip=True)
        
        # 只過濾有「開催決定」的新聞
        if "開催決定" in title:
            link_el = item.select_one('a')
            full_link = link_el['href'] if link_el['href'].startswith('http') else f"https://hakoniwalily.jp{link_el['href']}"
            
            # --- 關鍵步驟：進入內文頁面抓取真實日期 ---
            inner_res = requests.get(full_link, headers=headers)
            inner_res.encoding = 'utf-8'
            inner_soup = BeautifulSoup(inner_res.text, 'html.parser')
            content_text = inner_soup.get_text()

            # 使用正規表達式尋找日期格式如：2026年6月28日 或 2026.06.28
            date_match = re.search(r'(\d{4})年(\d{1,2})月(\d{1,2})日', content_text)
            if not date_match:
                date_match = re.search(r'(\d{4})\.(\d{1,2})\.(\d{1,2})', content_text)

            if date_match:
                # 格式化為 YYYY-MM-DD
                event_date = f"{date_match.group(1)}-{int(date_match.group(2)):02d}-{int(date_match.group(3)):02d}"
            else:
                # 如果內文沒找到，才勉強用列表頁的發布日期
                list_date_el = item.select_one('.p-news-list__item-date')
                event_date = list_date_el.get_text(strip=True).replace('.', '-') if list_date_el else ""

            events.append({
                "title": title,
                "start": event_date,
                "url": full_link,
                "allDay": True
            })

    # 存檔
    with open('events.json', 'w', encoding='utf-8') as f:
        json.dump(events, f, ensure_ascii=False, indent=4)
    print(f"成功更新！共抓取 {len(events)} 筆活動。")

if __name__ == "__main__":
    scrape_hakolili()
