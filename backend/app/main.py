import traceback
import logging
import asyncio
import httpx
from typing import List, Dict, Any, Optional
from urllib.parse import quote, unquote
from fastapi import FastAPI, HTTPException, Query, Header, Request
from fastapi.responses import RedirectResponse, HTMLResponse
from pydantic import BaseModel

from app.spotify_client import SpotifyClient, SpotifyRateLimitException
from app.config import settings
from app.gemini_recommender import generate_recommendations
from app.scheduler import start_scheduler, load_schedule_config, save_schedule_config, update_scheduler_job, run_scheduled_recommendation_async

# Configurar logs para depuración en consola
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("uvicorn")

app = FastAPI(
    title="SpodjAI Backend",
    description="Servidor backend para manejar autenticación y sincronización con Spotify y Gemini API",
    version="0.2.0"
)

@app.on_event("startup")
def on_startup():
    try:
        start_scheduler()
    except Exception as e:
        logger.error(f"Error al iniciar el scheduler en arranque: {e}")

spotify_client = SpotifyClient()

class RecommendationResponse(BaseModel):
    playlist_id: str
    playlist_url: str
    tracks_added: int
    recommendations: List[Dict[str, str]]

class ScheduleRequest(BaseModel):
    enabled: bool
    hour: int = 8
    minute: int = 0
    limit: int = 75
    discovery_ratio: float = 0.3
    mood: str = "general"
    refresh_token: Optional[str] = None

@app.get("/")
def read_root():
    return {
        "message": "Servidor backend de SpodjAI funcionando correctamente.",
        "docs_url": "/docs",
        "login_url": "/login"
    }

@app.get("/login")
def login(request: Request, platform: Optional[str] = Query(None)):
    """
    Redirige al usuario al inicio de sesión de Spotify.
    """
    if (settings.spotify_client_id == "PON_AQUI_TU_CLIENT_ID" or 
        settings.spotify_client_secret == "PON_AQUI_TU_CLIENT_SECRET"):
        raise HTTPException(
            status_code=400,
            detail="Credenciales no configuradas. Por favor, edita el archivo backend/.env con tu SPOTIFY_CLIENT_ID y SPOTIFY_CLIENT_SECRET."
        )
    
    # Extraer el Host de la petición (ej. 192.168.0.28:8000 o 127.0.0.1:8000)
    host = request.headers.get("host", "127.0.0.1:8000")
    protocol = "https" if request.url.scheme == "https" else "http"
    custom_redirect_uri = f"{protocol}://{host}/callback/spotify"
    
    state_parts = []
    if platform:
        state_parts.append(f"platform={platform}")
    state_parts.append(f"ruri={quote(custom_redirect_uri)}")
    state = "&".join(state_parts)

    auth_url = spotify_client.get_authorization_url(state=state, redirect_uri=custom_redirect_uri)
    return RedirectResponse(auth_url)

# Manejar ambas rutas para evitar problemas de compatibilidad de configuración
@app.get("/callback", response_class=HTMLResponse)
@app.get("/callback/spotify", response_class=HTMLResponse)
async def callback(code: str = Query(None), error: str = Query(None), state: str = Query(None)):
    """
    Recibe el código de autorización temporal de Spotify y lo intercambia por tokens de acceso.
    Soporta rutas /callback y /callback/spotify.
    """
    if error:
        return f"""
        <html>
            <head>
                <title>Error de Autenticación - SpodjAI</title>
                <style>
                    body {{ font-family: 'Segoe UI', Arial, sans-serif; background-color: #121212; color: #FF5555; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }}
                    .card {{ background-color: #181818; padding: 40px; border-radius: 12px; box-shadow: 0 8px 24px rgba(0,0,0,0.6); max-width: 500px; width: 100%; border: 1px solid #FF5555; text-align: center; }}
                    h1 {{ margin-top: 0; }}
                    .btn {{ display: inline-block; background-color: #FF5555; color: white; padding: 12px 24px; border-radius: 25px; text-decoration: none; font-weight: bold; margin-top: 20px; transition: background-color 0.2s; }}
                    .btn:hover {{ background-color: #ff3333; }}
                </style>
            </head>
            <body>
                <div class="card">
                    <h1>Error de Spotify</h1>
                    <p>Spotify devolvió un error durante la autenticación: <strong>{error}</strong></p>
                    <a href="/login" class="btn">Intentar de nuevo</a>
                </div>
            </body>
        </html>
        """
    
    if not code:
        raise HTTPException(status_code=400, detail="Código de autorización no proporcionado.")

    try:
        # Extraer ruri de state si fue pasado
        custom_redirect_uri = None
        if state and "ruri=" in state:
            for part in state.split("&"):
                if part.startswith("ruri="):
                    custom_redirect_uri = unquote(part.split("ruri=")[1])

        # Intercambio de código por tokens usando el redirect_uri dinámico
        tokens = await spotify_client.get_tokens(code, redirect_uri=custom_redirect_uri)
        access_token = tokens.get("access_token")
        refresh_token = tokens.get("refresh_token")
        expires_in = tokens.get("expires_in")
        
        # Validar tokens obteniendo el perfil de usuario
        user_info = await spotify_client.get_current_user(access_token)
        user_name = user_info.get("display_name", "Usuario de Spotify")
        user_id = user_info.get("id")

        # Si el login vino desde Android (detectado en el parámetro 'state'), redirigimos por Deep Link
        if state and "platform=mobile" in state:
            return RedirectResponse(f"spodjai://auth?refresh_token={refresh_token}&access_token={access_token}")

        # HTML con estilo premium "Spotify Dark"
        return HTMLResponse(content=f"""
        <html>
            <head>
                <title>¡Conexión Exitosa! - SpodjAI</title>
                <style>
                    body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #121212; color: #FFFFFF; display: flex; justify-content: center; align-items: center; min-height: 100vh; margin: 0; padding: 20px; box-sizing: border-box; }}
                    .card {{ background-color: #181818; padding: 40px; border-radius: 16px; box-shadow: 0 10px 30px rgba(0,0,0,0.7); max-width: 650px; width: 100%; border: 1px solid #282828; }}
                    h1 {{ color: #1DB954; margin-top: 0; font-size: 28px; font-weight: 700; }}
                    p {{ color: #b3b3b3; line-height: 1.6; font-size: 15px; }}
                    .token-section {{ margin-top: 25px; }}
                    .token-title {{ font-weight: bold; color: #1DB954; margin-bottom: 5px; font-size: 14px; text-transform: uppercase; letter-spacing: 1px; }}
                    .token-val {{ word-break: break-all; font-family: 'Courier New', Courier, monospace; background-color: #0b0b0b; padding: 12px; border-radius: 8px; display: block; border: 1px solid #282828; color: #e5e5e5; font-size: 13px; max-height: 100px; overflow-y: auto; }}
                    .btn {{ display: inline-block; background-color: #1DB954; color: white; padding: 12px 28px; border-radius: 25px; text-decoration: none; font-weight: bold; margin-top: 30px; text-align: center; transition: background-color 0.2s, transform 0.2s; }}
                    .btn:hover {{ background-color: #1ed760; transform: scale(1.02); }}
                    .success-badge {{ display: inline-block; background-color: rgba(29, 185, 84, 0.1); color: #1DB954; padding: 6px 12px; border-radius: 20px; font-weight: bold; font-size: 12px; margin-bottom: 15px; }}
                </style>
            </head>
            <body>
                <div class="card">
                    <div class="success-badge">✓ AUTENTICACIÓN COMPLETADA</div>
                    <h1>¡Conectado con Spotify!</h1>
                    <p>Hola, <strong>{user_name}</strong> (Spotify ID: <code>{user_id}</code>). El backend ha guardado y validado tus credenciales.</p>
                    
                    <div class="token-section">
                        <div class="token-title">Access Token (Expira en {expires_in}s):</div>
                        <div class="token-val">{access_token}</div>
                    </div>
                    
                    <div class="token-section">
                        <div class="token-title">Refresh Token:</div>
                        <div class="token-val">{refresh_token}</div>
                    </div>
                    
                    <p style="font-size: 12px; color: #777; margin-top: 25px;">
                        Guarda este <strong>Refresh Token</strong> para usarlo en la app de Android o llama al endpoint de generación de recomendaciones.
                    </p>
                    <a href="/" class="btn">Volver al Inicio</a>
                </div>
            </body>
        </html>
        """)
    except Exception as e:
        error_details = traceback.format_exc()
        return f"""
        <html>
            <head>
                <title>Error de Autenticación - SpodjAI</title>
                <style>
                    body {{ font-family: 'Segoe UI', Arial, sans-serif; background-color: #121212; color: #FFFFFF; padding: 30px; }}
                    .container {{ max-width: 800px; margin: 0 auto; background-color: #181818; padding: 30px; border-radius: 12px; border: 1px solid #FF5555; }}
                    h1 {{ color: #FF5555; margin-top: 0; }}
                    pre {{ background-color: #0b0b0b; padding: 15px; border-radius: 8px; color: #FF5555; overflow-x: auto; font-family: monospace; border: 1px solid #282828; }}
                    .btn {{ display: inline-block; background-color: #1DB954; color: white; padding: 10px 20px; border-radius: 20px; text-decoration: none; font-weight: bold; margin-top: 20px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>Error al procesar la respuesta de Spotify</h1>
                    <p>Ocurrió un error inesperado al intentar intercambiar el código por tokens:</p>
                    <p><strong>Detalle:</strong> {str(e)}</p>
                    <h3>Seguimiento del Error (Stacktrace):</h3>
                    <pre>{error_details}</pre>
                    <a href="/login" class="btn">Reintentar Conexión</a>
                </div>
            </body>
        </html>
        """

@app.get("/refresh")
async def refresh(refresh_token: str):
    """
    Ruta para que la aplicación cliente refresque su token a través del backend.
    """
    if not refresh_token:
        raise HTTPException(status_code=400, detail="El parámetro refresh_token es obligatorio.")
    try:
        tokens = await spotify_client.refresh_access_token(refresh_token)
        return tokens
    except Exception as e:
        raise HTTPException(
            status_code=400, 
            detail=f"Error al refrescar el token de acceso con Spotify: {str(e)}"
        )

@app.get("/api/schedule")
def get_schedule():
    """Devuelve la configuración actual de la tarea programada."""
    return load_schedule_config()

@app.post("/api/schedule")
def set_schedule(req: ScheduleRequest):
    """Guarda la nueva configuración de la tarea programada y actualiza el motor APScheduler."""
    config = load_schedule_config()
    config["enabled"] = req.enabled
    config["hour"] = req.hour
    config["minute"] = req.minute
    config["limit"] = req.limit
    config["discovery_ratio"] = req.discovery_ratio
    config["mood"] = req.mood
    if req.refresh_token:
        config["refresh_token"] = req.refresh_token
    save_schedule_config(config)
    update_scheduler_job()
    return {"status": "success", "config": config}

@app.get("/api/schedule/trigger")
async def trigger_schedule_manual():
    """
    Endpoint para disparar manualmente la actualización programada en segundo plano
    (útil para crones externos como cron-job.org que despiertan el servidor de Render).
    """
    config = load_schedule_config()
    if not config.get("enabled"):
        return {"status": "ignored", "reason": "La programación automática no está habilitada en user_schedule.json"}
    
    # Disparar en segundo plano para responder rápido a la petición HTTP y evitar timeout
    asyncio.create_task(run_scheduled_recommendation_async(config))
    return {"status": "triggered", "message": "Actualización programada iniciada en segundo plano con éxito"}

@app.post("/api/recommend", response_model=RecommendationResponse)
async def recommend(
    limit: int = Query(75, ge=1, le=100),
    discovery_ratio: float = Query(0.3, ge=0.0, le=1.0),
    mood: str = Query("general"),
    refresh_token: Optional[str] = Query(None),
    authorization: Optional[str] = Header(None),
    access_token: Optional[str] = Query(None)
):
    """
    Endpoint principal del Smart AI DJ.
    """
    # Si recibimos el refresh_token, lo guardamos para permitir ejecuciones automáticas futuras
    if refresh_token:
        config = load_schedule_config()
        config["refresh_token"] = refresh_token
        save_schedule_config(config)

    # Extraer token de autorización (Soporta Header 'Authorization: Bearer <token>' o query param)
    token = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1]
    elif access_token:
        token = access_token
        
    if not token:
        raise HTTPException(
            status_code=401,
            detail="Falta el token de acceso de Spotify. Proporciónalo en el Header 'Authorization: Bearer <token>' o mediante el parámetro de consulta 'access_token'."
        )

    try:
        logger.info("1. Obteniendo datos de Spotify del usuario...")
        # Obtener Top Tracks, Recientes y Canciones Guardadas (Me Gusta)
        top_data = await spotify_client.get_top_tracks(token, limit=50)
        recent_data = await spotify_client.get_recently_played(token, limit=50)
        saved_data = await spotify_client.get_saved_tracks(token, limit=50)
        
        top_tracks = top_data.get("items", [])
        recent_items = recent_data.get("items", [])
        saved_items = saved_data.get("items", [])
        
        logger.info("2. Recuperando géneros musicales de los artistas top...")
        top_artists_data = await spotify_client.get_top_artists(token, limit=50)
        top_artists = top_artists_data.get("items", [])
        
        genre_counts = {}
        for artist in top_artists:
            for g in artist.get("genres", []):
                genre_counts[g] = genre_counts.get(g, 0) + 1
                
        sorted_genres = sorted(genre_counts.items(), key=lambda x: x[1], reverse=True)
        top_genres = [g[0] for g in sorted_genres[:10]]

        logger.info(f"Géneros consolidados: {top_genres}")

        logger.info("3. Obteniendo datos del perfil y playlist actual para exclusión...")
        user_info = await spotify_client.get_current_user(token)
        user_id = user_info["id"]
        playlist_name = "SpodjAI"
        playlist_id = await spotify_client.get_or_create_playlist(token, user_id, playlist_name)
        
        existing_tracks = await spotify_client.get_playlist_tracks(token, playlist_id)
        logger.info(f"Canciones encontradas en la playlist actual para excluir: {len(existing_tracks)}")

        logger.info(f"4. Generando recomendaciones con la IA (Mood: {mood})...")
        recommendations = await generate_recommendations(
            top_tracks, recent_items, saved_items, top_genres,
            limit=limit, discovery_ratio=discovery_ratio,
            exclude_tracks=existing_tracks, mood=mood
        )

        logger.info("5. Buscando los URIs de Spotify para las recomendaciones generadas...")
        resolved_uris = []
        valid_recommendations = []
        
        # Limitar la concurrencia a 2 peticiones simultáneas para evitar ser bloqueados por el API de Spotify
        sem = asyncio.Semaphore(2)
        rate_limit_encountered = False

        async def search_and_map(item):
            nonlocal rate_limit_encountered
            if rate_limit_encountered:
                return None
            async with sem:
                track_name = item.get("track")
                artist_name = item.get("artist")
                if not track_name or not artist_name:
                    return None
                try:
                    # Espaciar levemente el inicio de cada búsqueda para no saturar
                    await asyncio.sleep(0.15)
                    uri = await spotify_client.search_track(token, track_name, artist_name)
                    if uri:
                        return {"uri": uri, "item": item}
                except SpotifyRateLimitException as rate_err:
                    logger.error(f"Se ha alcanzado un límite de tasa (429) de Spotify: {rate_err}. Deteniendo búsquedas restantes...")
                    rate_limit_encountered = True
                except Exception as e:
                    logger.warning(f"Error al buscar {track_name} - {artist_name}: {e}")
                return None

        # Crear y ejecutar tareas de forma espaciada
        tasks = []
        for i, item in enumerate(recommendations):
            # Retrasar el encolado inicial de cada tarea de forma progresiva
            async def spaced_task(itm, delay):
                await asyncio.sleep(delay)
                return await search_and_map(itm)
            tasks.append(spaced_task(item, i * 0.1))

        search_results = await asyncio.gather(*tasks)

        resolved_uris = []
        valid_recommendations = []
        for res in search_results:
            if res:
                resolved_uris.append(res["uri"])
                valid_recommendations.append(res["item"])
                logger.info(f"Encontrada: {res['item'].get('track')} - {res['item'].get('artist')} -> {res['uri']}")

        if not resolved_uris:
            raise HTTPException(
                status_code=429 if rate_limit_encountered else 404,
                detail="Spotify está limitando las peticiones (Límite 429) o no se encontró ninguna canción." if rate_limit_encountered else "No se pudo encontrar ninguna de las canciones recomendadas por la IA en la búsqueda de Spotify."
            )

        # Inyectar las canciones, manejando recuperación automática si la playlist se eliminó de Spotify (403/404)
        try:
            await spotify_client.replace_playlist_tracks(token, playlist_id, resolved_uris)
        except httpx.HTTPStatusError as status_err:
            if status_err.response.status_code in [403, 404]:
                logger.warning(f"La playlist con ID {playlist_id} no es escribible (403/404). Creando una playlist nueva...")
                # Forzar la creación de una nueva playlist puenteando la búsqueda
                async with httpx.AsyncClient() as client:
                    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
                    create_url = f"{spotify_client.api_base_url}/me/playlists"
                    payload = {
                        "name": playlist_name,
                        "description": "Playlist inteligente actualizada dinámicamente por SpodjAI.",
                        "public": True
                    }
                    response = await client.post(create_url, headers=headers, json=payload)
                    response.raise_for_status()
                    playlist_id = response.json().get("id")
                
                # Intentar inyectar las canciones en la nueva playlist
                await spotify_client.replace_playlist_tracks(token, playlist_id, resolved_uris)
            else:
                raise status_err

        logger.info(f"Playlist {playlist_name} actualizada con éxito con {len(resolved_uris)} canciones.")

        # Intentar subir el logotipo como portada personalizada de la playlist
        import os
        cover_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "playlist_cover.jpg")
        await spotify_client.set_playlist_cover_from_file(token, playlist_id, cover_path)

        playlist_url = f"https://open.spotify.com/playlist/{playlist_id}"

        return RecommendationResponse(
            playlist_id=playlist_id,
            playlist_url=playlist_url,
            tracks_added=len(resolved_uris),
            recommendations=valid_recommendations
        )

    except Exception as e:
        logger.error(f"Error durante el proceso de recomendación: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail=f"Ocurrió un error en el servidor de SpodjAI: {str(e)}"
        )
