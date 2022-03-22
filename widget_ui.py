from kivy.app import App
from parserlayout import ParserLayout
from kivy.core.window import Window


class MainApp(App):
    def __init__(self, catalog_manager, parser):
        super().__init__()
        self.catalog_manager = catalog_manager
        self.parser = parser

    def build(self):
        return ParserLayout(catalog_manager=self.catalog_manager, parser=self.parser)
