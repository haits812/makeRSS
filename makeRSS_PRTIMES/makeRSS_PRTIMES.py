import requests
import re
import xml.etree.ElementTree as ET
from xml.dom import minidom
import os
import csv
from datetime import datetime

MAX_XML_ITEMS = 300  # XMLに保持する最大アイテム数

def load_existing_csv(csv_file):
    """CSVファイルから既存のアイテムを読み込む"""
    existing_items = []
    existing_links = set()
    if os.path.exists(csv_file):
        with open(csv_file, 'r', encoding='utf-8-sig', newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                existing_items.append(row)
                existing_links.add(row['link'])
    return existing_items, existing_links

def migrate_xml_to_csv(xml_file, csv_file):
    """既存のXMLからCSVにデータを移行する（初回のみ）"""
    if os.path.exists(csv_file) or not os.path.exists(xml_file):
        return [], set()
    
    print(f"Migrating data from {xml_file} to {csv_file}...")
    items = []
    links = set()
    
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()
        for item in root.findall(".//item"):
            title_elem = item.find("title")
            link_elem = item.find("link")
            desc_elem = item.find("description")
            date_elem = item.find("pubDate")
            
            if title_elem is not None and link_elem is not None:
                item_data = {
                    'title': title_elem.text or '',
                    'link': link_elem.text or '',
                    'description': desc_elem.text if desc_elem is not None else '',
                    'pubDate': date_elem.text if date_elem is not None else ''
                }
                items.append(item_data)
                links.add(item_data['link'])
        print(f"Migrated {len(items)} items from XML")
    except Exception as e:
        print(f"Error migrating XML: {e}")
    
    return items, links

def save_csv(csv_file, items):
    """全アイテムをCSVに保存"""
    if not items:
        return
    fieldnames = ['title', 'link', 'description', 'pubDate']
    with open(csv_file, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(items)

def fetch_and_update_feed(feed):
    url = feed["url"]
    includeWords = feed["includeWords"]
    output_file = feed["output_file"]
    csv_file = output_file.replace('.xml', '.csv')
    
    # CSVが無ければ既存XMLから移行
    if not os.path.exists(csv_file) and os.path.exists(output_file):
        all_items, existing_links = migrate_xml_to_csv(output_file, csv_file)
    else:
        # 既存のCSVからアイテムを読み込む
        all_items, existing_links = load_existing_csv(csv_file)
    
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
    
    # 新しいアイテムを先頭に追加（CSVは全件保持）
    all_items = new_items + all_items
    
    # CSVに全件保存
    save_csv(csv_file, all_items)
    
    # XMLは最新500件のみ
    xml_items = all_items[:MAX_XML_ITEMS]
    
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
    # 不正なXML文字を取り除く
    xml_str = re.sub(u'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', xml_str.decode()).encode()
    xml_pretty_str = minidom.parseString(xml_str).toprettyxml(indent="  ")

    # 空白行を取り除く
    xml_pretty_str = os.linesep.join([s for s in xml_pretty_str.splitlines() if s.strip()])

    with open(output_file, "w", encoding='utf-8') as f:
        f.write(xml_pretty_str)
    
    print(f"Updated {output_file}: {len(xml_items)} items in XML, {len(all_items)} total in CSV")

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

