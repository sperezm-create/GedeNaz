from __future__ import annotations

import json
import os
import re
from threading import Thread
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle
from kivy.metrics import dp
from kivy.properties import ListProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget


API_BASE_URL = os.getenv("GEDENAZ_API_URL", "https://gedenaz-api.onrender.com").rstrip("/")
# TiDB credentials stay on the Flask server. Point this URL at that server,
# configured with GEDENAZ_ENV_FILE=env.tidb; never embed DB credentials here.
DB_API_URL = os.getenv("GEDENAZ_DB_API_URL", "http://127.0.0.1:5001").rstrip("/")


class ColorBlock(BoxLayout):
    background_color = ListProperty([1, 1, 1, 1])

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.canvas.before:
            self._color = Color(*self.background_color)
            self._rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._update_rect, size=self._update_rect)
        self.bind(background_color=self._update_color)

    def _update_rect(self, *_args):
        self._rect.pos = self.pos
        self._rect.size = self.size

    def _update_color(self, *_args):
        self._color.rgba = self.background_color


def _request_json(url: str, method: str = "GET", payload: dict | None = None):
    body = json.dumps(payload).encode("utf-8") if payload is not None else None
    request = Request(url, data=body, method=method)
    if body is not None:
        request.add_header("Content-Type", "application/json")
    try:
        # Render can need several seconds to wake a sleeping instance.
        with urlopen(request, timeout=30) as response:
            raw = response.read().decode("utf-8")
            return response.status, json.loads(raw) if raw else None
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")
        if "mysql.connector.errors.InterfaceError" in detail and "Connection refused" in detail:
            raise RuntimeError(
                "El servidor respondió, pero intenta usar MySQL local. "
                "Inicia el servidor TiDB con: python scripts/run_tidb_api.py"
            ) from exc
        # Flask debug pages are HTML; show a compact message instead of dumping
        # the entire traceback into the small mobile dialog.
        detail = re.sub(r"<[^>]+>", " ", detail)
        detail = " ".join(detail.split())
        raise RuntimeError(f"HTTP {exc.code}: {detail or exc.reason}") from exc
    except (URLError, TimeoutError, OSError) as exc:
        raise RuntimeError(f"No se pudo llegar a {url}: {exc}") from exc


class GedeNazApp(App):
    title = "GedeNaz"

    def build(self):
        Window.size = (390, 760)
        Window.clearcolor = (0.95, 0.96, 0.94, 1)
        root = ColorBlock(orientation="vertical", padding=dp(20), spacing=dp(16),
                          background_color=[0.95, 0.96, 0.94, 1])
        root.add_widget(Label(text="GedeNaz", color=(0.09, 0.11, 0.12, 1),
                             font_size=dp(34), bold=True, size_hint_y=None, height=dp(54)))
        root.add_widget(Label(text="Conexiones", color=(0.25, 0.29, 0.31, 1),
                             font_size=dp(18), size_hint_y=None, height=dp(34)))
        self.message_label = Label(text=f"API: {API_BASE_URL}\nTiDB vía API: {DB_API_URL}",
                                   color=(0.18, 0.21, 0.23, 1), font_size=dp(13),
                                   halign="left", valign="middle", size_hint_y=None, height=dp(70))
        self.message_label.bind(size=self.message_label.setter("text_size"))
        root.add_widget(self.message_label)
        root.add_widget(self._button("Probar conexión a la API", self.check_api, [0.15, 0.39, 0.38, 1]))
        root.add_widget(self._button("Ver / editar base TiDB", self.open_database))
        root.add_widget(Widget())
        return root

    def _button(self, text, callback, color=None):
        return Button(text=text, font_size=dp(17), bold=True, background_normal="",
                      background_color=color or [0.55, 0.23, 0.18, 1], color=(1, 1, 1, 1),
                      size_hint_y=None, height=dp(54), on_release=callback)

    def check_api(self, *_args):
        self.message_label.text = f"Comprobando {API_BASE_URL}/health…"
        Thread(target=self._check_api_in_background, daemon=True).start()

    def _check_api_in_background(self):
        try:
            _status, data = _request_json(f"{API_BASE_URL}/health")
            message = f"API disponible: {data.get('service', 'servicio')} ({API_BASE_URL})"
        except Exception as exc:  # el texto distingue red de errores HTTP
            message = f"Fallo al comprobar API: {exc}"
        Clock.schedule_once(lambda _dt: setattr(self.message_label, "text", message), 0)

    def open_database(self, *_args):
        panel = BoxLayout(orientation="vertical", padding=dp(12), spacing=dp(8))
        panel.add_widget(Label(text=f"Productos · {DB_API_URL}", size_hint_y=None, height=dp(32)))
        self.products_label = Label(text="Pulsa 'Cargar productos' para consultar TiDB.",
                                    halign="left", valign="top", size_hint_y=None, height=dp(130))
        self.products_label.bind(size=self.products_label.setter("text_size"))
        panel.add_widget(self.products_label)
        self.product_id = TextInput(hint_text="ID del producto", multiline=False,
                                    input_filter="int", size_hint_y=None, height=dp(42))
        panel.add_widget(self.product_id)
        self.fields = {}
        for name, hint in (("nombre", "Nombre"), ("categoria", "Categoría"),
                           ("precio", "Precio"), ("stock", "Stock")):
            field = TextInput(hint_text=hint, multiline=False, size_hint_y=None, height=dp(40))
            self.fields[name] = field
            panel.add_widget(field)
        actions = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(8))
        actions.add_widget(self._button("Cargar productos", self.load_products, [0.15, 0.39, 0.38, 1]))
        actions.add_widget(self._button("Cargar ID", self.load_product))
        panel.add_widget(actions)
        panel.add_widget(self._button("Guardar cambios", self.save_product, [0.15, 0.39, 0.38, 1]))
        self.db_popup = Popup(title="Base de datos TiDB", content=panel,
                              size_hint=(0.95, 0.92), auto_dismiss=True)
        self.db_popup.open()

    def _run_db_action(self, action):
        self.products_label.text = "Conectando…"
        def work():
            try:
                message = action()
            except Exception as exc:
                message = f"Error: {exc}\nRevisa que el servidor local use env.tidb y esté disponible en {DB_API_URL}."
            Clock.schedule_once(lambda _dt: setattr(self.products_label, "text", message), 0)
        Thread(target=work, daemon=True).start()

    def load_products(self, *_args):
        def action():
            _status, rows = _request_json(f"{DB_API_URL}/productos")
            if not rows:
                return "TiDB respondió correctamente. No hay productos activos."
            return "Productos activos:\n" + "\n".join(
                f"#{row['id']} {row['nombre']} · {row['categoria']} · ${row['precio']} · stock {row['stock']}"
                for row in rows[:30]
            )
        self._run_db_action(action)

    def load_product(self, *_args):
        product_id = self.product_id.text.strip()
        if not product_id:
            self.products_label.text = "Escribe el ID de un producto."
            return
        def action():
            _status, row = _request_json(f"{DB_API_URL}/productos/{product_id}")
            def populate(_dt):
                for name, field in self.fields.items():
                    field.text = str(row.get(name, ""))
            Clock.schedule_once(populate, 0)
            return f"Producto #{row['id']} cargado. Edita los campos y pulsa Guardar cambios."
        self._run_db_action(action)

    def save_product(self, *_args):
        product_id = self.product_id.text.strip()
        if not product_id:
            self.products_label.text = "Escribe el ID del producto que quieres editar."
            return
        payload = {name: field.text.strip() for name, field in self.fields.items()}
        def action():
            _status, row = _request_json(f"{DB_API_URL}/productos/{product_id}", "PUT", payload)
            Clock.schedule_once(lambda _dt: self._clear_product_fields(), 0)
            return f"Producto #{row['id']} guardado correctamente en la base configurada en el servidor."
        self._run_db_action(action)

    def _clear_product_fields(self):
        self.product_id.text = ""
        for field in self.fields.values():
            field.text = ""


if __name__ == "__main__":
    GedeNazApp().run()
