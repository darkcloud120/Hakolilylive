import requests
from bs4 import BeautifulSoup
import json
import re

def scrape_hakolili():
    url = "https://hakoniwalily.jp/news/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    print(f"正在連線至: {url}")
    response = requests.get(url, headers=headers)
    response.encoding = 'utf-8'
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # 診斷點 1：看看有沒有抓到任何 <li>
    articles = soup.select('ul.p-news-list li') 
    print(f"找到的列表項目數量: {len(articles)}")

    events = []

    for item in articles:
        # 診斷點 2：印出所有找到的標題，確認關鍵字
        title_el = item.select_one('.p-news-list__item-title')
        if not title_el:
            continue
            
        raw_title = title_el.get_text(strip=True)
        print(f"檢查標題: {raw_title}") # 這會在 GitHub Actions 日誌顯示

        # 放寬條件：只要有「開催」就抓，不一定要「開催決定」
        if "開催" in raw_title:
            print(f"🎯 命中目標: {raw_title}")
            link_el = item.select_one('a')
            full_link = link_el['href'] if link_el['href'].startswith('http') else f"https://hakoniwalily.jp{link_el['href']}"
            
            # 進入內文
            inner_res = requests.get(full_link, headers=headers)
            inner_res.encoding = 'utf-8'
            inner_soup = BeautifulSoup(inner_res.text, 'html.parser')
            
            # 取得內文所有文字
            inner_text = inner_soup.get_text()
            lines = [l.strip() for l in inner_text.split('\n') if l.strip()]
            
            final_title = raw_title
            event_date = ""

            # 根據你的需求：從【タイトル】下一行抓標題
            for i, line in enumerate(lines):
                if "【タイトル】" in line and i + 1 < len(lines):
                    final_title = lines[i+1]
                    print(f"   ﹂ 內文標題改為: {final_title}")
                
                # 搜尋日期 (YYYY年MM月DD日)
                if not event_date:
                    date_match = re.search(r'(\d{4})年(\d{1,2})月(\d{1,2})日', line)
                    if date_match:
                        event_date = f"{date_match.group(1)}-{int(date_match.group(2)):02d}-{int(date_match.group(3)):02d}"
                        print(f"   ﹂ 找到日期: {event_date}")

            events.append({
                "title": final_title,
                "start": event_date if event_date else "2026-04-14", # 真的找不到就放今天
                "url": full_link,
                "allDay": True
            })

    # 寫入檔案
    with open('events.json', 'w', encoding='utf-8') as f:
        json.dump(events, f, ensure_ascii=False, indent=4)
    
    print(f"任務結束。最終 events 數量: {len(events)}")

if __name__ == "__main__":
    scrape_hakolili()
