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

GENRES = [
    "black metal", "brutal death metal", "deathcore", "folk metal", "folk rock",
    "goregrind", "grindcore", "grunge", "hard rock", "heavy metal", "indie",
    "industrial metal", "nu metal", "punk", "punk rock", "progressive metal",
    "rap metal", "rap rock", "rock", "rock alternativo", "slamming", "thrash metal"
]

class Artist(rx.Base):
    name: str
    genres: List[str]
    count: int

class State(rx.State):
    access_token: str = ""
    search_query: str = ""
    search_results: List[Dict[str, Any]] = []
    selected_artists: List[Dict[str, Any]] = []
    comparison_result: str = ""
    error_message: str = ""
    country_popularity: str = ""
    debug_info: str = ""
    selected_genre: str = ""
    genre_artists: List[Artist] = []
    is_loading: bool = False

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
        params = {"q": self.search_query, "type": "artist", "limit": 3}
        try:
            response = requests.get(f"{SPOTIFY_API_BASE_URL}/search", headers=headers, params=params)
            response.raise_for_status()
            artists = response.json()["artists"]["items"]
            self.search_results = []
            for artist in artists:
                artist_info = {
                    "id": artist["id"],
                    "name": artist["name"],
                    "genres": ", ".join(artist["genres"]),
                    "popularity": artist["popularity"],
                    "followers": artist["followers"]["total"],
                }
                artist_response = requests.get(f"{SPOTIFY_API_BASE_URL}/artists/{artist['id']}", headers=headers)
                if artist_response.status_code == 200:
                    artist_details = artist_response.json()
                    artist_info["country"] = self.get_country_name(artist_details.get("birthplace") or artist_details.get("location") or "Unknown")
                else:
                    artist_info["country"] = "Información no disponible"
                self.search_results.append(artist_info)
        except requests.RequestException as e:
            self.error_message = f"Error en la búsqueda: {str(e)}"

    def get_country_name(self, location: str) -> str:
        return location

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

        self.comparison_result = f"{artist1['name']} (de {artist1['country']}, Popularidad: {popularity1}) vs {artist2['name']} (de {artist2['country']}, Popularidad: {popularity2}).\n"

        if popularity1 > popularity2:
            self.comparison_result += f"{artist1['name']} es más popular globalmente."
        elif popularity2 > popularity1:
            self.comparison_result += f"{artist2['name']} es más popular globalmente."
        else:
            self.comparison_result += f"Ambos artistas tienen la misma popularidad global."

    def reset_comparison(self) -> None:
        self.selected_artists = []
        self.comparison_result = ""
        self.error_message = ""
        self.country_popularity = ""
        self.debug_info = ""

    def get_country_popularity(self, artist: Dict[str, Any], country: str = "HN") -> None:
        if not self.access_token:
            self.get_access_token()
        
        if self.error_message:
            return

        headers = {"Authorization": f"Bearer {self.access_token}"}
        artist_id = artist["id"]
        artist_name = artist["name"]
        
        self.debug_info = f"Consultando artista: {artist_name} (ID: {artist_id})\n"
        self.debug_info += f"País de origen: {artist['country']}\n"
        self.debug_info += f"Géneros: {artist['genres']}\n"
        self.debug_info += f"Popularidad global: {artist['popularity']}\n"
        self.debug_info += f"Seguidores: {artist['followers']}\n"

        params = {"country": country, "limit": 10}
        try:
            response = requests.get(f"{SPOTIFY_API_BASE_URL}/artists/{artist_id}/top-tracks", headers=headers, params=params)
            response.raise_for_status()
            tracks = response.json()["tracks"]
            
            if not tracks:
                self.country_popularity = f"No se encontraron pistas populares en Honduras para {artist_name}."
                return

            self.debug_info += "Pistas principales en Honduras:\n"
            for track in tracks:
                self.debug_info += f"- {track['name']} (Popularidad: {track['popularity']})\n"

            total_popularity = sum(track["popularity"] for track in tracks)
            avg_popularity = total_popularity / len(tracks)
            
            popularity_level = "baja"
            if avg_popularity > 70:
                popularity_level = "muy alta"
            elif avg_popularity > 50:
                popularity_level = "alta"
            elif avg_popularity > 30:
                popularity_level = "moderada"

            top_track = max(tracks, key=lambda x: x["popularity"])
            
            self.country_popularity = f"La popularidad de {artist_name} (de {artist['country']}) en Honduras es {popularity_level}. " \
                                      f"Su canción más popular en Honduras es '{top_track['name']}' " \
                                      f"con una popularidad de {top_track['popularity']}."

        except requests.RequestException as e:
            self.error_message = f"Error obteniendo la popularidad por país: {str(e)}"

    def select_genre(self, genre: str):
        self.selected_genre = genre
        self.get_artists_by_genre()

    def get_artists_by_genre(self):
        self.is_loading = True
        if not self.access_token:
            self.get_access_token()
        
        if self.error_message:
            self.is_loading = False
            return

        headers = {"Authorization": f"Bearer {self.access_token}"}
        
        try:
            # Buscar playlists relacionadas con el género
            playlist_params = {"q": self.selected_genre, "type": "playlist", "market": "HN", "limit": 5}
            playlist_response = requests.get(f"{SPOTIFY_API_BASE_URL}/search", headers=headers, params=playlist_params)
            playlist_response.raise_for_status()
            playlists = playlist_response.json()["playlists"]["items"]

            artist_count = {}
            for playlist in playlists:
                tracks_response = requests.get(f"{SPOTIFY_API_BASE_URL}/playlists/{playlist['id']}/tracks", headers=headers)
                if tracks_response.status_code == 200:
                    tracks = tracks_response.json()["items"]
                    for track in tracks:
                        if track["track"] and track["track"]["artists"]:
                            artist = track["track"]["artists"][0]
                            if artist["id"] in artist_count:
                                artist_count[artist["id"]]["count"] += 1
                            else:
                                artist_count[artist["id"]] = {
                                    "name": artist["name"],
                                    "count": 1,
                                    "genres": []
                                }

            # Obtener detalles de los artistas y filtrar por género
            genre_artists = []
            for artist_id, artist_info in artist_count.items():
                artist_response = requests.get(f"{SPOTIFY_API_BASE_URL}/artists/{artist_id}", headers=headers)
                if artist_response.status_code == 200:
                    artist_details = artist_response.json()
                    if self.selected_genre.lower() in [g.lower() for g in artist_details["genres"]]:
                        genre_artists.append(Artist(
                            name=artist_info["name"],
                            genres=artist_details["genres"],
                            count=artist_info["count"]
                        ))

            # Ordenar y limitar a los top 10 artistas
            self.genre_artists = sorted(genre_artists, key=lambda x: x.count, reverse=True)[:10]

        except requests.RequestException as e:
            self.error_message = f"Error obteniendo los artistas del género {self.selected_genre}: {str(e)}"
        
        self.is_loading = False

def index() -> rx.Component:
    return rx.vstack(
        rx.heading("Comparación de Popularidad en Spotify"),
        rx.vstack(
            rx.hstack(
                rx.input(placeholder="Buscar artista", on_change=State.set_search_query),
                rx.button("Buscar", on_click=State.search_artists),
            ),
            rx.vstack(
                rx.foreach(
                    State.search_results,
                    lambda artist: rx.vstack(
                        rx.text(f"{artist['name']} - País: {artist['country']}"),
                        rx.text(f"Géneros: {artist['genres']}"),
                        rx.text(f"Popularidad global: {artist['popularity']} - Seguidores: {artist['followers']}"),
                        rx.hstack(
                            rx.button(
                                "Seleccionar para comparación",
                                on_click=lambda: State.select_artist(artist),
                                is_disabled=State.selected_artists.length() >= 2
                            ),
                            rx.button(
                                "Popularidad en Honduras",
                                on_click=lambda: State.get_country_popularity(artist),
                            )
                        ),
                        rx.divider()
                    )
                )
            ),
            rx.text("Artistas seleccionados:"),
            rx.vstack(
                rx.foreach(
                    State.selected_artists,
                    lambda artist: rx.text(f"{artist['name']} ({artist['country']})")
                )
            ),
            rx.button("Comparar", on_click=State.compare_popularity, is_disabled=State.selected_artists.length() != 2),
            rx.button("Reiniciar", on_click=State.reset_comparison),
            rx.text(State.comparison_result),
            rx.text(State.country_popularity),
            rx.text(State.error_message, color="red"),
            rx.text(State.debug_info),
        ),
        rx.vstack(
            rx.heading("Top Artistas en Honduras por Género"),
            rx.text("Selecciona un género para ver los artistas:"),
            rx.form.root(
                rx.vstack(
                    rx.select(
                        GENRES,
                        placeholder="Selecciona un género",
                        on_change=State.select_genre,
                        name="genre",
                    ),
                    width="100%",
                ),
                width="100%",
            ),
            rx.cond(
                State.is_loading,
                rx.spinner(),
                rx.cond(
                    State.genre_artists.length() > 0,
                    rx.vstack(
                        rx.heading(f"Top Artistas en el género {State.selected_genre}", size="md"),
                        rx.vstack(
                            rx.foreach(
                                State.genre_artists,
                                lambda artist: rx.hstack(
                                    rx.text(artist.name),
                                    rx.spacer(),
                                    rx.text(f"Apariciones: {artist.count}")
                                )
                            )
                        ),
                        padding="1em",
                        border="1px solid #ccc",
                        border_radius="md",
                        margin="1em 0"
                    ),
                    rx.text("No se encontraron artistas para este género.")
                )
            ),
            rx.text(State.error_message, color="red"),
        ),
        spacing="1em",
    )

app = rx.App()
app.add_page(index)