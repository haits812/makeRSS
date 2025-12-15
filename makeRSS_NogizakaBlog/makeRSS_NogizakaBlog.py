import os
import re
import requests
import xml.etree.ElementTree as ET
from xml.dom import minidom
import csv
import codecs

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

def save_csv(csv_file, items):
    """全アイテムをCSVに保存（BOM付きUTF-8でExcel対応）"""
    if not items:
        return
    fieldnames = ['title', 'link', 'pubDate']
    with codecs.open(csv_file, 'w', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator='\n')
        writer.writeheader()
        writer.writerows(items)

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

    # 既存のCSVからアイテムを読み込む
    all_items, existing_links = load_existing_csv(csv_file_name)
    print(f"{xml_file_name}: 既存アイテム数 {len(all_items)}")

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

    # 新しいアイテムを先頭に追加（CSVは全件保持）
    all_items = new_items + all_items

    # CSVに全件保存
    save_csv(csv_file_name, all_items)
    print(f"{xml_file_name}: CSV保存完了 {len(all_items)} items")

    # XMLは最新300件のみ
    xml_items = all_items[:MAX_XML_ITEMS]

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
    print(f"{xml_file_name}: XML保存完了 {len(xml_items)} items (最大{MAX_XML_ITEMS}件)")

print("Done!")
