import requests
from googleapiclient.discovery import build
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Define tu clave de API y otros parámetros
API_KEY = os.getenv("API_KEY_YOUTUBE")
YOUTUBE_API_SERVICE_NAME = 'youtube'
YOUTUBE_API_VERSION = 'v3'

# Crear el objeto del servicio de YouTube
youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, developerKey=API_KEY)

def get_videos_by_genre(genre, max_results=50):
    # Realizar una búsqueda de videos
    search_response = youtube.search().list(
        q=genre,
        type='video',
        part='id,snippet',
        regionCode='HN',
        videoCategoryId='10',  # Categoría de Música
        maxResults=max_results
    ).execute()

    videos = []
    for search_result in search_response.get('items', []):
        video_id = search_result['id']['videoId']
        
        # Obtener estadísticas detalladas del video
        video_response = youtube.videos().list(
            part='snippet,statistics',
            id=video_id
        ).execute()
        
        video_info = video_response['items'][0]
        
        videos.append({
            'title': video_info['snippet']['title'],
            'view_count': int(video_info['statistics']['viewCount']),
            'channel_title': video_info['snippet']['channelTitle']
        })
    
    # Ordenar los videos por número de vistas (de mayor a menor)
    videos.sort(key=lambda x: x['view_count'], reverse=True)
    
    return videos

# Ejemplo de uso
genre = 'thrash metal'  # Puedes cambiar esto al género que desees
top_videos = get_videos_by_genre(genre)

print(f"Top {len(top_videos)} videos de {genre} más vistos en Honduras:")
for i, video in enumerate(top_videos, 1):
    print(f"{i}. {video['title']} - {video['channel_title']} ({video['view_count']} vistas)")