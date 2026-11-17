"""Aplicación móvil de GedeNaz construida con Kivy."""

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.uix.textinput import TextInput

from api_client import ApiClient


class LoginScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(
            orientation="vertical",
            padding=24,
            spacing=12,
        )
        layout.add_widget(Label(text="GedeNaz", font_size="32sp", size_hint_y=None, height=56))
        layout.add_widget(Label(text="URL de la API", size_hint_y=None, height=28))
        self.url_input = TextInput(
            text="https://",
            multiline=False,
            size_hint_y=None,
            height=48,
        )
        layout.add_widget(self.url_input)
        layout.add_widget(Label(text="Usuario", size_hint_y=None, height=28))
        self.username_input = TextInput(multiline=False, size_hint_y=None, height=48)
        layout.add_widget(self.username_input)
        layout.add_widget(Label(text="Contraseña", size_hint_y=None, height=28))
        self.password_input = TextInput(
            password=True,
            multiline=False,
            size_hint_y=None,
            height=48,
        )
        layout.add_widget(self.password_input)
        self.message = Label(text="", size_hint_y=None, height=48)
        layout.add_widget(self.message)
        login_button = Button(text="Iniciar sesión", size_hint_y=None, height=52)
        login_button.bind(on_release=self.login)
        layout.add_widget(login_button)
        self.add_widget(layout)

    def login(self, _button):
        try:
            client = ApiClient(
                self.url_input.text,
                self.username_input.text.strip(),
                self.password_input.text,
            )
            username = client.login()
            app = App.get_running_app()
            app.api_client = client
            inventory_screen = app.screen_manager.get_screen("inventory")
            inventory_screen.username = username
            app.screen_manager.current = "inventory"
            inventory_screen.load_products()
            self.message.text = ""
        except (ValueError, RuntimeError) as error:
            self.message.text = str(error)


class InventoryScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.username = ""
        layout = BoxLayout(orientation="vertical", padding=16, spacing=10)
        self.title = Label(text="Inventario", font_size="26sp", size_hint_y=None, height=48)
        layout.add_widget(self.title)
        actions = BoxLayout(size_hint_y=None, height=48, spacing=8)
        refresh_button = Button(text="Actualizar")
        refresh_button.bind(on_release=lambda _button: self.load_products())
        actions.add_widget(refresh_button)
        logout_button = Button(text="Cerrar sesión")
        logout_button.bind(on_release=self.logout)
        actions.add_widget(logout_button)
        layout.add_widget(actions)
        self.message = Label(text="", size_hint_y=None, height=36)
        layout.add_widget(self.message)
        self.products = Label(
            text="",
            halign="left",
            valign="top",
            size_hint_y=None,
        )
        self.products.bind(texture_size=self._resize_products)
        from kivy.uix.scrollview import ScrollView

        scroll = ScrollView()
        scroll.add_widget(self.products)
        layout.add_widget(scroll)
        self.add_widget(layout)

    def _resize_products(self, _label, size):
        self.products.height = size[1]
        self.products.text_size = (self.width - 40, None)

    def load_products(self):
        try:
            products = App.get_running_app().api_client.list_products()
            self.products.text = "\n\n".join(
                f"{item['nombre']} ({item['categoria']})\n"
                f"Precio: ${item['precio']}  |  Stock: {item['stock']}"
                for item in products
            ) or "No hay productos registrados."
            self.message.text = f"Sesión: {self.username}"
        except RuntimeError as error:
            self.message.text = str(error)

    def logout(self, _button):
        app = App.get_running_app()
        app.api_client = None
        app.screen_manager.current = "login"


class GedeNazMobileApp(App):
    def build(self):
        self.api_client = None
        self.screen_manager = ScreenManager()
        self.screen_manager.add_widget(LoginScreen(name="login"))
        self.screen_manager.add_widget(InventoryScreen(name="inventory"))
        return self.screen_manager


if __name__ == "__main__":
    GedeNazMobileApp().run()
