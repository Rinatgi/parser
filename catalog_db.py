import os
import json
import datetime
from setting import CATALOG_FILE_NAME


class CatalogJSONManager:

    @staticmethod
    def get_catalog():
        catalog_dict = {}
        catalog = {}
        if os.path.exists(CATALOG_FILE_NAME):
            # если файл существует
            # загружаем словарь каталога товаров
            with open(CATALOG_FILE_NAME, 'r', encoding='utf-8') as f:
                try:
                    # перехватываем ошибки
                    catalog = json.load(f)
                except FileNotFoundError:
                    return catalog_dict

        return catalog

    def save_catalog(self, catalog):
        with open(CATALOG_FILE_NAME, 'w', encoding='utf-8') as f:
            json.dump(catalog, f, ensure_ascii=False)




