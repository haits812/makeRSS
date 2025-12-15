import requests
import re
import xml.etree.ElementTree as ET
import html
import os
import csv
from collections import deque

MAX_XML_ITEMS = 300  # XMLに保持する最大アイテム数
FIELDNAMES = ['title', 'link', 'pubDate']

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

url_and_xmls = [
    {
        'url': 'https://www.hinatazaka46.com/s/official/diary/member/list?ima=0000&ct=14',
        'xml': 'feed_Blog_Kosaka.xml',
        'csv': 'feed_Blog_Kosaka.csv',
    },
    {
        'url': 'https://www.hinatazaka46.com/s/official/diary/member/list?ima=0000&ct=12',
        'xml': 'feed_Blog_Kanemura.xml',
        'csv': 'feed_Blog_Kanemura.csv',
    },
    {
        'url': 'https://www.hinatazaka46.com/s/official/diary/member/list?ima=0000&ct=000',
        'xml': 'feed_Blog_Poka.xml',
        'csv': 'feed_Blog_Poka.csv',
    },
]

for url_and_xml in url_and_xmls:
    url = url_and_xml['url']
    xml_file_name = url_and_xml['xml']
    csv_file_name = url_and_xml['csv']

    # 既存リンクのみ読み込み（軽量）
    existing_links = load_existing_links(csv_file_name)
    print(f"{xml_file_name}: 既存リンク数 {len(existing_links)}")

    # HTTPリクエスト
    response = requests.get(url)
    html_content = response.text

    # 正規表現で情報を抜き出す
    link_pattern = re.compile(r'<a class="c-button-blog-detail" href="([^"]+)">個別ページ<\/a>')
    title_pattern = re.compile(r'<div class="c-blog-article__title">\s*([\s\S]*?)\s*<\/div>')
    date_pattern = re.compile(r'<div class="c-blog-article__date">\s*([\s\S]*?)\s*<\/div>')

    new_items = []
    for link, title, date in zip(link_pattern.findall(html_content), title_pattern.findall(html_content), date_pattern.findall(html_content)):
        full_link = "https://www.hinatazaka46.com" + link
        if full_link in existing_links:
            continue
        new_items.append({
            'title': html.unescape(title),
            'link': full_link,
            'pubDate': date
        })
        existing_links.add(full_link)

    print(f"{xml_file_name}: 新規アイテム数 {len(new_items)}")

    # 新規がなければスキップ
    if not new_items:
        print(f"{xml_file_name}: 更新スキップ")
        continue

    # 新規アイテムをCSV末尾に追記（高速）
    append_csv(csv_file_name, new_items)
    print(f"{xml_file_name}: CSV追記完了")

    # XMLは最新300件（CSV末尾300行を逆順で取得）
    xml_items = read_last_n_lines(csv_file_name, MAX_XML_ITEMS)

    # XML作成
    root = ET.Element("rss", version="2.0")
    channel = ET.SubElement(root, "channel")
    ET.SubElement(channel, "title").text = "Latest Blogs"
    ET.SubElement(channel, "description").text = "日向坂46 - 最新のブログ投稿"

    for item_data in xml_items:
        item = ET.SubElement(channel, "item")
        ET.SubElement(item, "title").text = item_data['title']
        ET.SubElement(item, "link").text = item_data['link']
        ET.SubElement(item, "pubDate").text = item_data['pubDate']

    # XMLファイルに保存
    tree = ET.ElementTree(root)
    ET.indent(tree, space="  ")
    tree.write(xml_file_name, encoding='utf-8', xml_declaration=True)
    print(f"{xml_file_name}: XML保存完了 {len(xml_items)} items")

print("Done!")
