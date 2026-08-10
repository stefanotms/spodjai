import httpx
from typing import Dict, Any, List
from urllib.parse import urlencode
from app.config import settings

class SpotifyRateLimitException(Exception):
    """Excepción lanzada cuando Spotify responde con un código de estado 429 (Límite de Tasa)."""
    def __init__(self, retry_after: int):
        self.retry_after = retry_after
        super().__init__(f"Spotify Rate Limit alcanzado. Reintentar en {retry_after} segundos.")

class SpotifyClient:
    def __init__(self):
        import os
        self.client_id = settings.spotify_client_id
        self.client_secret = settings.spotify_client_secret
        self.redirect_uri = settings.spotify_redirect_uri
        self.auth_url = "https://accounts.spotify.com/authorize"
        self.token_url = "https://accounts.spotify.com/api/token"
        self.api_base_url = "https://api.spotify.com/v1"
        self.cache_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "search_cache.json")
        self.search_cache = {}
        self.load_search_cache()
        
        # Scopes requeridos para leer historial y modificar playlists
        self.scopes = [
            "user-read-recently-played",
            "user-top-read",
            "user-library-read",
            "playlist-modify-public",
            "playlist-modify-private",
            "playlist-read-private",
            "playlist-read-collaborative"
        ]

    def load_search_cache(self):
        import os, json
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, "r", encoding="utf-8") as f:
                    self.search_cache = json.load(f)
            except Exception:
                self.search_cache = {}

    def save_search_cache(self):
        import os, json
        try:
            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump(self.search_cache, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def get_authorization_url(self, state: str = None, redirect_uri: str = None) -> str:
        """
        Genera la URL de autorización para redirigir al usuario a Spotify.
        """
        r_uri = redirect_uri or self.redirect_uri
        params = {
            "client_id": self.client_id,
            "response_type": "code",
            "redirect_uri": r_uri,
            "scope": " ".join(self.scopes),
            "show_dialog": "true"
        }
        if state:
            params["state"] = state
        
        return f"{self.auth_url}?{urlencode(params)}"

    async def get_tokens(self, code: str, redirect_uri: str = None) -> Dict[str, Any]:
        """
        Intercambia el código de autorización por un Access Token y un Refresh Token.
        """
        r_uri = redirect_uri or self.redirect_uri
        async with httpx.AsyncClient() as client:
            payload = {
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": r_uri,
            }
            auth = (self.client_id, self.client_secret)
            headers = {"Content-Type": "application/x-www-form-urlencoded"}
            
            response = await client.post(
                self.token_url,
                data=payload,
                auth=auth,
                headers=headers
            )
            response.raise_for_status()
            return response.json()

    async def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """
        Obtiene un nuevo Access Token utilizando el Refresh Token.
        """
        async with httpx.AsyncClient() as client:
            payload = {
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
            }
            auth = (self.client_id, self.client_secret)
            headers = {"Content-Type": "application/x-www-form-urlencoded"}
            
            response = await client.post(
                self.token_url,
                data=payload,
                auth=auth,
                headers=headers
            )
            response.raise_for_status()
            return response.json()

    async def get_current_user(self, access_token: str) -> Dict[str, Any]:
        """
        Obtiene el perfil del usuario autenticado para validar el token.
        """
        async with httpx.AsyncClient() as client:
            headers = {"Authorization": f"Bearer {access_token}"}
            response = await client.get(f"{self.api_base_url}/me", headers=headers)
            response.raise_for_status()
            return response.json()

    async def get_top_tracks(self, access_token: str, limit: int = 20) -> Dict[str, Any]:
        """
        Obtiene los temas más escuchados por el usuario.
        """
        async with httpx.AsyncClient() as client:
            headers = {"Authorization": f"Bearer {access_token}"}
            params = {"limit": limit, "time_range": "medium_term"}
            response = await client.get(f"{self.api_base_url}/me/top/tracks", headers=headers, params=params)
            response.raise_for_status()
            return response.json()

    async def get_top_artists(self, access_token: str, limit: int = 20) -> Dict[str, Any]:
        """
        Obtiene los artistas más escuchados por el usuario.
        """
        async with httpx.AsyncClient() as client:
            headers = {"Authorization": f"Bearer {access_token}"}
            params = {"limit": limit, "time_range": "medium_term"}
            response = await client.get(f"{self.api_base_url}/me/top/artists", headers=headers, params=params)
            response.raise_for_status()
            return response.json()

    async def get_recently_played(self, access_token: str, limit: int = 20) -> Dict[str, Any]:
        """
        Obtiene los temas recientemente escuchados por el usuario.
        """
        async with httpx.AsyncClient() as client:
            headers = {"Authorization": f"Bearer {access_token}"}
            params = {"limit": limit}
            response = await client.get(f"{self.api_base_url}/me/player/recently-played", headers=headers, params=params)
            response.raise_for_status()
            return response.json()

    async def get_saved_tracks(self, access_token: str, limit: int = 50) -> Dict[str, Any]:
        """
        Obtiene las canciones guardadas en la biblioteca del usuario (Canciones que te gustan / Liked Songs).
        """
        async with httpx.AsyncClient() as client:
            headers = {"Authorization": f"Bearer {access_token}"}
            params = {"limit": limit}
            try:
                response = await client.get(f"{self.api_base_url}/me/tracks", headers=headers, params=params)
                if response.status_code == 200:
                    return response.json()
            except Exception:
                pass
            return {"items": []}

    async def get_artists_genres(self, access_token: str, artist_ids: List[str]) -> Dict[str, List[str]]:
        """
        Obtiene los géneros asociados a una lista de IDs de artistas.
        Spotify limita a un máximo de 50 IDs por petición.
        """
        if not artist_ids:
            return {}
        
        # Filtrar IDs válidos (22 caracteres alfanuméricos)
        valid_ids = [aid for aid in artist_ids if isinstance(aid, str) and len(aid) == 22 and aid.isalnum()]
        invalid_ids = [aid for aid in artist_ids if aid not in valid_ids]
        if invalid_ids:
            import logging
            logging.getLogger(__name__).warning(f"IDs descartados en spotify_client: {invalid_ids}")
            
        # Filtrar duplicados y tomar un máximo de 50
        unique_ids = list(set(valid_ids))[:50]
        if not unique_ids:
            return {}
        
        ids_str = ",".join(unique_ids)
        
        async with httpx.AsyncClient() as client:
            headers = {"Authorization": f"Bearer {access_token}"}
            params = {"ids": ids_str}
            response = await client.get(f"{self.api_base_url}/artists", headers=headers, params=params)
            
            try:
                response.raise_for_status()
            except httpx.HTTPStatusError as e:
                import logging
                logging.getLogger(__name__).error(f"Error 403 de Spotify. Cuerpo: {e.response.text}")
                raise
            
            artists_data = response.json().get("artists", [])
            artist_genres = {}
            for artist in artists_data:
                if artist:
                    artist_genres[artist["id"]] = artist.get("genres", [])
            return artist_genres

    async def search_track(self, access_token: str, track_name: str, artist_name: str) -> str:
        """
        Busca una canción en Spotify y devuelve su URI. Retorna None si no se encuentra.
        Maneja límites de tasa (HTTP 429) de forma automática con reintentos y caché local.
        """
        # Limpieza de clave para buscar en la caché local
        cache_key = f"{track_name.strip().lower()} || {artist_name.strip().lower()}"
        if cache_key in self.search_cache:
            return self.search_cache[cache_key]

        import asyncio
        url = f"{self.api_base_url}/search"
        async with httpx.AsyncClient() as client:
            headers = {"Authorization": f"Bearer {access_token}"}
            query = f"track:{track_name} artist:{artist_name}"
            params = {
                "q": query,
                "type": "track",
                "limit": 1
            }
            
            async def call_with_retry(q_str):
                params["q"] = q_str
                for attempt in range(4):
                    try:
                        resp = await client.get(url, headers=headers, params=params)
                        if resp.status_code == 429:
                            retry_after = int(resp.headers.get("Retry-After", 2))
                            import logging
                            logging.getLogger("uvicorn").warning(f"Límite de tasa de Spotify (429) alcanzado para '{q_str}'. Retry-After: {retry_after}s.")
                            raise SpotifyRateLimitException(retry_after)
                        resp.raise_for_status()
                        return resp
                    except SpotifyRateLimitException as e:
                        raise e
                    except Exception as e:
                        if attempt == 3:
                            raise e
                        await asyncio.sleep(1)
                return None

            try:
                response = await call_with_retry(query)
                if response:
                    tracks = response.json().get("tracks", {}).get("items", [])
                    if tracks:
                        uri = tracks[0]["uri"]
                        self.search_cache[cache_key] = uri
                        self.save_search_cache()
                        return uri
            except SpotifyRateLimitException as rate_err:
                raise rate_err
            except Exception:
                pass
            
            # Búsqueda difusa de respaldo si la exacta falla
            fallback_query = f"{track_name} {artist_name}"
            try:
                response = await call_with_retry(fallback_query)
                if response:
                    tracks = response.json().get("tracks", {}).get("items", [])
                    if tracks:
                        uri = tracks[0]["uri"]
                        self.search_cache[cache_key] = uri
                        self.save_search_cache()
                        return uri
            except SpotifyRateLimitException as rate_err:
                raise rate_err
            except Exception:
                pass
                
            return None

    async def get_or_create_playlist(self, access_token: str, user_id: str, playlist_name: str = "SpodjAI") -> str:
        """
        Busca una playlist por nombre en la cuenta del usuario. Si no existe, la crea.
        Devuelve el ID de la playlist. Recorre todas las páginas de listas del usuario.
        """
        target_name = playlist_name.strip().lower()
        async with httpx.AsyncClient() as client:
            headers = {"Authorization": f"Bearer {access_token}"}
            
            # Recorrer todas las páginas de playlists del usuario
            try:
                url = f"{self.api_base_url}/me/playlists"
                params = {"limit": 50}
                while url:
                    response = await client.get(url, headers=headers, params=params if url.endswith("/me/playlists") else None)
                    if response.status_code == 200:
                        data = response.json()
                        playlists = data.get("items", [])
                        for pl in playlists:
                            if pl and pl.get("name", "").strip().lower() == target_name:
                                import logging
                                logging.getLogger(__name__).info(f"Playlist existente '{playlist_name}' encontrada con ID: {pl.get('id')}")
                                return pl.get("id")
                        url = data.get("next")
                    else:
                        break
            except Exception as e:
                import logging
                logging.getLogger(__name__).warning(f"No se pudieron consultar las playlists existentes: {e}")
            
            # Si no existe en ninguna página, la creamos usando /me/playlists
            create_url = f"{self.api_base_url}/me/playlists"
            payload = {
                "name": playlist_name,
                "description": "Playlist inteligente actualizada dinámicamente por SpodjAI.",
                "public": True
            }
            response = await client.post(create_url, headers=headers, json=payload)
            response.raise_for_status()
            new_id = response.json().get("id")
            import logging
            logging.getLogger(__name__).info(f"Nueva playlist '{playlist_name}' creada con ID: {new_id}")
            return new_id

    async def replace_playlist_tracks(self, access_token: str, playlist_id: str, track_uris: List[str]) -> Dict[str, Any]:
        """
        Vacía la playlist y la reemplaza completamente con la lista de URIs provista,
        manejando bloques de 100 canciones para evitar las limitaciones de tasa de la API de Spotify.
        """
        url = f"{self.api_base_url}/playlists/{playlist_id}/items"
        
        # Si la lista de URIs está vacía, simplemente vaciamos la playlist
        if not track_uris:
            async with httpx.AsyncClient() as client:
                headers = {
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json"
                }
                response = await client.put(url, headers=headers, json={"uris": []})
                response.raise_for_status()
                return response.json()

        # Dividir los URIs en lotes de 100 canciones máximo (límite oficial de Spotify por petición)
        chunks = [track_uris[i:i + 100] for i in range(0, len(track_uris), 100)]
        
        async with httpx.AsyncClient() as client:
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            # El primer lote reemplaza la playlist entera (PUT)
            response = await client.put(url, headers=headers, json={"uris": chunks[0]})
            response.raise_for_status()
            result = response.json()
            
            # Los lotes adicionales se agregan al final (POST)
            for chunk in chunks[1:]:
                response = await client.post(url, headers=headers, json={"uris": chunk})
                response.raise_for_status()
                
            return result

    async def get_playlist_tracks(self, access_token: str, playlist_id: str) -> List[Dict[str, str]]:
        """
        Obtiene los nombres y artistas de las canciones actuales en la playlist.
        """
        async with httpx.AsyncClient() as client:
            headers = {"Authorization": f"Bearer {access_token}"}
            url = f"{self.api_base_url}/playlists/{playlist_id}/items"
            params = {"limit": 100, "fields": "items(track(name,artists(name)))"}
            
            try:
                response = await client.get(url, headers=headers, params=params)
                if response.status_code == 200:
                    tracks = []
                    for item in response.json().get("items", []):
                        track = item.get("track")
                        if track:
                            name = track.get("name")
                            artists = ", ".join([a.get("name") for a in track.get("artists", []) if a.get("name")])
                            if name and artists:
                                tracks.append({"track": name, "artist": artists})
                    return tracks
            except Exception as e:
                import logging
                logging.getLogger(__name__).warning(f"Error al obtener canciones de la playlist: {e}")
            return []
