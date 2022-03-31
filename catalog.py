import psycopg2
from setting import DB_NAME, USER, PASSWORD


class CatalogManager:
    def __init__(self):
        self.connection = psycopg2.connect(dbname=DB_NAME, user=USER, password=PASSWORD)
        self.cursor = self.connection.cursor()
        self.tree_catalog = {'name': 'Каталог'}

    def get_catalog_list(self):
        catalog_list = []
        self.cursor.execute(
            """
                SELECT * FROM main_catalog
            """
        )
        main_catalog = self.cursor.fetchall()
        for catalog in main_catalog:
            directory_list = []
            catalog_id = catalog[0]
            self.cursor.execute(
                """
                    SELECT * FROM directory                    
                """
            )
            directories = self.cursor.fetchall()
            for directory in directories:
                subdirectory_list = []
                id_directory = directory[0]
                fk_catalog_id = directory[3]
                if catalog_id == fk_catalog_id:
                    self.cursor.execute("SELECT * FROM subdirectory")
                    subdirectories = self.cursor.fetchall()
                    for subdirectory in subdirectories:
                        fk_directory_id = subdirectory[3]
                        if fk_directory_id == id_directory:
                            subdirectory_dict = {'name': subdirectory[1], 'children': []}
                            subdirectory_list.append(subdirectory_dict)
                    directory_dict = {'name': directory[1], 'children': subdirectory_list}
                    directory_list.append(directory_dict)
            catalog_dict = {'name': catalog[1], 'children': directory_list}
            catalog_list.append(catalog_dict)

        return catalog_list
