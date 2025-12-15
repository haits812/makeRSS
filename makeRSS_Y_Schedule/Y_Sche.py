import os
import re
from bs4 import BeautifulSoup
from pyppeteer import launch
from xml.etree.ElementTree import Element, SubElement, tostring
from datetime import datetime, timedelta
import xml.dom.minidom
import xml.etree.ElementTree as ET
import asyncio
from html import unescape as html_unescape
from urllib.parse import urlparse, parse_qs
import traceback
import csv
from collections import deque

MAX_XML_ITEMS = 300  # XMLに保持する最大アイテム数
FIELDNAMES = ['pubDate', 'title', 'link', 'category', 'start_time']

def load_existing_keys(csv_file):
    """CSVからキーのみ読み込む（重複チェック用・軽量）"""
    existing_keys = set()
    if os.path.exists(csv_file):
        with open(csv_file, 'r', encoding='utf-8-sig', newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                key = (row['pubDate'], extract_url_part(row['link']))
                existing_keys.add(key)
    return existing_keys

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
    
    # 日付降順でソートして返す（スケジュールは日付順が重要）
    items = list(last_n)
    items.sort(key=lambda x: x.get('pubDate', ''), reverse=True)
    return items

def extract_url_part(url):
    """URLが可変する部分を除外してURLを確認する"""
    parsed_url = urlparse(url)
    path = parsed_url.path.split("/")[-1]
    query = parse_qs(parsed_url.query)
    unique_part = f"{path}_{query.get('pri1', [''])[0]}_{query.get('wd00', [''])[0]}_{query.get('wd01', [''])[0]}_{query.get('wd02', [''])[0]}"
    return unique_part

async def main():
    existing_file = 'Y_Sche.xml'
    csv_file = 'Y_Sche.csv'
    
    # 既存キーのみ読み込み（軽量）
    existing_keys = load_existing_keys(csv_file)
    print(f"既存キー数: {len(existing_keys)}")

    # 新規情報を保存するリスト
    new_schedules = []

    # 先月の1日から3ヶ月先までのyyyymmを生成
    start_date = (datetime.today().replace(day=1) - timedelta(days=1)).replace(day=1)
    end_date = start_date + timedelta(days=90)
    current_date = start_date

    browser = None
    try:
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
                        title = html_unescape(title_tag.get_text()) if title_tag else ""
                        
                        schedule_url = html_unescape(link['href'])
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

    # 新規がなければスキップ
    if not new_schedules:
        print("新規スケジュールなし、更新スキップ")
        return

    # 新規アイテムをCSV末尾に追記（高速）
    append_csv(csv_file, new_schedules)
    print(f"CSV追記完了: {len(new_schedules)} items added")

    # XMLは最新300件（CSV末尾から取得し日付降順ソート）
    xml_items = read_last_n_lines(csv_file, MAX_XML_ITEMS)

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
