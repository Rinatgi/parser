from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.treeview import TreeView, TreeViewLabel
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.recycleview import RecycleView
from kivy.uix.image import Image
from kivy.uix.boxlayout import BoxLayout
import subprocess
import sys
import webbrowser
from kivy.clock import Clock


class ParserLayout(ScreenManager):
    def __init__(self, catalog_manager, parser):
        super().__init__()
        self.parser = parser
        self.node = {'name': 'Каталог'}
        self.catalog_manager = catalog_manager
        if not self.catalog_manager.get_catalog():
            self.parser.start_parsing()
        else:
            catalog_list = self.catalog_manager.get_catalog()

            self.node['children'] = catalog_list
            self.__create_widgets()
            self.__place_widgets()

    def __create_widgets(self):
        self.main_screen = Screen(name='main window')
        self.main_layout = GridLayout(rows=2)
        self.screen_parsing_process = Screen(name='Process progress')
        self.layout_parsing_process = BoxLayout(orientation='vertical', spacing=10, size_hint_y=None)
        self.button_back = Button(text='< Назад в главное меню',
                                  size_hint_y=None, height=40,
                                  on_press=lambda x: self.set_screen('main window'))
        self.top_layout = GridLayout()
        self.top_layout.cols = 4
        self.top_layout.spacing = 10
        self.top_layout.col_force_default = False
        self.top_layout.row_force_default = True
        self.top_layout.col_default_height = 300
        self.top_layout.row_default_height = 500
        self.catalog_view = CatalogView()
        self.catalog_view.select_handler = self.add_node
        self.select_view = SelectView()
        self.product_view = ProductView()
        self.product_view.select_handler = self.product_info
        self.select_view.select_handler = self.get_product_list
        self.button_layout = GridLayout(row_force_default=True,
                                        row_default_height=40,
                                        size_hint=(1, 0.06))
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
                                     height=40
                                     )
        self.button_catalog = Button(text='Удалить категорию',
                                     font_size=12,
                                     on_release=self.delete_node,
                                     size_hint_y=None,
                                     height=40
                                     )
        self.button_add = Button(text="Сбросить поиск",
                                 font_size=12,
                                 on_release=self.add_node,
                                 size_hint_y=None,
                                 height=40
                                 )
        self.button_status = Button(text="Статус",
                                    font_size=12,
                                    on_release=lambda x: self.set_screen('Process progress'),
                                    size_hint_y=None,
                                    height=40
                                    )
        self.info_top_layout = GridLayout(rows=3)
        self.info_layout = GridLayout(rows=4,
                                      minimum_height=20,
                                      row_force_default=True,
                                      row_default_height=100
                                      )
        self.price_layout = GridLayout(cols=1, spacing=5, size_hint_y=None)
        self.price_layout.bind(minimum_height=self.price_layout.setter('height'))
        self.root = RecycleView(size_hint=(1, 1), size=(self.info_top_layout.width,
                                                        self.info_top_layout.height))

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
        self.label_link = Label(markup=True,
                                font_size=12,
                                text='[ref=some]Ссылка на товар[/ref]',
                                size_hint_x=0.5,
                                size_hint_y=0.1,
                                height=50,
                                on_ref_press=self.open_link_product
                                )
        self.image_product = Image()

    def __place_widgets(self):
        self.add_widget(self.main_screen)
        self.add_widget(self.screen_parsing_process)
        self.main_screen.add_widget(self.top_layout)
        self.main_screen.add_widget(self.button_layout)
        self.screen_parsing_process.add_widget(self.button_back)
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
        self.button_layout.add_widget(self.button_status)
        self.info_top_layout.add_widget(self.label_info)
        self.info_top_layout.add_widget(self.image_product)
        self.info_top_layout.add_widget(self.info_layout)
        self.info_layout.add_widget(self.label_link)
        self.info_layout.add_widget(self.label_name_price)
        self.info_layout.add_widget(self.root)
        self.root.add_widget(self.price_layout)
        self.populate_tree_view(self.catalog_view, None, self.node)

    def set_screen(self, name_screen):
        self.current = name_screen

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
        self.delete_product_node()

    def delete_product_node(self):
        for node in [i for i in self.product_view.iterate_all_nodes()]:
            self.product_view.remove_node(node)

    def get_path_products(self, obj):
        """
            получаем ссылку на каталог товаров из подкатегории
        """
        list_row_product = []
        subdirectories = self.select_view.iterate_open_nodes()
        for subdirectory in subdirectories:
            if subdirectory.text == 'Выбранные категории':
                continue
            else:
                row_product = self.parser.get_path_subdirectory(subdirectory.text)
                list_row_product.append(row_product)
        self.search_products(list_row_product)

    def search_products(self, list_row_subdirectory):
        """
            запускаем парсер и
            получаем  данные наших товаров
        """
        for row_subdirectory in list_row_subdirectory:
            path = row_subdirectory[2]
            subdirectory_id = row_subdirectory[0]

            self.process = subprocess.Popen([sys.executable, 'parser_product.py', path, str(subdirectory_id)],
                                            stdout=subprocess.PIPE,
                                            universal_newlines=True,
                                            text=True,
                                            )
            self.event = Clock.schedule_interval(self.print_log_process, 10)
            self.disable_button_search()

    def print_log_process(self, dt):
        """
            выводим  наш ход процесса парсинга

        """
        if self.process.poll() is None:
            with open('log.txt', 'r') as file:
                out = file.read()
            if not out.strip():
                pass
            else:
                text_status = f"Обработано {out} элементов"
                button_text = Button(text=text_status,
                                     size_hint_y=None, height=40,
                                     disabled=True
                                     )
                self.screen_parsing_process.add_widget(button_text)
                open('log.txt', 'w').close()
        else:
            open('log.txt', 'w').close()
            self.screen_parsing_process.add_widget(Label(text='End parsing'))
            self.button_parsing.disabled = False
            self.event.cancel()

    def get_product_list(self):
        self.delete_product_node()
        subdirectory = self.select_view.selected_node.text
        row_product = self.parser.get_path_subdirectory(subdirectory)
        subdirectory_id = row_product[0]
        product_list = self.parser.get_products_list(subdirectory_id)
        for product in product_list:
            self.product_view.add_node(TreeViewLabel(text=product))

    def product_info(self):
        product_name = self.product_view.selected_node.text
        product_info = self.parser.get_product_info(product_name)
        self.link_product = product_info['path']
        price_results = product_info['price_result']
        self.image_product.source = product_info['path_image']
        self.price_layout.clear_widgets()
        for price_result in price_results:
            text_price = str(price_result[1]) + product_info['item_product'] + " " + price_result[0].strftime('%Y-%m-%d')
            button_price = Button(text=text_price, size_hint_y=None, height=20)
            self.price_layout.add_widget(button_price)

    def open_link_product(self, obj, a):
        webbrowser.open(self.link_product)

    def disable_button_search(self):
        if self.process.poll() is None:
            self.button_parsing.disabled = True


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
        if self.collide_point(*touch.pos):
            self.select_handler()

    def select_handler(self):
        pass


class SelectView(TreeView):
    def __init__(self):
        super().__init__()
        self.root_options = dict(text='Выбранные категории')
        self.hide_root = False
        self.indent_level = 4
        self.size_hint_y = None

    def on_touch_down(self, touch):
        super().on_touch_down(touch)
        if self.collide_point(*touch.pos):
            self.select_handler()

    def select_handler(self):
        pass
