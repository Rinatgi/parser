from widget_ui import MainApp
from catalog_db import CatalogJSONManager
from parser_db import Parser


class Application:
    def __init__(self):
        self.catalog_manager = CatalogJSONManager()
        self.parser = Parser(catalog_manager=self.catalog_manager)
        self.main_window = MainApp(catalog_manager=self.catalog_manager, parser=self.parser)

    def start(self):
        """
        """
        self.main_window.run()

