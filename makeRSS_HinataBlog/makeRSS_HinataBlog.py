import requests
import re
import xml.etree.ElementTree as ET
from xml.dom import minidom
import html
import os
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

    # 既存のCSVからアイテムを読み込む
    all_items, existing_links = load_existing_csv(csv_file_name)
    print(f"{xml_file_name}: 既存アイテム数 {len(all_items)}")

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
    print(f"{xml_file_name}: XML保存完了 {len(xml_items)} items (最大{MAX_XML_ITEMS}件)")

print("Done!")
