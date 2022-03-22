from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.treeview import TreeView, TreeViewLabel
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from setting import DATE_FORMAT


class ParserLayout(GridLayout):
    def __init__(self, catalog_manager, parser):
        super().__init__()
        self.parser = parser
        self.node = {'name': 'Каталог'}
        self.rows = 2
        self.catalog_manager = catalog_manager
        if not self.catalog_manager.get_catalog():
            self.parser.start_parsing()
        else:
            catalog_list = self.catalog_manager.get_catalog()

            self.node['children'] = catalog_list
            self.__create_widgets()
            self.__place_widgets()

    def __create_widgets(self):
        self.top_layout = GridLayout()
        self.top_layout.cols = 4
        self.top_layout.spacing = 10
        self.top_layout.col_force_default = False
        self.top_layout.row_force_default = True
        self.top_layout.col_default_height = 300
        self.top_layout.row_default_height = 500
        self.catalog_view = CatalogView()
        self.catalog_view.select_handler = self.add_node
        self.select_view = TreeView(root_options=dict(text='Список поиска'),
                                    hide_root=False,
                                    indent_level=4,
                                    size_hint_y=None,
                                    )
        self.product_view = ProductView()
        self.product_view.select_handler = self.product_info
        self.button_layout = GridLayout(row_force_default=True,
                                        row_default_height=40,
                                        size_hint=(0.3, 0.05))
        self.scroll = ScrollView(size_hint=(1, 0.5),
                                 size=(self.top_layout.width, self.top_layout.height),
                                 scroll_type=['bars', 'content'])
        self.scroll_select = ScrollView(size_hint=(1, 0.8),
                                        size=(self.top_layout.width, self.top_layout.height),
                                        scroll_type=['bars', 'content']
                                        )
        self.scroll_product = ScrollView(size_hint=(1, 1),
                                         size=(self.top_layout.width, self.top_layout.height),
                                         scroll_type=['bars', 'content']
                                         )
        self.select_view.bind(minimum_height=self.select_view.setter('height'))
        self.product_view.bind(minimum_height=self.product_view.setter('height'))
        self.catalog_view.bind(minimum_height=self.catalog_view.setter('height'))
        self.button_layout.cols = 4
        self.button_parsing = Button(text="Найти товары",
                                     font_size=12,
                                     on_release=self.get_path_products,
                                     size_hint_y=None,
                                     )
        self.button_catalog = Button(text='Удалить категорию',
                                     font_size=12,
                                     on_release=self.delete_node,
                                     size_hint_y=None,
                                     )
        self.button_add = Button(text="Сбросить поиск",
                                 font_size=12,
                                 on_release=self.add_node,
                                 size_hint_y=None
                                 )
        self.info_top_layout = GridLayout(rows=2)
        self.info_layout = GridLayout(rows=3,
                                      cols=2,
                                      minimum_height=20,
                                      row_force_default=True,
                                      row_default_height=30

                                      )
        self.label_info = Label(text='Информация о товаре',
                                size_hint_x=0.5,
                                size_hint_y=0.06,
                                width=100,
                                font_size=14)
        self.label_name_price = Label(text='Цена',
                                      font_size=12,
                                      size_hint_x=0.5,
                                      size_hint_y=0.1,
                                      height=50)
        self.label_price = Label(text='0.00',
                                 font_size=12,
                                 size_hint_x=0.5,
                                 size_hint_y=0.1,
                                 height=50)
        self.label_name_date = Label(text='Дата цены',
                                     font_size=12,
                                     size_hint_x=0.5,
                                     size_hint_y=0.1,
                                     height=10)
        self.label_date = Label(text='01/01/2022',
                                font_size=12,
                                size_hint_x=0.5,
                                size_hint_y=0.1,
                                height=50)
        self.label_name_link = Label(text='Ссылка на товар',
                                     font_size=12,
                                     size_hint_x=0.5,
                                     size_hint_y=0.1,
                                     height=50)
        self.label_link = Label(markup=True,
                                font_size=12,
                                text='[ref=]My link[/ref]',
                                size_hint_x=0.5,
                                size_hint_y=0.1,
                                height=50,
                                )

    def __place_widgets(self):
        self.add_widget(self.top_layout)
        self.add_widget(self.button_layout)
        self.top_layout.add_widget(self.scroll)
        self.top_layout.add_widget(self.scroll_select)
        self.top_layout.add_widget(self.scroll_product)
        self.top_layout.add_widget(self.info_top_layout)
        self.scroll.add_widget(self.catalog_view)
        self.scroll_select.add_widget(self.select_view)
        self.scroll_product.add_widget(self.product_view)
        self.button_layout.add_widget(self.button_parsing)
        self.button_layout.add_widget(self.button_catalog)
        self.button_layout.add_widget(self.button_add)
        self.info_top_layout.add_widget(self.label_info)
        self.info_top_layout.add_widget(self.info_layout)
        self.info_layout.add_widget(self.label_name_price)
        self.info_layout.add_widget(self.label_price)
        self.info_layout.add_widget(self.label_name_date)
        self.info_layout.add_widget(self.label_date)
        self.info_layout.add_widget(self.label_name_link)
        self.info_layout.add_widget(self.label_link)
        self.populate_tree_view(self.catalog_view, None, self.node)

    def populate_tree_view(self, tree_view, parent, node):
        """
            создаем наш каталог
        """
        if parent is None:
            tree_node = tree_view.add_node(TreeViewLabel(text=node['name'],
                                                         is_open=False))
        else:
            tree_node = tree_view.add_node(TreeViewLabel(text=node['name'],
                                                         is_open=False), parent)

        for child_node in node['children']:
            self.populate_tree_view(tree_view, tree_node, child_node)

    def add_node(self):
        """
            добавляем директорию в список поиска товаров
        """
        node = self.catalog_view.selected_node
        self.select_view.add_node(TreeViewLabel(text=node.text))
        self.catalog_view.remove_node(node)

    def delete_node(self, obj):
        """
            удаляем директорию в списке поиска товаров
        """
        node = self.select_view.selected_node
        self.select_view.remove_node(node)

    def get_path_products(self, obj):
        """
            получаем ссылку на каталог товаров из подкатегории
        """
        subdirectory = self.select_view.selected_node.text
        print(subdirectory)
        row_product = self.parser.get_path_subdirectory(subdirectory)
        self.search_products(row_product)

    def search_products(self, row_subdirectory):
        """
            запускаем парсер и
            получаем список наших товаров
        """
        path = row_subdirectory[2]
        subdirectory_id = row_subdirectory[0]
        print(subdirectory_id)
        self.parser.parsing_items(path, subdirectory_id)
        product_list = self.parser.get_products_list(subdirectory_id)
        for product in product_list:
            self.product_view.add_node(TreeViewLabel(text=product))

    def product_info(self):
        product_name = self.product_view.selected_node.text
        product_info = self.parser.get_product_info(product_name)
        print(product_info['price'])
        self.label_price.text = ""
        self.label_price.text = str(product_info['price']) + product_info['item_product']


class CatalogView(TreeView):
    def __init__(self):
        super().__init__()
        self.root_options = dict(text='Леруа Мерлен')
        self.hide_root = False
        self.indent_level = 4
        self.size_hint_y = None

    def on_touch_down(self, touch):
        super().on_touch_down(touch)
        if touch.is_double_tap and self.collide_point(*touch.pos):
            self.select_handler()

    def select_handler(self):
        pass


class TopLayout(GridLayout):
    def __init__(self):
        super().__init__()
        self.height = 400
        self.spacing = 5


class ProductView(TreeView):
    def __init__(self):
        super().__init__()
        self.root_options = dict(text='Список продуктов')
        self.hide_root = False
        self.indent_level = 3
        self.size_hint_y = None

    def on_touch_down(self, touch):
        super().on_touch_down(touch)
        if touch.is_double_tap and self.collide_point(*touch.pos):
            self.select_handler()

    def select_handler(self):
        pass

