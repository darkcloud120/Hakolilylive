import requests
from bs4 import BeautifulSoup
import json
import re

def clean_event_title(text):
    """
    強力清洗標題，移除所有日期雜訊
    """
    if not text:
        return ""
    
    # 1. 移除常見標籤與關鍵字
    text = text.replace('NEWSEVENT', '').replace('{NEWS}{EVENT}', '').replace('開催決定', '').replace('！', '')
    
    # 2. 移除 00.00.0000 或 0000.00.00 等各式日期組合
    # 這裡的正則表達式會抓取：[數字][點/斜線/橫槓][數字][點/斜線/橫槓][數字]
    text = re.sub(r'\d{1,4}[\.\/\-]\d{1,2}[\.\/\-]\d{1,4}', '', text)
    
    # 3. 移除開頭或結尾可能殘留的 00.00 格式 (例如 04.02)
    text = re.sub(r'^\d{1,2}[\.\/\-]\d{1,2}\s*', '', text)
    text = re.sub(r'\s*\d{1,2}[\.\/\-]\d{1,2}$', '', text)
    
    # 4. 移除所有剩餘的連續 4 位以上數字 (通常是年份)
    text = re.sub(r'\d{4}', '', text)
    
    # 5. 清理多餘空白與特殊符號
    text = text.strip()
    return text

def scrape_hakolili():
    url = "https://hakoniwalily.jp/news/"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    
    print("🚀 執行標題「強力脫水」淨化中...")
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

            print(f"🔎 處理中: {full_url}")
            inner_res = requests.get(full_url, headers=headers)
            inner_res.encoding = 'utf-8'
            inner_soup = BeautifulSoup(inner_res.text, 'html.parser')
            lines = [l.strip() for l in inner_soup.get_text().split('\n') if l.strip()]
            
            event_title = ""
            event_date = ""

            # 解析內文
            for i, line in enumerate(lines):
                if "タイトル" in line and i + 1 < len(lines):
                    potential = lines[i+1]
                    if "▼" not in potential and "【" not in potential:
                        event_title = clean_event_title(potential)
                
                if not event_date:
                    match = re.search(r'(\d{4})年(\d{1,2})月(\d{1,2})日', line)
                    if match:
                        event_date = f"{match.group(1)}-{int(match.group(2)):02d}-{int(match.group(3)):02d}"

            # 如果內文沒抓到乾淨標題，改抓列表標題並強力清洗
            if not event_title:
                event_title = clean_event_title(a.get_text(strip=True))

            events.append({
                "title": event_title,
                "start": event_date if event_date else "2026-04-14",
                "url": full_url,
                "allDay": True,
                "description": event_title 
            })

        with open('events.json', 'w', encoding='utf-8') as f:
            json.dump(events, f, ensure_ascii=False, indent=4)
        print(f"✅ 淨化完成！共存入 {len(events)} 筆資料。")

    except Exception as e:
        print(f"❌ 發生錯誤: {e}")

if __name__ == "__main__":
    scrape_hakolili()
