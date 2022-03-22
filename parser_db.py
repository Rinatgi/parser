from seleniumwire import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
import datetime, time
import json
import gzip
import psycopg2
from setting import DB_NAME, USER, PASSWORD


class Parser:

    def __init__(self, catalog_manager):
        self.connection = psycopg2.connect(dbname=DB_NAME, user=USER, password=PASSWORD)
        self.cur = self.connection.cursor()
        self.product_list = []
        self.tree_catalog = {'name': 'Каталог'}
        self.catalog_manager = catalog_manager

    def start_parsing(self):
        """
            запускаем наш парсинг сайта Леруа Мерлен

        """
        self.browser = webdriver.Chrome()
        self.browser.get('http://kazan.leroymerlin.ru/')
        button_catalog = self.browser.find_element_by_css_selector("uc-catalog-button-v2[data-name='catalogue']")
        button_catalog.click()
        self.get_catalog_data()

    def get_catalog_data(self):
        """
            получаем данные наименований каталога товаров
        """

        for request in self.browser.requests:
            if request.url == 'https://kazan.leroymerlin.ru/content/elbrus/kazan/ru/catalogue.navigation.json':
                body_data = request.response.body
                data = gzip.decompress(body_data)
                body_data = data.decode("utf-8")
                self.catalog_data = json.loads(body_data)
                main_catalogs_list = self.catalog_data.get("children")
                catalogs_list = []
                for catalog in main_catalogs_list:
                    """
                        получаем имена и ссылки на каталоги товаров
                    """
                    self.name_catalog = catalog.get("name")
                    self.path_catalog = catalog.get("sitePath")
                    self.catalog_json_path = catalog.get("navigationChunk")
                    self.cur.execute("""
                                        INSERT INTO main_catalog(name_catalog, path_catalog) 
                                        VALUES(%(name)s, %(path)s) RETURNING catalog_id;
                                     """,
                                     {'name': self.name_catalog, 'path': self.path_catalog}
                                     )
                    catalog_id = self.cur.fetchone()[0]
                    self.browser.implicitly_wait(90)
                    children_catalogs = catalog.get("children")
                    directory_list = []
                    for children_catalog in children_catalogs:
                        """
                            получаем категории товаров в каталоге
                        """
                        self.name_directory = children_catalog.get("name")
                        self.path_directory = children_catalog.get('sitePath')
                        self.directory_json_path = children_catalog.get("navigationChunk")
                        self.cur.execute("""
                                            INSERT INTO directory(name_directory, path_directory, catalog_id) 
                                            VALUES(%(name)s, %(path)s, %(catalog_id)s) RETURNING directory_id;
                                         """,
                                         {
                                          'name': self.name_directory,
                                          'path': self.path_directory,
                                          'catalog_id': catalog_id
                                          }
                                         )
                        directory_id = self.cur.fetchone()[0]
                        url_new = 'https://kazan.leroymerlin.ru' + self.directory_json_path
                        request.url = url_new
                        self.browser.get(url_new)
                        time.sleep(5)
                        for _request in self.browser.requests:
                            """
                                получаем данные подкатегорий товаров
                            """
                            if _request.url == url_new:
                                body_child_data = _request.response.body
                                data_child = gzip.decompress(body_child_data)
                                body_child_data = data_child.decode("utf-8")
                                children_catalog_data = json.loads(body_child_data)
                                subdirectories_list = children_catalog_data.get('children')
                                subdirectory_list = []
                                for subdirectory in subdirectories_list:
                                    """
                                        получаем имена и ссылки на подкатегории и переходим на страницу товаров
                                    """
                                    self.name_subdirectory = subdirectory.get('name')
                                    self.path_subdirectory = subdirectory.get('sitePath')
                                    self.cur.execute(
                                        """
                                            INSERT INTO subdirectory(name_subdirectory, path_subdirectory, directory_id) 
                                            VALUES(%(name)s, %(path)s, %(directory_id)s) RETURNING subdirectory_id;
                                        """,
                                        {
                                         'name': self.name_subdirectory,
                                         'path': self.path_subdirectory,
                                         'directory_id': directory_id

                                         }
                                                     )
                                    subdirectory_id = self.cur.fetchone()[0]
                                    self.connection.commit()
                                    self.browser.implicitly_wait(90)
                                    subdirectory['children'] = []
                                    subdirectory_list.append(subdirectory)
                                children_catalog['children'] = subdirectory_list
                                directory_list.append(children_catalog)
                    catalog['children'] = children_catalogs
                    catalogs_list.append(catalog)
                self.tree_catalog['children'] = catalogs_list
                self.catalog_manager.save_catalog(catalogs_list)

    def get_catalog(self):
        return self.tree_catalog

    def parsing_items(self, path_subdirectory, subdirectory_id):
        """
            Получаем список товаров из категорий: имена, цену и т.д.

        """
        browser = webdriver.Chrome()
        url = 'https://kazan.leroymerlin.ru/' + path_subdirectory
        browser.implicitly_wait(30)
        browser.get(url)
        page = True
        while page:
            items_name = browser.find_elements_by_css_selector("span[class='t9jup0e_plp p1h8lbu4_plp']")
            name_product_list = []
            for item_name in items_name:
                name_product = item_name.text
                name_product_list.append(name_product)
            self.product_list.append(name_product_list)
            items_href = browser.find_elements_by_css_selector("a[data-qa ='product-name']")
            product_path_list = []
            for item_href in items_href:
                product_path = item_href.get_attribute('href')
                product_path_list.append(product_path)
            self.product_list.append(product_path_list)
            items_price = browser.find_elements_by_css_selector\
                (
                 "p[class='t3y6ha_plp xc1n09g_plp p1q9hgmc_plp']"
                )
            product_price_list = []
            for item_price in items_price:
                product_price_str = item_price.text
                product_price = product_price_str.replace(" ", "")
                product_price = product_price.replace(",", ".")
                product_price = float(product_price)
                product_price_list.append(product_price)

            self.product_list.append(product_price_list)
            units_measure = browser.find_elements_by_css_selector\
                (
                 "p[class='t3y6ha_plp x9a98_plp pb3lgg7_plp']"
                )
            init_list = []
            for init_measure in units_measure:
                init = init_measure.text
                init_list.append(init)
            self.product_list.append(init_list)
            len_list = len(name_product_list) - 1
            n = 0
            while n < len_list:
                self.cur.execute(
                    """
                        INSERT INTO product(name_product, path_product, item_product, fk_subdirectory_id) 
                        VALUES(%(name)s, %(path)s, %(init)s, %(subdirectory_id)s) RETURNING product_id;
                    """,
                    {'name': name_product_list[n],
                     'path': product_path_list[n],
                     'init': init_list[n],
                     'subdirectory_id': subdirectory_id
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

            try:
                next_page = WebDriverWait(browser, 20).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "a[data-qa-pagination-item='right']"))
                )
                next_page.click()
                page = True
                time.sleep(10)
            except:
                self.product_list.clear()
                page = False
                browser.close()

    def get_path_subdirectory(self, subdirectory):
        self.cur.execute(
            """
                SELECT * FROM subdirectory 
            """
        )
        result = self.cur.fetchall()
        for row in result:
            if row[1] == subdirectory:
                return row
            else:
                continue

    def get_products_list(self, subdirectory_id):
        product_list = []
        self.cur.execute(
            """
                SELECT name_product, fk_subdirectory_id FROM  product           
            """
        )
        results = self.cur.fetchall()
        for result in results:
            if result[1] == subdirectory_id:
                product_list.append(result[0])
        return product_list

    def get_product_info(self, product_name):
        product_dict = {}
        self.cur.execute(
            """
                SELECT * FROM product
            """
        )
        results = self.cur.fetchall()
        for result in results:
            if result[1] == product_name:
                self.cur.execute(
                    """
                        SELECT * FROM price_product                    
                    """
                )
                product_price_results = self.cur.fetchall()
                for price_result in product_price_results:
                    if price_result[3] == result[0]:
                        product_dict.update(dict(path=result[2],
                                                 price=price_result[2],
                                                 date=price_result[1],
                                                 item_product=result[3])
                                            )
                        print(product_dict)
                        return product_dict
