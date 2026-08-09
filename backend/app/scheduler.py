import os
import json
import logging
import asyncio
from typing import Dict, Any, Optional
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger("uvicorn")

SCHEDULE_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "user_schedule.json")
scheduler = BackgroundScheduler(timezone="UTC")

def load_schedule_config() -> Dict[str, Any]:
    """Carga la configuración de la tarea programada desde user_schedule.json."""
    if os.path.exists(SCHEDULE_FILE):
        try:
            with open(SCHEDULE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error al leer user_schedule.json: {e}")
    return {
        "enabled": False,
        "hour": 8,
        "minute": 0,
        "limit": 75,
        "discovery_ratio": 0.3,
        "mood": "general",
        "refresh_token": None
    }

def save_schedule_config(config: Dict[str, Any]):
    """Guarda la configuración de la tarea programada en user_schedule.json."""
    try:
        with open(SCHEDULE_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Error al guardar user_schedule.json: {e}")

async def run_scheduled_recommendation_async(config: Dict[str, Any]):
    """
    Ejecuta el proceso completo de recomendación e inyección en Spotify en segundo plano.
    """
    refresh_token = config.get("refresh_token")
    if not refresh_token:
        logger.warning("No hay refresh_token guardado para ejecutar el Auto-Update de SpodjAI.")
        return

    from app.spotify_client import SpotifyClient
    from app.gemini_recommender import generate_recommendations

    spotify_client = SpotifyClient()
    logger.info("⏰ [AUTO-UPDATE] Iniciando actualización automática programada de SpodjAI...")

    try:
        # Refrescar token de acceso
        token_data = await spotify_client.refresh_access_token(refresh_token)
        access_token = token_data.get("access_token")
        if not access_token:
            logger.error("⏰ [AUTO-UPDATE] No se pudo refrescar el access_token de Spotify.")
            return

        # Recuperar perfil y canciones del usuario
        top_data = await spotify_client.get_top_tracks(access_token, limit=50)
        recent_data = await spotify_client.get_recently_played(access_token, limit=50)
        saved_data = await spotify_client.get_saved_tracks(access_token, limit=50)
        top_artists_data = await spotify_client.get_top_artists(access_token, limit=50)

        top_tracks = top_data.get("items", [])
        recent_items = recent_data.get("items", [])
        saved_items = saved_data.get("items", [])
        top_artists = top_artists_data.get("items", [])

        genre_counts = {}
        for artist in top_artists:
            for g in artist.get("genres", []):
                genre_counts[g] = genre_counts.get(g, 0) + 1
        sorted_genres = sorted(genre_counts.items(), key=lambda x: x[1], reverse=True)
        top_genres = [g[0] for g in sorted_genres[:10]]

        user_info = await spotify_client.get_current_user(access_token)
        user_id = user_info["id"]
        playlist_name = "SpodjAI"
        playlist_id = await spotify_client.get_or_create_playlist(access_token, user_id, playlist_name)
        existing_tracks = await spotify_client.get_playlist_tracks(access_token, playlist_id)

        limit = config.get("limit", 75)
        discovery_ratio = config.get("discovery_ratio", 0.3)
        mood = config.get("mood", "general")

        logger.info(f"⏰ [AUTO-UPDATE] Generando {limit} temas (Mood: {mood}, Ratio: {discovery_ratio})...")
        recommendations = await generate_recommendations(
            top_tracks, recent_items, saved_items, top_genres,
            limit=limit, discovery_ratio=discovery_ratio,
            exclude_tracks=existing_tracks, mood=mood
        )

        sem = asyncio.Semaphore(5)
        async def search_and_map(item):
            async with sem:
                t_name = item.get("track")
                a_name = item.get("artist")
                if not t_name or not a_name:
                    return None
                try:
                    uri = await spotify_client.search_track(access_token, t_name, a_name)
                    if uri:
                        return {"uri": uri, "item": item}
                except Exception:
                    pass
                return None

        tasks = [search_and_map(item) for item in recommendations]
        results = await asyncio.gather(*tasks)
        resolved_uris = [r["uri"] for r in results if r]

        if not resolved_uris:
            logger.error("⏰ [AUTO-UPDATE] No se encontraron URIs válidas.")
            return

        import httpx
        try:
            await spotify_client.replace_playlist_tracks(access_token, playlist_id, resolved_uris)
        except httpx.HTTPStatusError as status_err:
            if status_err.response.status_code in [403, 404]:
                async with httpx.AsyncClient() as client:
                    headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
                    create_url = f"{spotify_client.api_base_url}/me/playlists"
                    payload = {"name": playlist_name, "description": "Playlist inteligente por SpodjAI.", "public": True}
                    resp = await client.post(create_url, headers=headers, json=payload)
                    resp.raise_for_status()
                    playlist_id = resp.json().get("id")
                await spotify_client.replace_playlist_tracks(access_token, playlist_id, resolved_uris)
            else:
                raise status_err

        logger.info(f"⏰ [AUTO-UPDATE] ¡Éxito! Playlist {playlist_name} actualizada con {len(resolved_uris)} canciones.")

    except Exception as e:
        logger.error(f"⏰ [AUTO-UPDATE] Error durante la ejecución automática: {e}")

def scheduled_job_wrapper():
    """Wrapper sincrónico para llamar a la función asíncrona desde APScheduler."""
    config = load_schedule_config()
    if config.get("enabled"):
        asyncio.run(run_scheduled_recommendation_async(config))

def update_scheduler_job():
    """Añade o remueve el trabajo programado según user_schedule.json."""
    config = load_schedule_config()
    job_id = "spodjai_daily_update"
    
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)

    if config.get("enabled"):
        hour = config.get("hour", 8)
        minute = config.get("minute", 0)
        trigger = CronTrigger(hour=hour, minute=minute)
        scheduler.add_job(scheduled_job_wrapper, trigger=trigger, id=job_id)
        logger.info(f"⏰ [SCHEDULER] Programación activa: Todos los días a las {hour:02d}:{minute:02d}.")
    else:
        logger.info("⏰ [SCHEDULER] Programación desactivada.")

def start_scheduler():
    """Inicia el motor APScheduler si no está corriendo."""
    if not scheduler.running:
        scheduler.start()
        logger.info("⏰ [SCHEDULER] Motor APScheduler iniciado.")
    update_scheduler_job()
