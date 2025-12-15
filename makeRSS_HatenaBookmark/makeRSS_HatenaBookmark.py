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
    
    # dequeで末尾N行を効率的に取得
    with open(csv_file, 'r', encoding='utf-8-sig', newline='') as f:
        reader = csv.DictReader(f)
        last_n = deque(reader, maxlen=n)
    
    # 逆順にして返す（最新が先頭）
    return list(reversed(last_n))

def main():
    print("スクリプト開始！")
    
    # 初期設定
    url = "https://b.hatena.ne.jp/entrylist/it/AI%E3%83%BB%E6%A9%9F%E6%A2%B0%E5%AD%A6%E7%BF%92"
    output_file = "makeRSS_HatenaBookmark.xml"
    csv_file = "makeRSS_HatenaBookmark.csv"

    print(f"初期URL: {url}")

    # 既存リンクのみ読み込み（軽量）
    existing_links = load_existing_links(csv_file)
    print(f"既存リンク数: {len(existing_links)}")

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
            print("リクエスト失敗！")
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

    # 新規アイテムをCSV末尾に追記（高速）
    append_csv(csv_file, new_items)
    print(f"CSV追記完了: {len(new_items)} items added")
    
    # XMLは最新300件（CSV末尾300行を逆順で取得）
    xml_items = read_last_n_lines(csv_file, MAX_XML_ITEMS)

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
