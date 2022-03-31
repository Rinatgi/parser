import sys
import datetime, time
import urllib.request
import psycopg2
from setting import DB_NAME, USER, PASSWORD, PATH_IMAGE_CATALOG
from seleniumwire import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException


class ParserProduct:

    def __init__(self):
        self.connection = psycopg2.connect(dbname=DB_NAME, user=USER, password=PASSWORD)
        self.cur = self.connection.cursor()
        self.product_list = []
        self.path_subdirectory = sys.argv[1]
        self.subdirectory_id = int(sys.argv[2])
        self.parsing_items()

    def parsing_items(self):
        """
            Получаем список товаров из категорий: имена, цену и т.д.
        """

        browser = webdriver.Chrome()
        url = 'https://kazan.leroymerlin.ru/' + self.path_subdirectory
        browser.implicitly_wait(20)
        browser.get(url)
        page = True
        count_product = 0
        # amount_product = browser.find_element_by_tag_name('data-qa-products-count')
        # print(amount_product.text)
        while page:
            items_name = browser.find_elements_by_css_selector("a[data-qa='product-image']")
            name_product_list = []
            for item_name in items_name:
                name_product = item_name.get_attribute('aria-label')
                name_product_list.append(name_product)
            self.product_list.append(name_product_list)
            items_href = browser.find_elements_by_css_selector("a[data-qa ='product-name']")
            product_path_list = []
            for item_href in items_href:
                product_path = item_href.get_attribute('href')
                product_path_list.append(product_path)
            self.product_list.append(product_path_list)
            items_price = browser.find_elements_by_css_selector \
                (
                    'div[data-qa="product-primary-price"] p:nth-child(1)'
                )
            product_price_list = []
            for item_price in items_price:
                product_price_str = item_price.text
                product_price = product_price_str.replace(" ", "")
                product_price = product_price.replace(",", ".")
                product_price = float(product_price)
                product_price_list.append(product_price)

            self.product_list.append(product_price_list)
            units_measure = browser.find_elements_by_css_selector \
                (
                    'div[data-qa="product-primary-price"] p:nth-child(2)'
                )
            init_list = []
            for init_measure in units_measure:
                init = init_measure.text
                init_list.append(init)
            self.product_list.append(init_list)
            image_urls_list = []
            image_urls = browser.find_elements_by_css_selector("img[itemprop='image']")
            for image_url in image_urls:
                url = image_url.get_attribute('src')
                image_urls_list.append(url)
            len_list = len(name_product_list)
            n = 0
            while n < len_list:
                self.cur.execute("SELECT product_id, name_product  FROM product WHERE name_product=%s",
                                 (name_product_list[n],))
                result = self.cur.fetchone()
                try:
                    id_product = result[0]
                    self.cur.execute(

                        """
                            INSERT INTO price_product(date_price, price_product, fk_product_id) 
                            VALUES(%(date)s, %(price)s, %(product_id)s) ;
                        """,
                        {
                            'price': product_price_list[n],
                            'date': datetime.date.today(),
                            'product_id': id_product
                        }
                    )
                    self.connection.commit()
                    n += 1
                except TypeError:
                    image = urllib.request.urlopen(image_urls_list[n])
                    time_now = str(time.time())
                    image_name = PATH_IMAGE_CATALOG + time_now + '.jpg'
                    with open(image_name, 'wb') as handler:
                        handler.write(image.read())
                    self.cur.execute(
                        """
                            INSERT INTO product(name_product, path_product, item_product, fk_subdirectory_id, path_image) 
                            VALUES(%(name)s, %(path)s, %(init)s, %(subdirectory_id)s, %(path_image)s) RETURNING product_id;
                        """,
                        {'name': name_product_list[n],
                         'path': product_path_list[n],
                         'init': init_list[n],
                         'subdirectory_id': self.subdirectory_id,
                         'path_image': image_name
                         }
                    )
                    product_id = self.cur.fetchone()[0]
                    self.cur.execute(
                        """
                            INSERT INTO price_product(date_price, price_product, fk_product_id) 
                            VALUES(%(date)s, %(price)s, %(product_id)s) ;
                        """,
                        {
                            'price': product_price_list[n],
                            'date': datetime.date.today(),
                            'product_id': product_id
                        }
                    )
                    self.connection.commit()
                    n += 1
            count_product += len_list
            with open('log.txt', 'w') as file:
                file.write(str(count_product))

            try:
                next_page = WebDriverWait(browser, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "a[data-qa-pagination-item='right']"))
                )
                next_page.click()
                page = True
                time.sleep(6)
            except TimeoutException:
                self.product_list.clear()
                page = False
                browser.close()
        self.cur.close()
        self.connection.close()


parser_product = ParserProduct()
