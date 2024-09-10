import reflex as rx
import requests
import base64
import os
from typing import Dict, List, Any
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Obtener credenciales de las variables de entorno
CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")

TOKEN_URL = "https://accounts.spotify.com/api/token"
SPOTIFY_API_BASE_URL = "https://api.spotify.com/v1"

class State(rx.State):
    access_token: str = ""
    search_query: str = ""
    search_results: List[Dict[str, Any]] = []
    selected_artists: List[Dict[str, Any]] = []
    comparison_result: str = ""
    error_message: str = ""

    def get_access_token(self) -> None:
        if not CLIENT_ID or not CLIENT_SECRET:
            self.error_message = "Error: Credenciales de Spotify no encontradas en las variables de entorno."
            return

        auth_header = base64.b64encode(f"{CLIENT_ID}:{CLIENT_SECRET}".encode()).decode()
        headers = {
            "Authorization": f"Basic {auth_header}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        data = {"grant_type": "client_credentials"}
        try:
            response = requests.post(TOKEN_URL, headers=headers, data=data)
            response.raise_for_status()
            self.access_token = response.json()["access_token"]
        except requests.RequestException as e:
            self.error_message = f"Error obteniendo el token de acceso: {str(e)}"

    def search_artists(self) -> None:
        if not self.access_token:
            self.get_access_token()
        
        if self.error_message:
            return

        headers = {"Authorization": f"Bearer {self.access_token}"}
        params = {"q": self.search_query, "type": "artist", "limit": 5}
        try:
            response = requests.get(f"{SPOTIFY_API_BASE_URL}/search", headers=headers, params=params)
            response.raise_for_status()
            self.search_results = response.json()["artists"]["items"]
        except requests.RequestException as e:
            self.error_message = f"Error en la búsqueda: {str(e)}"

    def select_artist(self, artist: Dict[str, Any]) -> None:
        if len(self.selected_artists) < 2:
            self.selected_artists.append(artist)
        if len(self.selected_artists) == 2:
            self.compare_popularity()

    def compare_popularity(self) -> None:
        if len(self.selected_artists) != 2:
            self.error_message = "Por favor, selecciona dos artistas para comparar."
            return

        artist1, artist2 = self.selected_artists
        popularity1 = artist1["popularity"]
        popularity2 = artist2["popularity"]

        if popularity1 > popularity2:
            self.comparison_result = f"{artist1['name']} (Popularidad: {popularity1}) es más popular que {artist2['name']} (Popularidad: {popularity2})."
        elif popularity2 > popularity1:
            self.comparison_result = f"{artist2['name']} (Popularidad: {popularity2}) es más popular que {artist1['name']} (Popularidad: {popularity1})."
        else:
            self.comparison_result = f"{artist1['name']} y {artist2['name']} tienen la misma popularidad ({popularity1})."

    def reset_comparison(self) -> None:
        self.selected_artists = []
        self.comparison_result = ""
        self.error_message = ""

def index() -> rx.Component:
    return rx.vstack(
        rx.heading("Comparación de Popularidad en Spotify"),
        rx.hstack(
            rx.input(placeholder="Buscar artista", on_change=State.set_search_query),
            rx.button("Buscar", on_click=State.search_artists),
        ),
        rx.vstack(
            rx.foreach(
                State.search_results,
                lambda artist: rx.button(
                    artist["name"],
                    on_click=lambda: State.select_artist(artist),
                    is_disabled=State.selected_artists.length() >= 2
                )
            )
        ),
        rx.text("Artistas seleccionados:"),
        rx.vstack(
            rx.foreach(
                State.selected_artists,
                lambda artist: rx.text(artist["name"])
            )
        ),
        rx.button("Comparar", on_click=State.compare_popularity, is_disabled=State.selected_artists.length() != 2),
        rx.button("Reiniciar", on_click=State.reset_comparison),
        rx.text(State.comparison_result),
        rx.text(State.error_message, color="red"),
        spacing="1em"
    )

app = rx.App()
app.add_page(index)