"""Cliente HTTP para comunicarse con GedeNaz API desde Android."""

from urllib.parse import urlparse

import requests


class ApiClient:
    def __init__(
        self,
        base_url: str,
        username: str,
        password: str,
        timeout: float = 10.0,
    ) -> None:
        normalized_url = base_url.strip().rstrip("/")
        parsed_url = urlparse(normalized_url)
        if parsed_url.scheme not in {"http", "https"} or not parsed_url.netloc:
            raise ValueError("Ingresa la URL completa del servidor, por ejemplo https://servidor.")
        self.base_url = normalized_url
        self.timeout = timeout
        self.session = requests.Session()
        self.session.auth = (username, password)

    def login(self) -> str:
        response = self._request("POST", "/auth/login")
        if not isinstance(response, dict) or not response.get("username"):
            raise RuntimeError("El servidor devolvió datos de inicio de sesión inválidos.")
        return str(response["username"])

    def list_products(self) -> list[dict]:
        response = self._request("GET", "/products")
        if not isinstance(response, list):
            raise RuntimeError("La API devolvió una lista de productos inválida.")
        return response

    def _request(self, method: str, path: str):
        try:
            response = self.session.request(
                method,
                f"{self.base_url}{path}",
                timeout=self.timeout,
            )
            response.raise_for_status()
        except requests.HTTPError as error:
            status_code = error.response.status_code if error.response is not None else 0
            if status_code == 401:
                message = "Usuario o contraseña incorrectos."
            else:
                message = f"El servidor rechazó la solicitud (HTTP {status_code})."
            raise RuntimeError(message) from error
        except requests.RequestException as error:
            raise RuntimeError(
                "No se pudo comunicar con el servidor GedeNaz. "
                "Verifica la URL y la conexión."
            ) from error
        if response.status_code == 204:
            return None
        try:
            return response.json()
        except requests.exceptions.JSONDecodeError as error:
            raise RuntimeError("El servidor devolvió una respuesta inválida.") from error
