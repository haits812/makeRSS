import requests
import re
import xml.etree.ElementTree as ET
import html

url_and_xmls = [
    {
        'url': 'https://www.hinatazaka46.com/s/official/diary/member/list?ima=0000&ct=14',
        'xml': 'feed_Blog_Kosaka.xml',
    },
    {
        'url': 'https://www.hinatazaka46.com/s/official/diary/member/list?ima=0000&ct=12',
        'xml': 'feed_Blog_Kanemura.xml',
    },
    {
        'url': 'https://www.hinatazaka46.com/s/official/diary/member/list?ima=0000&ct=000',
        'xml': 'feed_Blog_Poka.xml',
    },
]

for url_and_xml in url_and_xmls:
    url = url_and_xml['url']
    xml_file_name = url_and_xml['xml']

    # HTTPリクエスト
    response = requests.get(url)
    html_content = response.text

    # 正規表現で情報を抜き出す
    link_pattern = re.compile(r'<a class="c-button-blog-detail" href="([^"]+)">個別ページ<\/a>')
    title_pattern = re.compile(r'<div class="c-blog-article__title">\s*([\s\S]*?)\s*<\/div>')
    date_pattern = re.compile(r'<div class="c-blog-article__date">\s*([\s\S]*?)\s*<\/div>')

    new_articles = []
    for link, title, date in zip(link_pattern.findall(html_content), title_pattern.findall(html_content), date_pattern.findall(html_content)):
        link = "https://www.hinatazaka46.com" + link
        new_articles.append({'date': date, 'title': title, 'link': link})

    # XML作成
    root = ET.Element("rss", version="2.0")
    channel = ET.SubElement(root, "channel")
    ET.SubElement(channel, "title").text = "Latest Blogs"
    ET.SubElement(channel, "description").text = "日向坂46 - 最新のブログ投稿"

    for article in new_articles:
        item = ET.SubElement(channel, "item")
        ET.SubElement(item, "title").text = html.unescape(article['title'])  # ここを変えたよ
        ET.SubElement(item, "link").text = html.unescape(article['link'])  # 必要ならここも
        ET.SubElement(item, "pubDate").text = article['date']

    # XMLファイルに保存
    tree = ET.ElementTree(root)
    ET.indent(tree, space="  ")
    tree.write(xml_file_name, encoding='utf-8', xml_declaration=True)
