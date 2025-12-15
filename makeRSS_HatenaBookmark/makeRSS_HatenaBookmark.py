import requests
import re
import xml.etree.ElementTree as ET
from xml.dom import minidom
import os
import csv

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

def main():
    print("スクリプト開始！")
    
    # 初期設定
    url = "https://b.hatena.ne.jp/entrylist/it/AI%E3%83%BB%E6%A9%9F%E6%A2%B0%E5%AD%A6%E7%BF%92"
    output_file = "makeRSS_HatenaBookmark.xml"
    csv_file = "makeRSS_HatenaBookmark.csv"

    print(f"初期URL: {url}")

    # CSVが無ければ既存XMLから移行
    if not os.path.exists(csv_file) and os.path.exists(output_file):
        all_items, existing_links = migrate_xml_to_csv(output_file, csv_file)
    else:
        # 既存のCSVからアイテムを読み込む
        all_items, existing_links = load_existing_csv(csv_file)
    
    print(f"既存アイテム数: {len(all_items)}")

    # 初期ページ番号と最終ページ番号
    start_page = 1
    end_page = 5
    current_page = start_page
    new_items = []

    # スクレイピング処理
    while url and current_page <= end_page:
        print(f"現在のページ：{current_page}")
        
        response = requests.get(url)
        print(f"HTTPステータスコード: {response.status_code}")
        
        if response.status_code != 200:
            print("リクエスト失敗！😱")
            break
            
        html_content = response.text

        article_pattern = re.compile(r'<h3 class="entrylist-contents-title">[\s\S]*?<a href="([^"]+)"[\s\S]*?title="([^"]+)"[\s\S]*?<\/a>[\s\S]*?<li class="entrylist-contents-date">([^<]+)<\/li>[\s\S]*?<p class="entrylist-contents-description" data-gtm-click-label="entry-info-description-href">([\s\S]+?)<\/p>')
    
        for match in article_pattern.findall(html_content):
            link, title, date, description = match

            if link in existing_links:
                continue

            new_item = {
                'title': title,
                'link': link,
                'description': description,
                'pubDate': date
            }
            new_items.append(new_item)
            existing_links.add(link)

        # 次のページへ
        next_page_match = re.search(r'<a href="(/entrylist/it/AI%E3%83%BB%E6%A9%9F%E6%A2%B0%E5%AD%A6%E7%BF%92\?page=\d+)" class="js-keyboard-openable">', html_content)

        if next_page_match:
            url = 'https://b.hatena.ne.jp' + next_page_match.group(1)
        else:
            url = None

        current_page += 1

    print(f"新規アイテム数: {len(new_items)}")

    # 新しいアイテムを先頭に追加（CSVは全件保持）
    all_items = new_items + all_items
    
    # CSVに全件保存
    save_csv(csv_file, all_items)
    print(f"CSV保存完了: {len(all_items)} items")
    
    # XMLは最新500件のみ
    xml_items = all_items[:MAX_XML_ITEMS]

    # XMLを生成
    root = ET.Element("rss", version="2.0")
    channel = ET.SubElement(root, "channel")
    ET.SubElement(channel, "title").text = "はてなブックマーク AI・機械学習からの情報"
    ET.SubElement(channel, "description").text = "はてなブックマーク AI・機械学習からの情報を提供します。"
    ET.SubElement(channel, "link").text = "https://b.hatena.ne.jp/entrylist/it/AI%E3%83%BB%E6%A9%9F%E6%A2%B0%E5%AD%A6%E7%BF%92"

    for item_data in xml_items:
        item = ET.SubElement(channel, "item")
        ET.SubElement(item, "title").text = item_data['title']
        ET.SubElement(item, "link").text = item_data['link']
        ET.SubElement(item, "pubDate").text = item_data['pubDate']
        ET.SubElement(item, "description").text = item_data['description']

    xml_str = ET.tostring(root)
    xml_pretty_str = minidom.parseString(xml_str).toprettyxml(indent="  ")
    xml_pretty_str = os.linesep.join([s for s in xml_pretty_str.splitlines() if s.strip()])
    
    with open(output_file, "w", encoding='utf-8') as f:
        f.write(xml_pretty_str)

    print(f"XML保存完了: {len(xml_items)} items (最大{MAX_XML_ITEMS}件)")
    print("スクリプト終了！")

if __name__ == "__main__":
    main()
