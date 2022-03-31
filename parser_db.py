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
            "SELECT * FROM product WHERE name_product=%s", (product_name,)
        )
        result = self.cur.fetchone()
        self.cur.execute(
            "SELECT date_price, price_product  FROM price_product WHERE fk_product_id=%s", (result[0],)
        )
        product_price_results = self.cur.fetchall()

        product_dict.update(dict(path=result[2],
                                 price_result=product_price_results,
                                 item_product=result[3],
                                 path_image=result[5])
                            )
        return product_dict
