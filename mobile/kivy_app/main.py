from __future__ import annotations

import json
import os
from threading import Thread
from urllib.error import URLError
from urllib.request import urlopen

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle
from kivy.metrics import dp
from kivy.properties import ListProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.widget import Widget

#tests simples#
API_BASE_URL = os.getenv("GEDENAZ_API_URL", "https://gedenaz-api.onrender.com").rstrip("/")


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


class GedeNazApp(App):
    title = "GedeNaz"

    def build(self):
        Window.size = (390, 760)
        Window.clearcolor = (0.95, 0.96, 0.94, 1)

        root = ColorBlock(
            orientation="vertical",
            padding=dp(20),
            spacing=dp(16),
            background_color=[0.95, 0.96, 0.94, 1],
        )

        root.add_widget(
            Label(
                text="GedeNaz",
                color=(0.09, 0.11, 0.12, 1),
                font_size=dp(34),
                bold=True,
                size_hint_y=None,
                height=dp(54),
            )
        )
        root.add_widget(
            Label(
                text="Inventario y ventas",
                color=(0.25, 0.29, 0.31, 1),
                font_size=dp(18),
                size_hint_y=None,
                height=dp(34),
            )
        )

        self.status_label = Label(
            text=f"API: {API_BASE_URL}",
            color=(0.18, 0.21, 0.23, 1),
            font_size=dp(14),
            halign="left",
            valign="middle",
            size_hint_y=None,
            height=dp(44),
        )
        self.status_label.bind(size=self.status_label.setter("text_size"))
        root.add_widget(self.status_label)

        root.add_widget(self._button("Probar conexion", self.check_api, [0.15, 0.39, 0.38, 1]))
        root.add_widget(self._button("Productos", lambda *_: self.show_message("Modulo Productos")))
        root.add_widget(self._button("Ventas", lambda *_: self.show_message("Modulo Ventas")))
        root.add_widget(self._button("Reportes", lambda *_: self.show_message("Modulo Reportes")))

        root.add_widget(Widget())

        self.message_label = Label(
            text="Base inicial lista",
            color=(0.19, 0.22, 0.24, 1),
            font_size=dp(15),
            halign="center",
            valign="middle",
            size_hint_y=None,
            height=dp(60),
        )
        self.message_label.bind(size=self.message_label.setter("text_size"))
        root.add_widget(self.message_label)

        return root

    def _button(self, text, callback, color=None):
        return Button(
            text=text,
            font_size=dp(17),
            bold=True,
            background_normal="",
            background_color=color or [0.55, 0.23, 0.18, 1],
            color=(1, 1, 1, 1),
            size_hint_y=None,
            height=dp(54),
            on_release=callback,
        )

    def show_message(self, text):
        self.message_label.text = f"{text}: pantalla pendiente"

    def check_api(self, *_args):
        self.message_label.text = "Probando conexion..."
        Thread(target=self._check_api_in_background, daemon=True).start()

    def _check_api_in_background(self):
        try:
            with urlopen(f"{API_BASE_URL}/health", timeout=5) as response:
                data = json.loads(response.read().decode("utf-8"))
            message = f"Conexion OK: {data.get('service', 'api')}"
        except (OSError, URLError, TimeoutError, json.JSONDecodeError) as exc:
            message = f"No se pudo conectar: {exc}"
        Clock.schedule_once(lambda _dt: setattr(self.message_label, "text", message), 0)

if __name__ == "__main__":
    GedeNazApp().run()

