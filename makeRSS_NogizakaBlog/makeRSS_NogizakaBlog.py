import os
import re
import requests
import xml.dom.minidom
from xml.etree import ElementTree as ET
from xml.dom import minidom
from datetime import datetime
from html import unescape
from xml.etree.ElementTree import Element, SubElement, ElementTree, tostring

def prettify(elem):
    rough_string = ET.tostring(elem, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ")

url_and_xmls = [
        {
            'url': 'https://www.nogizaka46.com/s/n46/diary/MEMBER/list?page=0&ct=55387&cd=MEMBER',
            'xml': 'feed_Blog_YumikiNao.xml',
            'include_phrase': [],
        },
        #{
        #    'url': 'https://www.nogizaka46.com/s/n46/diary/MEMBER/list?page=0&ct=40001&cd=MEMBER',
        #    'xml': 'feed_Blog_YumikiNao.xml',
        #    'include_phrase': ['弓木'],
        #},
        {
            'url': 'https://www.nogizaka46.com/s/n46/diary/MEMBER/list?page=0&ct=48010&cd=MEMBER',
            'xml': 'feed_Blog_KanagawaSaya.xml',
            'include_phrase': [],
        },
        #{
        #    'url': 'https://www.nogizaka46.com/s/n46/diary/MEMBER/list?page=0&ct=40005&cd=MEMBER',
        #    'xml': 'feed_Blog_KanagawaSaya.xml',
        #    'include_phrase': ['金川'],
        #},
        #{
        #    'url': 'https://www.nogizaka46.com/s/n46/diary/MEMBER/list?page=0&ct=55396&cd=MEMBER',
        #    'xml': 'feed_Blog_Ioki.xml',
        #    'include_phrase': [],
        #},
        #{
        #    'url': 'https://www.nogizaka46.com/s/n46/diary/MEMBER/list?page=0&ct=40007&cd=MEMBER',
        #    'xml': 'feed_Blog_Ioki.xml',
        #    'include_phrase': ['五百城'],
        #},
        #{
        #    'url': 'https://www.nogizaka46.com/s/n46/diary/MEMBER/list?page=0&ct=55397&cd=MEMBER',
        #    'xml': 'feed_Blog_Ikeda.xml',
        #    'include_phrase': [],
        #},
        #{
        #    'url': 'https://www.nogizaka46.com/s/n46/diary/MEMBER/list?page=0&ct=40007&cd=MEMBER',
        #    'xml': 'feed_Blog_Ikeda.xml',
        #    'include_phrase': ['池田'],
        #},
        #{
        #    'url': 'https://www.nogizaka46.com/s/n46/diary/MEMBER/list?page=0&ct=55390&cd=MEMBER',
        #    'xml': 'feed_Blog_Ichinose.xml',
        #    'include_phrase': [],
        #},
        #{
        #    'url': 'https://www.nogizaka46.com/s/n46/diary/MEMBER/list?page=0&ct=40007&cd=MEMBER',
        #    'xml': 'feed_Blog_Ichinose.xml',
        #    'include_phrase': ['一ノ瀬'],
        #},
        #{
        #    'url': 'https://www.nogizaka46.com/s/n46/diary/MEMBER/list?page=0&ct=36749&cd=MEMBER',
        #    'xml': 'feed_Blog_Ito.xml',
        #    'include_phrase': [],
        #},
        #{
        #    'url': 'https://www.nogizaka46.com/s/n46/diary/MEMBER/list?page=0&ct=40004&cd=MEMBER',
        #    'xml': 'feed_Blog_Ito.xml',
        #    'include_phrase': ['伊藤'],
        #},
        #{
        #    'url': 'https://www.nogizaka46.com/s/n46/diary/MEMBER/list?page=0&ct=55389&cd=MEMBER',
        #    'xml': 'feed_Blog_Inoue.xml',
        #    'include_phrase': [],
        #},
        #{
        #    'url': 'https://www.nogizaka46.com/s/n46/diary/MEMBER/list?page=0&ct=40007&cd=MEMBER',
        #    'xml': 'feed_Blog_Inoue.xml',
        #    'include_phrase': ['井上'],
        #},
        #{
        #    'url': 'https://www.nogizaka46.com/s/n46/diary/MEMBER/list?page=0&ct=36750&cd=MEMBER',
        #    'xml': 'feed_Blog_Iwamoto.xml',
        #    'include_phrase': [],
        #},
        #{
        #    'url': 'https://www.nogizaka46.com/s/n46/diary/MEMBER/list?page=0&ct=40004&cd=MEMBER',
        #    'xml': 'feed_Blog_Iwamoto.xml',
        #    'include_phrase': ['岩本'],
        #},
        #{
        #    'url': 'https://www.nogizaka46.com/s/n46/diary/MEMBER/list?page=0&ct=36751&cd=MEMBER',
        #    'xml': 'feed_Blog_Umezawa.xml',
        #    'include_phrase': [],
        #},
        #{
        #    'url': 'https://www.nogizaka46.com/s/n46/diary/MEMBER/list?page=0&ct=40004&cd=MEMBER',
        #    'xml': 'feed_Blog_Umezawa.xml',
        #    'include_phrase': ['梅澤'],
        #},
        #{
        #    'url': 'https://www.nogizaka46.com/s/n46/diary/MEMBER/list?page=0&ct=48006&cd=MEMBER',
        #    'xml': 'feed_Blog_Endo.xml',
        #    'include_phrase': [],
        #},
        #{
        #    'url': 'https://www.nogizaka46.com/s/n46/diary/MEMBER/list?page=0&ct=40005&cd=MEMBER',
        #    'xml': 'feed_Blog_Endo.xml',
        #    'include_phrase': ['遠藤'],
        #},
        #{
        #    'url': 'https://www.nogizaka46.com/s/n46/diary/MEMBER/list?page=0&ct=55401&cd=MEMBER',
        #    'xml': 'feed_Blog_Okamoto.xml',
        #    'include_phrase': [],
        #},
        #{
        #    'url': 'https://www.nogizaka46.com/s/n46/diary/MEMBER/list?page=0&ct=40007&cd=MEMBER',
        #    'xml': 'feed_Blog_Okamoto.xml',
        #    'include_phrase': ['岡本'],
        #},
        #{
        #    'url': 'https://www.nogizaka46.com/s/n46/diary/MEMBER/list?page=0&ct=55392&cd=MEMBER',
        #    'xml': 'feed_Blog_Ogawa.xml',
        #    'include_phrase': [],
        #},
        #{
        #    'url': 'https://www.nogizaka46.com/s/n46/diary/MEMBER/list?page=0&ct=40007&cd=MEMBER',
        #    'xml': 'feed_Blog_Ogawa.xml',
        #    'include_phrase': ['小川'],
        #},
        #{
        #    'url': 'https://www.nogizaka46.com/s/n46/diary/MEMBER/list?page=0&ct=55394&cd=MEMBER',
        #    'xml': 'feed_Blog_Okuda.xml',
        #    'include_phrase': [],
        #},
        #{
        #    'url': 'https://www.nogizaka46.com/s/n46/diary/MEMBER/list?page=0&ct=40007&cd=MEMBER',
        #    'xml': 'feed_Blog_Okuda.xml',
        #    'include_phrase': ['奥田'],
        #},
        #{
        #    'url': 'https://www.nogizaka46.com/s/n46/diary/MEMBER/list?page=0&ct=48008&cd=MEMBER',
        #    'xml': 'feed_Blog_Kaki.xml',
        #    'include_phrase': [],
        #},
        #{
        #    'url': 'https://www.nogizaka46.com/s/n46/diary/MEMBER/list?page=0&ct=40005&cd=MEMBER',
        #    'xml': 'feed_Blog_Kaki.xml',
        #    'include_phrase': ['賀喜'],
        #},
        #{
        #    'url': 'https://www.nogizaka46.com/s/n46/diary/MEMBER/list?page=0&ct=48009&cd=MEMBER',
        #    'xml': 'feed_Blog_Kakehashi.xml',
        #    'include_phrase': [],
        #},
        #{
        #    'url': 'https://www.nogizaka46.com/s/n46/diary/MEMBER/list?page=0&ct=40005&cd=MEMBER',
        #    'xml': 'feed_Blog_Kakehashi.xml',
        #    'include_phrase': ['掛橋'],
        #},
        #{
        #    'url': 'https://www.nogizaka46.com/s/n46/diary/MEMBER/list?page=0&ct=55400&cd=MEMBER',
        #    'xml': 'feed_Blog_Kawasaki.xml',
        #    'include_phrase': [],
        #},
        #{
        #    'url': 'https://www.nogizaka46.com/s/n46/diary/MEMBER/list?page=0&ct=40007&cd=MEMBER',
        #    'xml': 'feed_Blog_Kawasaki.xml',
        #    'include_phrase': ['川﨑'],
        #},
        #{
        #    'url': 'https://www.nogizaka46.com/s/n46/diary/MEMBER/list?page=0&ct=36753&cd=MEMBER',
        #    'xml': 'feed_Blog_Kubo.xml',
        #    'include_phrase': [],
        #},
        #{
        #    'url': 'https://www.nogizaka46.com/s/n46/diary/MEMBER/list?page=0&ct=40004&cd=MEMBER',
        #    'xml': 'feed_Blog_Kubo.xml',
        #    'include_phrase': ['久保'],
        #},
        #{
        #    'url': 'https://www.nogizaka46.com/s/n46/diary/MEMBER/list?page=0&ct=55383&cd=MEMBER',
        #    'xml': 'feed_Blog_Kuromi.xml',
        #    'include_phrase': [],
        #},
        #{
        #    'url': 'https://www.nogizaka46.com/s/n46/diary/MEMBER/list?page=0&ct=40001&cd=MEMBER',
        #    'xml': 'feed_Blog_Kuromi.xml',
        #    'include_phrase': ['黒見'],
        #},
        #{
        #    'url': 'https://www.nogizaka46.com/s/n46/diary/MEMBER/list?page=0&ct=36754&cd=MEMBER',
        #    'xml': 'feed_Blog_Sakaguchi.xml',
        #    'include_phrase': [],
        #},
        #{
        #    'url': 'https://www.nogizaka46.com/s/n46/diary/MEMBER/list?page=0&ct=40004&cd=MEMBER',
        #    'xml': 'feed_Blog_Sakaguchi.xml',
        #    'include_phrase': ['阪口'],
        #},
        #{
        #    'url': 'https://www.nogizaka46.com/s/n46/diary/MEMBER/list?page=0&ct=36755&cd=MEMBER',
        #    'xml': 'feed_Blog_SatoKaede.xml',
        #    'include_phrase': [],
        #},
        #{
        #    'url': 'https://www.nogizaka46.com/s/n46/diary/MEMBER/list?page=0&ct=40004&cd=MEMBER',
        #    'xml': 'feed_Blog_SatoKaede.xml',
        #    'include_phrase': ['佐藤'],
        #},
        #{
        #    'url': 'https://www.nogizaka46.com/s/n46/diary/MEMBER/list?page=0&ct=55384&cd=MEMBER',
        #    'xml': 'feed_Blog_SatoRika.xml',
        #    'include_phrase': [],
        #},
        #{
        #    'url': 'https://www.nogizaka46.com/s/n46/diary/MEMBER/list?page=0&ct=40001&cd=MEMBER',
        #    'xml': 'feed_Blog_SatoRika.xml',
        #    'include_phrase': ['佐藤'],
        #},
        #{
        #    'url': 'https://www.nogizaka46.com/s/n46/diary/MEMBER/list?page=0&ct=48013&cd=MEMBER',
        #    'xml': 'feed_Blog_Shibata.xml',
        #    'include_phrase': [],
        #},
        #{
        #    'url': 'https://www.nogizaka46.com/s/n46/diary/MEMBER/list?page=0&ct=40005&cd=MEMBER',
        #    'xml': 'feed_Blog_Shibata.xml',
        #    'include_phrase': ['柴田'],
        #},
        #{
        #    'url': 'https://www.nogizaka46.com/s/n46/diary/MEMBER/list?page=0&ct=55391&cd=MEMBER',
        #    'xml': 'feed_Blog_Sugawara.xml',
        #    'include_phrase': [],
        #},
        #{
        #    'url': 'https://www.nogizaka46.com/s/n46/diary/MEMBER/list?page=0&ct=40007&cd=MEMBER',
        #    'xml': 'feed_Blog_Sugawara.xml',
        #    'include_phrase': ['菅原'],
        #},
        #{
        #    'url': 'https://www.nogizaka46.com/s/n46/diary/MEMBER/list?page=0&ct=48014&cd=MEMBER',
        #    'xml': 'feed_Blog_Seimiya.xml',
        #    'include_phrase': [],
        #},
        #{
        #    'url': 'https://www.nogizaka46.com/s/n46/diary/MEMBER/list?page=0&ct=40005&cd=MEMBER',
        #    'xml': 'feed_Blog_Seimiya.xml',
        #    'include_phrase': ['清宮'],
        #},
        #{
        #    'url': 'https://www.nogizaka46.com/s/n46/diary/MEMBER/list?page=0&ct=48015&cd=MEMBER',
        #    'xml': 'feed_Blog_Tamura.xml',
        #    'include_phrase': [],
        #},
        #{
        #    'url': 'https://www.nogizaka46.com/s/n46/diary/MEMBER/list?page=0&ct=40005&cd=MEMBER',
        #    'xml': 'feed_Blog_Tamura.xml',
        #    'include_phrase': ['田村'],
        #},
        #{
        #    'url': 'https://www.nogizaka46.com/s/n46/diary/MEMBER/list?page=0&ct=48017&cd=MEMBER',
        #    'xml': 'feed_Blog_Tsutsui.xml',
        #    'include_phrase': [],
        #},
        #{
        #    'url': 'https://www.nogizaka46.com/s/n46/diary/MEMBER/list?page=0&ct=40005&cd=MEMBER',
        #    'xml': 'feed_Blog_Tsutsui.xml',
        #    'include_phrase': ['筒井'],
        #},
        #{
        #    'url': 'https://www.nogizaka46.com/s/n46/diary/MEMBER/list?page=0&ct=55393&cd=MEMBER',
        #    'xml': 'feed_Blog_Tomisato.xml',
        #    'include_phrase': [],
        #},
        #{
        #    'url': 'https://www.nogizaka46.com/s/n46/diary/MEMBER/list?page=0&ct=40007&cd=MEMBER',
        #    'xml': 'feed_Blog_Tomisato.xml',
        #    'include_phrase': ['冨里'],
        #},
        #{
        #    'url': 'https://www.nogizaka46.com/s/n46/diary/MEMBER/list?page=0&ct=55395&cd=MEMBER',
        #    'xml': 'feed_Blog_Nakanishi.xml',
        #    'include_phrase': [],
        #},
        #{
        #    'url': 'https://www.nogizaka46.com/s/n46/diary/MEMBER/list?page=0&ct=40007&cd=MEMBER',
        #    'xml': 'feed_Blog_Nakanishi.xml',
        #    'include_phrase': ['中西'],
        #},
        #{
        #    'url': 'https://www.nogizaka46.com/s/n46/diary/MEMBER/list?page=0&ct=36756&cd=MEMBER',
        #    'xml': 'feed_Blog_Nakamura.xml',
        #    'include_phrase': [],
        #},
        #{
        #    'url': 'https://www.nogizaka46.com/s/n46/diary/MEMBER/list?page=0&ct=40004&cd=MEMBER',
        #    'xml': 'feed_Blog_Nakamura.xml',
        #    'include_phrase': ['中村'],
        #},
        #{
        #    'url': 'https://www.nogizaka46.com/s/n46/diary/MEMBER/list?page=0&ct=55385&cd=MEMBER',
        #    'xml': 'feed_Blog_Hayashi.xml',
        #    'include_phrase': [],
        #},
        #{
        #    'url': 'https://www.nogizaka46.com/s/n46/diary/MEMBER/list?page=0&ct=40001&cd=MEMBER',
        #    'xml': 'feed_Blog_Hayashi.xml',
        #    'include_phrase': ['林'],
        #},
        #{
        #    'url': 'https://www.nogizaka46.com/s/n46/diary/MEMBER/list?page=0&ct=55386&cd=MEMBER',
        #    'xml': 'feed_Blog_Matsuo.xml',
        #    'include_phrase': [],
        #},
        #{
        #    'url': 'https://www.nogizaka46.com/s/n46/diary/MEMBER/list?page=0&ct=40001&cd=MEMBER',
        #    'xml': 'feed_Blog_Matsuo.xml',
        #    'include_phrase': ['松尾'],
        #},
        #{
        #    'url': 'https://www.nogizaka46.com/s/n46/diary/MEMBER/list?page=0&ct=36757&cd=MEMBER',
        #    'xml': 'feed_Blog_Mukai.xml',
        #    'include_phrase': [],
        #},
        #{
        #    'url': 'https://www.nogizaka46.com/s/n46/diary/MEMBER/list?page=0&ct=40004&cd=MEMBER',
        #    'xml': 'feed_Blog_Mukai.xml',
        #    'include_phrase': ['向井'],
        #},
        #{
        #    'url': 'https://www.nogizaka46.com/s/n46/diary/MEMBER/list?page=0&ct=48019&cd=MEMBER',
        #    'xml': 'feed_Blog_Yakubo.xml',
        #    'include_phrase': [],
        #},
        #{
        #    'url': 'https://www.nogizaka46.com/s/n46/diary/MEMBER/list?page=0&ct=40005&cd=MEMBER',
        #    'xml': 'feed_Blog_Yakubo.xml',
        #    'include_phrase': ['矢久保'],
        #},
        #{
        #    'url': 'https://www.nogizaka46.com/s/n46/diary/MEMBER/list?page=0&ct=36758&cd=MEMBER',
        #    'xml': 'feed_Blog_Yamashita.xml',
        #    'include_phrase': [],
        #},
        #{
        #    'url': 'https://www.nogizaka46.com/s/n46/diary/MEMBER/list?page=0&ct=40004&cd=MEMBER',
        #    'xml': 'feed_Blog_Yamashita.xml',
        #    'include_phrase': ['山下'],
        #},
        #{
        #    'url': 'https://www.nogizaka46.com/s/n46/diary/MEMBER/list?page=0&ct=36759&cd=MEMBER',
        #    'xml': 'feed_Blog_Yoshida.xml',
        #    'include_phrase': [],
        #},
        #{
        #    'url': 'https://www.nogizaka46.com/s/n46/diary/MEMBER/list?page=0&ct=40004&cd=MEMBER',
        #    'xml': 'feed_Blog_Yoshida.xml',
        #    'include_phrase': ['吉田'],
        #},
        #{
        #    'url': 'https://www.nogizaka46.com/s/n46/diary/MEMBER/list?page=0&ct=36760&cd=MEMBER',
        #    'xml': 'feed_Blog_Yoda.xml',
        #    'include_phrase': [],
        #},
        #{
        #    'url': 'https://www.nogizaka46.com/s/n46/diary/MEMBER/list?page=0&ct=40004&cd=MEMBER',
        #    'xml': 'feed_Blog_Yoda.xml',
        #    'include_phrase': ['与田'],
        #},
        #{
        #    'url': 'https://www.nogizaka46.com/s/n46/diary/MEMBER/list?page=0&ct=40003&cd=MEMBER',
        #    'xml': 'feed_Blog_Unei.xml',
        #    'include_phrase': [],
        #},
]





# 各XMLファイル名に対応するchannel要素を保存する辞書
xml_data = {}

for url_and_xml in url_and_xmls:
    
    page_number = 0  # ページ番号の初期化
    
    url = url_and_xml['url']
    xml_file_name = url_and_xml['xml']
    include_phrase = url_and_xml.get('include_phrase', [])

    # xml_dataにchannel要素がなければ作成
    if xml_file_name not in xml_data:
        root = Element("rss", version="2.0")
        channel = SubElement(root, "channel")
        SubElement(channel, "title").text = "Latest Blogs"
        SubElement(channel, "description").text = "Nogizaka46 Latest Blog Posts"
        xml_data[xml_file_name] = {'root': root, 'channel': channel}
    else:
        channel = xml_data[xml_file_name]['channel']

    while url:
        print(f"Fetching URL: {url}")  # Debug
        response = requests.get(url)
        html_content = response.text

        # 記事のリンク、タイトル、日付を取得
        link_pattern = re.compile(r'<a class="bl--card js-pos a--op hv--thumb" href="([^"]+)">')
        title_pattern = re.compile(r'<p class="bl--card__ttl">([^<]+)</p>')
        date_pattern = re.compile(r'<p class="bl--card__date">([^<]+)</p>')

        links = link_pattern.findall(html_content)
        titles = title_pattern.findall(html_content)
        dates = date_pattern.findall(html_content)

        print(f"Found links: {links}")  # Debug
        print(f"Found titles: {titles}")  # Debug
        print(f"Found dates: {dates}")  # Debug

        for link, title, date in zip(links, titles, dates):
            if not include_phrase or any(phrase in title for phrase in include_phrase):
                item = SubElement(channel, "item")
                SubElement(item, "title").text = title
                SubElement(item, "link").text = f"https://www.nogizaka46.com{link}"
                SubElement(item, "pubDate").text = date

        for title in titles:
            if "該当するデータがございません" in title:
                url = None  # 次のページがないので、ループを終了
                break  # forループを抜ける
            
        if url:
            #page_number += 1
            #next_url = re.sub(r'page=\d+', f'page={page_number}', url)  # URL内のpage数を更新
            #url = next_url
            url = None
        else:
            break  # ループを抜ける
    else:
        url = None  # ページがなければNoneに設定

    print(f"Next URL: {url}")  # Debug

# 最後に各XMLファイルに書き出し
for xml_file_name, data in xml_data.items():
    root = data['root']
    xml_string = ET.tostring(root, 'utf-8')
    reparsed = minidom.parseString(xml_string)
    pretty_xml = reparsed.toprettyxml(indent="  ")
    with open(xml_file_name, 'wb') as f:
        f.write(pretty_xml.encode('utf-8'))

print("Done!")
