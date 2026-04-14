import requests
from bs4 import BeautifulSoup
import json
import re

def scrape_hakolili():
    url = "https://hakoniwalily.jp/news/"
    headers = {"User-Agent": "Mozilla/5.0"}
    
    try:
        response = requests.get(url, headers=headers)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')
        
        articles = soup.select('ul.p-news-list li') 
        events = []

        for item in articles:
            # 獲取列表標題，檢查關鍵字
            list_title = item.select_one('.p-news-list__item-title').get_text(strip=True)
            
            if "開催決定" in list_title:
                link_el = item.select_one('a')
                full_link = link_el['href'] if link_el['href'].startswith('http') else f"https://hakoniwalily.jp{link_el['href']}"
                
                # --- 進入內文詳情 ---
                inner_res = requests.get(full_link, headers=headers)
                inner_res.encoding = 'utf-8'
                inner_soup = BeautifulSoup(inner_res.text, 'html.parser')
                
                # 取得所有文字內容並按行切分
                lines = [line.strip() for line in inner_soup.get_text().split('\n') if line.strip()]
                
                final_title = list_title # 預設值
                event_date = ""

                # 遍歷每一行來精準找標題與日期
                for i, line in enumerate(lines):
                    # 1. 抓取標題：找【タイトル】的下一行
                    if "【タイトル】" in line and i + 1 < len(lines):
                        final_title = lines[i+1]
                    
                    # 2. 抓取日期：找 2026年04月14日 格式
                    if not event_date:
                        date_match = re.search(r'(\d{4})年(\d{1,2})月(\d{1,2})日', line)
                        if date_match:
                            event_date = f"{date_match.group(1)}-{int(date_match.group(2)):02d}-{int(date_match.group(3)):02d}"

                # 如果還是沒抓到日期，嘗試抓 2026.04.14 格式
                if not event_date:
                    date_match = re.search(r'(\d{4})\.(\d{1,2})\.(\d{1,2})', inner_soup.get_text())
                    if date_match:
                        event_date = f"{date_match.group(1)}-{int(date_match.group(2)):02d}-{int(date_match.group(3)):02d}"

                events.append({
                    "title": final_title,
                    "start": event_date if event_date else "TBD", # 若沒日期標註待定
                    "url": full_link,
                    "allDay": True
                })

        # 寫入檔案
        with open('events.json', 'w', encoding='utf-8') as f:
            json.dump(events, f, ensure_ascii=False, indent=4)
            
        print(events)
        print(f"完成！抓取到 {len(events)} 個活動。")

    except Exception as e:
        print(f"錯誤發生: {e}")

if __name__ == "__main__":
    scrape_hakolili()
