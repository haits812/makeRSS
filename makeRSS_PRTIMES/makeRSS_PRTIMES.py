import requests
import re
import xml.etree.ElementTree as ET
from xml.dom import minidom
import os
import csv
from collections import deque

MAX_XML_ITEMS = 300  # XMLに保持する最大アイテム数
FIELDNAMES = ['title', 'link', 'description', 'pubDate']

def load_existing_links(csv_file):
    """CSVからリンクのみ読み込む（重複チェック用・軽量）"""
    existing_links = set()
    if os.path.exists(csv_file):
        with open(csv_file, 'r', encoding='utf-8-sig', newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                existing_links.add(row['link'])
    return existing_links

def append_csv(csv_file, items):
    """新規アイテムをCSV末尾に追記（高速）"""
    if not items:
        return
    file_exists = os.path.exists(csv_file) and os.path.getsize(csv_file) > 0
    with open(csv_file, 'a', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        if not file_exists:
            writer.writeheader()
        writer.writerows(items)

def read_last_n_lines(csv_file, n):
    """CSVの末尾N行を読み込む（最新N件取得用）"""
    if not os.path.exists(csv_file):
        return []
    
    with open(csv_file, 'r', encoding='utf-8-sig', newline='') as f:
        reader = csv.DictReader(f)
        last_n = deque(reader, maxlen=n)
    
    return list(reversed(last_n))

def fetch_and_update_feed(feed):
    url = feed["url"]
    includeWords = feed["includeWords"]
    output_file = feed["output_file"]
    csv_file = output_file.replace('.xml', '.csv')
    
    # 既存リンクのみ読み込み（軽量）
    existing_links = load_existing_links(csv_file)
    print(f"{output_file}: 既存リンク数 {len(existing_links)}")
    
    # 新しいフィードを取得
    response = requests.get(url)
    rss_content = response.text
    
    items = re.findall(r"<item[^>]*>([\s\S]*?)<\/item>", rss_content)
    new_items = []
    
    for item in items:
        title_match = re.search(r"<title>(.*?)<\/title>", item)
        link_match = re.search(r"<link>(.*?)<\/link>", item)
        
        if not title_match or not link_match:
            continue
            
        title = title_match.group(1)
        link = link_match.group(1)
        
        # 既存のリンクならスキップ
        if link in existing_links:
            continue
        
        description_match = re.search(r"<description>([\s\S]*?)<\/description>", item)
        date_match = re.search(r"<dc:date>(.*?)<\/dc:date>", item)
        
        if not description_match or not date_match:
            continue
            
        description = description_match.group(1)
        date = date_match.group(1)
        
        if any(word in title or word in description for word in includeWords):
            new_item = {
                'title': title,
                'link': link,
                'description': description,
                'pubDate': date
            }
            new_items.append(new_item)
            existing_links.add(link)
    
    print(f"{output_file}: 新規 {len(new_items)} items")
    
    # 新規がなければスキップ
    if not new_items:
        print(f"{output_file}: 更新スキップ")
        return

    # 新規アイテムをCSV末尾に追記（高速）
    append_csv(csv_file, new_items)
    
    # XMLは最新300件（CSV末尾300行を逆順で取得）
    xml_items = read_last_n_lines(csv_file, MAX_XML_ITEMS)
    
    # XMLを生成
    root = ET.Element("rss", version="2.0")
    channel = ET.SubElement(root, "channel")
    ET.SubElement(channel, "title").text = f"{output_file}の特定のキーワードを含むRSS"
    ET.SubElement(channel, "description").text = f"{url}から特定のキーワードを含む記事を提供します。"
    ET.SubElement(channel, "link").text = url
    
    for item_data in xml_items:
        item_elem = ET.SubElement(channel, "item")
        ET.SubElement(item_elem, "title").text = item_data['title']
        ET.SubElement(item_elem, "link").text = item_data['link']
        ET.SubElement(item_elem, "description").text = item_data['description']
        ET.SubElement(item_elem, "pubDate").text = item_data['pubDate']
    
    xml_str = ET.tostring(root)
    xml_str = re.sub(u'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', xml_str.decode()).encode()
    xml_pretty_str = minidom.parseString(xml_str).toprettyxml(indent="  ")
    xml_pretty_str = os.linesep.join([s for s in xml_pretty_str.splitlines() if s.strip()])

    with open(output_file, "w", encoding='utf-8') as f:
        f.write(xml_pretty_str)
    
    print(f"{output_file}: XML保存完了 {len(xml_items)} items")

def main():
    feeds = [
        {
            "url": "https://prtimes.jp/index.rdf",
            "includeWords": ["生成AI", "ChatGPT", "DX", "自動化", "RPA", "ノーコード", "ローコード"],
            "output_file": "makeRSS_PRTIMES_AI.xml"
        },
        {
            "url": "https://prtimes.jp/index.rdf",
            "includeWords": ["BPaaS"],
            "output_file": "makeRSS_PRTIMES_BPaaS.xml"
        },
    ]
    
    for feed in feeds:
        fetch_and_update_feed(feed)

if __name__ == "__main__":
    main()
