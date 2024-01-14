import json
import os
import sys
import time
import traceback
sys.path.append(os.getcwd())  # NOQA

from src.utils.selenium import ChromeDriver
from src.chatgpt.parse_specs_helper import convert_json

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup as bs

from src.crawler.base import BaseCrawler
from concurrent.futures import ThreadPoolExecutor, as_completed


class Tgdd(BaseCrawler):

    # Load the category mapping config
    def __init__(self, headless: bool = False):
        self.tgdd_config = self.load_config('tgdd.json')
        self.headless = headless

        # Connect to database
        self.conn = self.connect_db('ttchat.db')

    # ----------------- Get all product links -----------------

    def _click_show_more(self, driver):
        # ----------------- Click Show More -----------------
        while True:
            time.sleep(0.5)
            try:
                show_more_btn = WebDriverWait(driver, 6).until(
                    EC.element_to_be_clickable(
                        (By.CLASS_NAME, 'view-more'))
                )
                if show_more_btn.get_attribute('style').strip() == '':
                    show_more_btn.click()
                    self.log(f'Clicking the Show More button: {show_more_btn.text}')
            except Exception as e:
                self.log('No more product to show')
                return

    def _parse_product_links(self, page_source: str) -> list:
        urls = []

        try:
            soup = bs(page_source, 'html.parser')
            ul = soup.find('ul', {'class': 'listproduct'})
            lis = ul.find_all('li')
            for li in lis:
                a = li.find('a')
                merged_url = f'https://www.thegioididong.com{a["href"]}'
                self.log(f'Found: {merged_url}')
                urls.append(merged_url)
        except Exception as e:
            self.log(traceback.format_exc())
        finally:
            self.log(f'Found {len(urls)} product links')
            return urls

    def _get_product_link(self, driver, manufacturer: str) -> list:
        """
            Get all product links of a manufacturer in The Gioi Di Dong
        Args:
            manufacturer (str): hp, dell, asus, lenovo, acer, msi

        Returns:
            list: The list of all product links of that manufacturer in The Gioi Di Dong
        """

        # Go the the manufacturer page
        self.log(f'Going to the manufacturer page: {self.tgdd_config[manufacturer]}')
        driver.get(self.tgdd_config[manufacturer])

        # Click the Show More button
        self._click_show_more(driver)

        # Parsing the page source
        self.log('Parsing the page source')
        urls = self._parse_product_links(driver.page_source)

        return urls

    def get_all_product_links(self):
        """
            Get all product links of all manufacturers in The Gioi Di Dong
        """
        # Get the driver
        self.log('Getting the driver')
        driver = ChromeDriver(headless=self.headless).driver

        urls = {}

        for manufacturer in self.tgdd_config.keys():
            urls[manufacturer] = self._get_product_link(driver=driver, manufacturer=manufacturer)

        # Close the driver
        self.log('Closing the driver')
        driver.close()

        # Save the result to file
        self.log('Saving the result to file')
        with open(os.path.join(os.getcwd(), 'data', 'tgdd_product_links.json'), 'w') as f:
            json.dump(urls, f, indent=4, ensure_ascii=True)

    # ----------------- Fetch all raw_htmls -----------------

    def _crawl_raw_htmls(self):
        """
            Crawl the raw HTML of all product pages
        Args:
            url (str): The product page URL

        Returns:
            str: The raw HTML of the product page
        """

        def fetch_html(url, manufacturer: str, id: int) -> bool:
            try:
                driver = ChromeDriver(headless=self.headless).driver
                driver.get(url)
                html = driver.page_source

                with open(f'data/raw_htmls/tgdd/{manufacturer}_{id}.html', 'w', encoding='utf-8') as f:
                    f.write(html)

                    craw_info = {
                        'Manufacturer': manufacturer,
                        'Url': url,
                        'Raw_html_path': f'data/raw_htmls/tgdd/{manufacturer}_{id}.html'
                    }

                self.log(f'========> Successfully fetch HTML of {url}')

                return craw_info
            except Exception as e:
                self.log(f'========> Fail to fetch HTML of {url}: {str(e)}')
                return False

        # Read the product links
        self.log(f'Start fetching ...')

        with open('data/tgdd_product_links.json', 'r') as f:
            tgdd_product_links: dict = json.load(f)

        def build_insert_query(manufacturer: str, url: str, raw_html_path: str) -> str:
            return f"""
                INSERT INTO html (Manufacturer, Url, Raw_html_path)
                VALUES ('{manufacturer}', '{url}', '{raw_html_path}')
            """

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = []

            for manufacturer in tgdd_product_links.keys():
                for id, url in enumerate(tgdd_product_links[manufacturer]):
                    futures.append(executor.submit(fetch_html, url, manufacturer, id))

            for future in as_completed(futures):
                if not future.result():
                    continue

                # If success, then insert to database
                result = future.result()
                manufacturer = result['Manufacturer']
                url = result['Url']
                raw_html_path = result['Raw_html_path']
                self.conn.execute(build_insert_query(manufacturer, url, raw_html_path))
                self.conn.commit()

        self.log(f'Finish fetching ...')

    # ----------------- Parse raw_htmls -----------------
    def parse_specs(self, html_path: str):
        with open(html_path, 'r', encoding='utf-8') as f:
            soup = bs(f.read(), 'html.parser')

        # Get the product name
        product_name = soup.find('h1').text.strip()

        # Get the box price
        box_price = soup.find('div', {'class': 'box-price'})

        # A function to process the price
        def process_price(price: str) -> int:
            try:
                price = price.replace('₫', '')
                price = price.replace('*', '')
                while '.' in price:
                    price = price.replace('.', '')

                price = price.strip()
                return int(price)
            except:
                return price

        # Get the price
        try:
            present_price: int = process_price(box_price.find('p', {'class': 'box-price-present'}).text.strip())
        except:
            present_price = None  # Do not have present price
        try:
            old_price: str = box_price.find('p', {'class': 'box-price-old'}).text.strip()
            old_price: int = process_price(old_price)
        except:
            old_price = None  # Do not have old price

        if old_price:
            discount = round((old_price - present_price) / old_price, 2)
        else:
            discount = None

        # Buid the raw specs
        def build_raw_specs() -> str:
            raw_specs = ''

            parameter = soup.find('div', {'class': 'parameter'})
            ul = parameter.find('ul')
            lis = ul.find_all('li')

            for li in lis:
                feature = li.find('p', {'class': 'lileft'}).text.strip()
                info = li.find('div', {'class': 'liright'}).text.strip()

                info_list = list(map(lambda x: x.strip(), info.split('\n')))
                info = ', '.join(info_list)

                raw_specs += f'{feature}: {info}\n'

            return raw_specs

        raw_specs = build_raw_specs()

        return {
            'html_path': html_path,
            'product_name': product_name,
            'present_price': present_price,
            'old_price': old_price,
            'discount': discount,
            'raw_specs': raw_specs
        }

    # ----------------- Feature Engineering using GPT -----------------

    def buid_insert_item_query(self, path_to_features, item: dict) -> str:
        detail_info = {}

        path = item['html_path']
        product_name = item['product_name']
        present_price = item['present_price']
        old_price = item['old_price']
        discount = item['discount']
        raw_specs = item['raw_specs']

        # Parse the specs using GPT
        result = convert_json(url=path_to_features[path]['url'], raw_specs=raw_specs)
        self.log(f'===> {result["status"]}: {result["message"]}')

        if result['status'] == 'success':
            item_specs = json.loads(result['data'])
        self.log(json.dumps(item_specs, indent=4, ensure_ascii=False))

        # Now insert to data_json
        detail_info['product_name'] = product_name
        detail_info['url'] = path_to_features[path]['url']
        detail_info['present_price'] = present_price
        detail_info['old_price'] = old_price
        detail_info['discount'] = discount
        detail_info['manufacturer'] = path_to_features[path]['manufacturer']
        detail_info['raw_html_path'] = path_to_features[path]['raw_html_path']

        # Merge the specs in to data_json[path]
        for key, val in item_specs.items():
            detail_info[key] = val

        # Build the query
        query = self.build_insert_query('laptop_detail_update', detail_info)

        return query, detail_info

    def feature_engineering(self):
        queries = []
        detail_infos = []

        path_to_features = {}

        result = self.conn.execute('SELECT * FROM html').fetchall()

        for row in result:
            path_to_features[row[3]] = {
                'manufacturer': row[1],
                'url': row[2],
                'raw_html_path': row[3],
            }

        # Next step, we need to parse the specs from the raw specs
        with open(os.path.join('data/tgdd_detail.json'), 'r', encoding='utf-8') as f:
            tgdd_detail: dict = json.load(f)

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = []

            for item in tgdd_detail:
                futures.append(executor.submit(self.buid_insert_item_query, path_to_features, item))

            for idx, future in enumerate(as_completed(futures)):
                self.log(f'===> [{idx}/{len(futures)}]==========================')
                query = future.result()[0]
                detail_info = future.result()[1]
                queries.append(query)
                detail_infos.append(detail_info)

        with open('data/tgdd_robust_detail_info.json', 'w', encoding='utf-8') as f:
            json.dump(detail_infos, f, indent=4, ensure_ascii=False)

        self.log('Inserting to database ...')

        for query in queries:
            try:
                self.conn.execute(query)
                self.conn.commit()
            except:
                continue

        self.log('Done')
        self.conn.close()


if __name__ == '__main__':
    tgdd = Tgdd(headless=True)
    # tgdd.get_all_product_links()
    # tgdd._crawl_raw_htmls()

    # Test robustness (Done)
    # data = []
    # for file_name in os.listdir('data/raw_htmls/tgdd'):
    #     print('Parsing', file_name)
    #     item = tgdd.parse_specs(f'data/raw_htmls/tgdd/{file_name}')
    #     data.append(item)
    #     print('====')

    # with open('data/tgdd_detail.json', 'w', encoding='utf-8') as f:
    #     json.dump(data, f, indent=4, ensure_ascii=False)

    tgdd.feature_engineering()
