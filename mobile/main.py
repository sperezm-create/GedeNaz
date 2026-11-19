"""Aplicación móvil de GedeNaz construida con Kivy."""

from kivy.app import App
from kivy.core.window import Window
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.uix.textinput import TextInput

from api_client import ApiClient

# Paleta suave (beige plano) igual que el login de escritorio.
BG = (0.945, 0.914, 0.863, 1)
FIELD_BG = (0.98, 0.965, 0.933, 1)
TEXT = (0.23, 0.2, 0.16, 1)
MUTED = (0.48, 0.43, 0.365, 1)
ACCENT = (0.659, 0.506, 0.29, 1)
ERROR = (0.65, 0.24, 0.18, 1)
Window.clearcolor = BG
DEFAULT_API_URL = "http://127.0.0.1:8000"


class LoginScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation="vertical", padding=(32, 40), spacing=10)
        layout.add_widget(
            Label(text="GedeNaz", font_size="34sp", bold=True, color=TEXT,
                  size_hint_y=None, height=64)
        )
        layout.add_widget(self._label("Usuario"))
        self.username_input = self._field()
        layout.add_widget(self.username_input)
        layout.add_widget(self._label("Contraseña"))
        self.password_input = self._field(password=True)
        layout.add_widget(self.password_input)
        self.message = Label(text="", color=ERROR, size_hint_y=None, height=44)
        layout.add_widget(self.message)
        login_button = Button(
            text="Entrar", size_hint_y=None, height=52, bold=True,
            background_normal="", background_color=ACCENT, color=(1, 1, 1, 1),
        )
        login_button.bind(on_release=self.login)
        layout.add_widget(login_button)
        layout.add_widget(self._label("Servidor"))
        self.url_input = self._field()
        self.url_input.text = DEFAULT_API_URL
        layout.add_widget(self.url_input)
        self.add_widget(layout)
        for field in (self.username_input, self.password_input, self.url_input):
            field.bind(text=lambda *_: setattr(self.message, "text", ""))
        self.password_input.bind(on_text_validate=self.login)

    @staticmethod
    def _label(text):
        return Label(text=text, color=MUTED, halign="left", size_hint_y=None, height=24)

    @staticmethod
    def _field(password=False):
        return TextInput(
            password=password, multiline=False, size_hint_y=None, height=48,
            background_normal="", background_active="", background_color=FIELD_BG,
            foreground_color=TEXT, cursor_color=TEXT, padding=(12, 12),
        )

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
            self.password_input.text = ""
            self.message.text = ""
        except (ValueError, RuntimeError) as error:
            self.password_input.text = ""  # primero: este cambio limpia el mensaje
            self.message.text = str(error)


class InventoryScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.username = ""
        layout = BoxLayout(orientation="vertical", padding=16, spacing=10)
        self.title = Label(text="Inventario", font_size="26sp", color=TEXT, size_hint_y=None, height=48)
        layout.add_widget(self.title)
        actions = BoxLayout(size_hint_y=None, height=48, spacing=8)
        refresh_button = Button(text="Actualizar", background_normal="", background_color=ACCENT)
        refresh_button.bind(on_release=lambda _button: self.load_products())
        actions.add_widget(refresh_button)
        logout_button = Button(text="Cerrar sesión", background_normal="", background_color=ACCENT)
        logout_button.bind(on_release=self.logout)
        actions.add_widget(logout_button)
        layout.add_widget(actions)
        self.message = Label(text="", color=MUTED, size_hint_y=None, height=36)
        layout.add_widget(self.message)
        self.products = Label(
            text="",
            color=TEXT,
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
