import requests

# Define tu clave de API y otros parámetros
API_KEY = ''
URL = 'https://www.googleapis.com/youtube/v3/videos'
PARAMS = {
    'part': 'snippet,statistics',
    'chart': 'mostPopular',
    'regionCode': 'HN',
    'videoCategoryId': '10',  # Suponiendo que '10' es la categoría de Música
    'key': API_KEY
}

# Hacer la solicitud a la API de YouTube
response = requests.get(URL, params=PARAMS)
data = response.json()

# Verificar si la respuesta contiene la clave 'items'
if 'items' in data:
    for video in data['items']:
        title = video['snippet']['title']
        view_count = video['statistics']['viewCount']
        print(title, view_count)
else:
    # Imprimir mensaje de error si la API devuelve un error
    error_message = data.get('error', {}).get('message', 'No se especificó un error.')
    print(f"Error en la solicitud a la API: {error_message}")
