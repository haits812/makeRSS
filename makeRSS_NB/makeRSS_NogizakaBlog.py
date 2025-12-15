import os
import re
import requests
import xml.etree.ElementTree as ET
from xml.dom import minidom
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
        'url': 'https://www.nogizaka46.com/s/n46/diary/MEMBER/list?page=0&ct=55387&cd=MEMBER',
        'xml': 'feed_Blog_YumikiNao.xml',
        'csv': 'feed_Blog_YumikiNao.csv',
        'include_phrase': [],
    },
    {
        'url': 'https://www.nogizaka46.com/s/n46/diary/MEMBER/list?page=0&ct=48010&cd=MEMBER',
        'xml': 'feed_Blog_KanagawaSaya.xml',
        'csv': 'feed_Blog_KanagawaSaya.csv',
        'include_phrase': [],
    },
]

for url_and_xml in url_and_xmls:
    url = url_and_xml['url']
    xml_file_name = url_and_xml['xml']
    csv_file_name = url_and_xml['csv']
    include_phrase = url_and_xml.get('include_phrase', [])

    # 既存リンクのみ読み込み（軽量）
    existing_links = load_existing_links(csv_file_name)
    print(f"{xml_file_name}: 既存リンク数 {len(existing_links)}")

    print(f"Fetching URL: {url}")
    response = requests.get(url)
    html_content = response.text

    # 記事のリンク、タイトル、日付を取得
    link_pattern = re.compile(r'<a class="bl--card js-pos a--op hv--thumb" href="([^"]+)">')
    title_pattern = re.compile(r'<p class="bl--card__ttl">([^<]+)</p>')
    date_pattern = re.compile(r'<p class="bl--card__date">([^<]+)</p>')

    links = link_pattern.findall(html_content)
    titles = title_pattern.findall(html_content)
    dates = date_pattern.findall(html_content)

    print(f"Found {len(links)} links, {len(titles)} titles, {len(dates)} dates")

    new_items = []
    for link, title, date in zip(links, titles, dates):
        if not include_phrase or any(phrase in title for phrase in include_phrase):
            full_link = f"https://www.nogizaka46.com{link}"
            if full_link in existing_links:
                continue
            new_items.append({
                'title': title,
                'link': full_link,
                'pubDate': date
            })
            existing_links.add(full_link)

    print(f"{xml_file_name}: 新規アイテム数 {len(new_items)}")

    # 新規アイテムをCSV末尾に追記（高速）
    append_csv(csv_file_name, new_items)
    print(f"{xml_file_name}: CSV追記完了")

    # XMLは最新300件（CSV末尾300行を逆順で取得）
    xml_items = read_last_n_lines(csv_file_name, MAX_XML_ITEMS)

    # XML作成
    root = ET.Element("rss", version="2.0")
    channel = ET.SubElement(root, "channel")
    ET.SubElement(channel, "title").text = "Latest Blogs"
    ET.SubElement(channel, "description").text = "Nogizaka46 Latest Blog Posts"

    for item_data in xml_items:
        item = ET.SubElement(channel, "item")
        ET.SubElement(item, "title").text = item_data['title']
        ET.SubElement(item, "link").text = item_data['link']
        ET.SubElement(item, "pubDate").text = item_data['pubDate']

    # XMLファイルに保存
    xml_string = ET.tostring(root, 'utf-8')
    reparsed = minidom.parseString(xml_string)
    pretty_xml = reparsed.toprettyxml(indent="  ")
    with open(xml_file_name, 'w', encoding='utf-8') as f:
        f.write(pretty_xml)
    print(f"{xml_file_name}: XML保存完了 {len(xml_items)} items")

print("Done!")
