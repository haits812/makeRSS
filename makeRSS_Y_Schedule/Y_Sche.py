import os
import re
from bs4 import BeautifulSoup
from pyppeteer import launch
from xml.etree.ElementTree import Element, SubElement, tostring, ElementTree
from datetime import datetime, timedelta
import xml.dom.minidom
import xml.etree.ElementTree as ET
import asyncio
import requests
from html import unescape as html_unescape
from urllib.parse import urlparse, parse_qs
import traceback
import csv

MAX_XML_ITEMS = 300  # XMLに保持する最大アイテム数

def load_existing_csv(csv_file):
    """CSVファイルから既存のスケジュールを読み込む"""
    existing_items = []
    existing_keys = set()
    if os.path.exists(csv_file):
        with open(csv_file, 'r', encoding='utf-8-sig', newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                existing_items.append(row)
                # 重複判定用のキー (日付 + URL一部)
                key = (row['pubDate'], extract_url_part(row['link']))
                existing_keys.add(key)
    return existing_items, existing_keys

def migrate_xml_to_csv(xml_file, csv_file):
    """既存のXMLからCSVにデータを移行する（初回のみ）"""
    if os.path.exists(csv_file) or not os.path.exists(xml_file):
        return [], set()
    
    print(f"Migrating data from {xml_file} to {csv_file}...")
    items = []
    keys = set()
    
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()
        for item in root.findall(".//item"):
            title_elem = item.find("title")
            link_elem = item.find("link")
            date_elem = item.find("pubDate")
            category_elem = item.find("category")
            start_time_elem = item.find("start_time")
            
            if title_elem is not None and link_elem is not None:
                item_data = {
                    'title': html_unescape(title_elem.text) if title_elem.text else '',
                    'link': html_unescape(link_elem.text) if link_elem.text else '',
                    'pubDate': date_elem.text if date_elem is not None else '',
                    'category': category_elem.text if category_elem is not None else '',
                    'start_time': start_time_elem.text if start_time_elem is not None else ''
                }
                items.append(item_data)
                key = (item_data['pubDate'], extract_url_part(item_data['link']))
                keys.add(key)
        print(f"Migrated {len(items)} items from XML")
    except Exception as e:
        print(f"Error migrating XML: {e}")
    
    return items, keys

def save_csv(csv_file, items):
    """全アイテムをCSVに保存"""
    if not items:
        return
    fieldnames = ['pubDate', 'title', 'link', 'category', 'start_time']
    with open(csv_file, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(items)

# URLが可変する部分を除外してURLを確認する
def extract_url_part(url):
    parsed_url = urlparse(url)
    path = parsed_url.path.split("/")[-1]  # /103002 や /102232 を取得
    query = parse_qs(parsed_url.query)
    unique_part = f"{path}_{query.get('pri1', [''])[0]}_{query.get('wd00', [''])[0]}_{query.get('wd01', [''])[0]}_{query.get('wd02', [''])[0]}"
    return unique_part

async def main():
    existing_file = 'Y_Sche.xml'
    csv_file = 'Y_Sche.csv'
    
    # CSVが無ければ既存XMLから移行
    if not os.path.exists(csv_file) and os.path.exists(existing_file):
        all_items, existing_keys = migrate_xml_to_csv(existing_file, csv_file)
        # CSVに保存
        if all_items:
            save_csv(csv_file, all_items)
    else:
        # 既存のCSVからアイテムを読み込む
        all_items, existing_keys = load_existing_csv(csv_file)
    
    print(f"既存アイテム数: {len(all_items)}")

    # 新規情報を保存するリスト
    new_schedules = []

    # 先月の1日から3ヶ月先までのyyyymmを生成
    start_date = (datetime.today().replace(day=1) - timedelta(days=1)).replace(day=1)
    end_date = start_date + timedelta(days=90)
    current_date = start_date

    browser = None
    try:
        # Pyppeteerでブラウザを開く
        browser = await launch(
            executablePath='/usr/bin/chromium-browser',
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-accelerated-2d-canvas',
                '--disable-gpu'
            ],
            defaultViewport=None,
            userDataDir='./user_data',
            logLevel='INFO'
        )
        print(f"Chromium launched successfully")

        while current_date <= end_date:
            yyyymm = current_date.strftime('%Y%m')
            url = f"https://www.nogizaka46.com/s/n46/media/list?dy={yyyymm}&members={{%22member%22:[%2255387%22]}}"
            print(f"Fetching URL: {url}")

            page = await browser.newPage()

            try:
                response = await page.goto(url, timeout=60000)
                print(f"Navigated to URL: {url}, Status: {response.status}")

                await page.waitForFunction(
                    '() => document.querySelectorAll(".sc--day").length > 0', 
                    timeout=60000
                )
                await page.waitForFunction('() => document.readyState === "complete"', timeout=60000)

                html = await page.content()
                soup = BeautifulSoup(html, 'html.parser')

                schedule_list = soup.find('div', class_='sc--lists js-apischedule-list')
                day_schedules = schedule_list.find_all('div', class_='sc--day')

                for day_schedule in day_schedules:
                    date_tag = day_schedule.find('p', class_='sc--day__d f--head')
                    
                    if date_tag is None:
                        continue
                    
                    date = f"{yyyymm[:4]}/{yyyymm[4:]}/{date_tag.text}"
            
                    schedule_links = day_schedule.find_all('a', class_='m--scone__a hv--op')

                    for link in schedule_links:
                        title_tag = link.find('p', class_='m--scone__ttl')
                        if title_tag:
                            title = title_tag.get_text()
                        else:
                            title = ""
                        title = html_unescape(str(title))
                        
                        schedule_url = link['href']
                        schedule_url = html_unescape(str(schedule_url))

                        category = link.find('p', class_='m--scone__cat__name').text
                        start_time_tag = link.find('p', class_='m--scone__start')
                        start_time = start_time_tag.text if start_time_tag else ''

                        extracted_url = extract_url_part(schedule_url)
                        try:
                            datetime.strptime(date, "%Y/%m/%d")
                            if (date, extracted_url) not in existing_keys:
                                new_item = {
                                    'pubDate': date,
                                    'title': title,
                                    'link': schedule_url,
                                    'category': category,
                                    'start_time': start_time
                                }
                                new_schedules.append(new_item)
                                existing_keys.add((date, extracted_url))
                                print(f"新規情報を追加: {date}, {title}")
                        except ValueError:
                            print(f"日付フォーマットエラー: {date}")

            except asyncio.TimeoutError:
                print(f"Navigation Timeout Exceeded for URL: {url}")
                traceback.print_exc()
            except Exception as e:
                print(f"Error occurred during browser operation: {e}")
                traceback.print_exc()
            finally:
                await page.close()

            # 次の月へ
            current_date = (current_date + timedelta(days=31)).replace(day=1)
            if current_date.day != 1:
                current_date = (current_date + timedelta(days=1)).replace(day=1)

    except Exception as e:
        print(f"Error occurred during browser operation: {e}")

    finally:
        if browser:
            await browser.close()
            print("Chromium closed.")

    print(f"新規スケジュール数: {len(new_schedules)}")

    # 新しいアイテムを先頭に追加（CSVは全件保持）
    all_items = new_schedules + all_items

    # 日付の降順にソート
    def parse_date(item):
        try:
            return datetime.strptime(item['pubDate'], "%Y/%m/%d")
        except:
            return datetime.min
    
    all_items.sort(key=parse_date, reverse=True)

    # CSVに全件保存
    save_csv(csv_file, all_items)
    print(f"CSV保存完了: {len(all_items)} items")

    # XMLは最新500件のみ
    xml_items = all_items[:MAX_XML_ITEMS]

    # RSSフィードを生成
    rss = Element("rss", version="2.0")
    channel = SubElement(rss, "channel")
    SubElement(channel, "title").text = "弓木奈於のスケジュール"
    SubElement(channel, "description").text = ""
    SubElement(channel, "link").text = ""
    
    for item_data in xml_items:
        item = SubElement(channel, "item")
        SubElement(item, "title").text = item_data['title']
        SubElement(item, "link").text = item_data['link']
        SubElement(item, "pubDate").text = item_data['pubDate']
        SubElement(item, "category").text = item_data['category']
        SubElement(item, "start_time").text = item_data['start_time']

    xml_str = xml.dom.minidom.parseString(tostring(rss)).toprettyxml(indent="   ")

    with open(existing_file, 'w', encoding='utf-8') as f:
        f.write(xml_str)
    
    print(f"XML保存完了: {len(xml_items)} items (最大{MAX_XML_ITEMS}件)")

if __name__ == "__main__":
    asyncio.run(main())
