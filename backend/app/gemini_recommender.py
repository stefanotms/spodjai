import json
import logging
from typing import List, Dict, Any, Optional
import google.generativeai as genai
from app.config import settings

logger = logging.getLogger("uvicorn")

def get_mock_recommendations() -> List[Dict[str, str]]:
    """
    Retorna recomendaciones simuladas cuando no se cuenta con una clave de API de Gemini válida.
    """
    return [
        {"artist": "Tame Impala", "track": "The Less I Know the Better", "reason": "Un clásico del indie psicodélico que encaja perfectamente con tus vibras de música alternativa."},
        {"artist": "Daft Punk", "track": "Instant Crush", "reason": "Una mezcla increíble de sintetizadores melódicos y voz con vocoder ideal para un ritmo de DJ dinámico."},
        {"artist": "Gorillaz", "track": "On Melancholy Hill", "reason": "Melodía synth-pop nostálgica y relajante que complementa tus gustos de indie y electrónica."},
        {"artist": "MGMT", "track": "Electric Feel", "reason": "Ritmo funky bailable que aporta energía y dinamismo a tu lista Smart AI DJ."},
        {"artist": "The xx", "track": "Intro", "reason": "Un tema instrumental atmosférico ideal para abrir la sesión de Smart AI DJ con la vibra correcta."},
        {"artist": "Rufus Du Sol", "track": "Innerbloom", "reason": "Viaje progresivo de house melódico que expandirá tus horizontes electrónicos."},
        {"artist": "Kaytranada", "track": "10%", "reason": "Ritmo neo-soul y house bailable con un groove inconfundible para salir de la zona de confort."},
        {"artist": "Disclosure", "track": "Latch", "reason": "Un éxito bailable que combina voces pop con un ritmo garage/house muy contagioso."},
        {"artist": "Glass Animals", "track": "Heat Waves", "reason": "Pop alternativo moderno con un ritmo lento pero envolvente que está muy de moda."},
        {"artist": "Foster The People", "track": "Pumped Up Kicks", "reason": "Indie pop rítmico y clásico para mantener el balance y familiaridad de la playlist."},
        {"artist": "Empire of the Sun", "track": "Walking On A Dream", "reason": "Vibras indie-dance veraniegas y nostálgicas que traen muy buena energía."},
        {"artist": "Phoenix", "track": "1901", "reason": "Indie rock francés enérgico y bailable con guitarras y sintetizadores pegadizos."},
        {"artist": "Jungle", "track": "Keep Moving", "reason": "Modern disco/funk con voces en falsete y un groove irresistible para bailar."},
        {"artist": "FKJ", "track": "Ylang Ylang", "reason": "Una mezcla lo-fi jazz y soul extremadamente relajante para balancear los momentos chill."},
        {"artist": "Bonobo", "track": "Cirrus", "reason": "Electrónica orgánica e instrumental con texturas ricas que te ayudan a concentrarte."}
    ]

async def generate_recommendations(
    top_tracks: List[Dict[str, Any]], 
    recent_tracks: List[Dict[str, Any]], 
    saved_tracks: List[Dict[str, Any]], 
    top_genres: List[str],
    limit: int = 75,
    discovery_ratio: float = 0.3,
    exclude_tracks: Optional[List[Dict[str, str]]] = None,
    mood: str = "general"
) -> List[Dict[str, str]]:
    """
    Envía los datos de reproducción del usuario a Gemini y obtiene recomendaciones personalizadas adaptadas al Mood especificado.
    """
    api_key = settings.gemini_api_key
    
    if not api_key:
        logger.warning("GEMINI_API_KEY no configurada en .env. Usando recomendaciones simuladas (Mock Mode).")
        return get_mock_recommendations()

    try:
        genai.configure(api_key=api_key)
        import random
        
        # 1. Dar formato a las canciones guardadas en biblioteca (Me Gusta) - Mezclado aleatoriamente para romper bucles
        saved_tracks_shuffled = list(saved_tracks[:30])
        random.shuffle(saved_tracks_shuffled)
        
        saved_tracks_lines = []
        for i, item in enumerate(saved_tracks_shuffled, 1):
            track = item.get("track", {})
            artist = ", ".join([a["name"] for a in track.get("artists", [])])
            name = track.get("name")
            saved_tracks_lines.append(f"{i}. {name} - {artist}")
        saved_tracks_text = "\n".join(saved_tracks_lines) if saved_tracks_lines else "No hay suficientes canciones guardadas."

        # 2. Dar formato a los Tops - Mezclado aleatoriamente
        top_tracks_shuffled = list(top_tracks[:50])
        random.shuffle(top_tracks_shuffled)
        
        top_tracks_lines = []
        for i, t in enumerate(top_tracks_shuffled, 1):
            artist = ", ".join([a["name"] for a in t.get("artists", [])])
            name = t.get("name")
            top_tracks_lines.append(f"{i}. {name} - {artist}")
        top_tracks_text = "\n".join(top_tracks_lines) if top_tracks_lines else "No hay suficientes datos de canciones más escuchadas."

        # 3. Formatear géneros
        top_genres_shuffled = list(top_genres)
        random.shuffle(top_genres_shuffled)
        genres_text = ", ".join(top_genres_shuffled) if top_genres_shuffled else "Pop, Rock, Indefinido"

        comfort_pct = int((1.0 - discovery_ratio) * 100)
        discovery_pct = int(discovery_ratio * 100)

        # 4. Formatear la lista de exclusión combinando la playlist actual y el historial de reproducción reciente
        # Esto previene el feedback loop y garantiza variedad absoluta
        exclude_tracks_lines = []
        exclude_set = set()

        if exclude_tracks:
            for t in exclude_tracks:
                track_name = t.get('track', '').strip().lower()
                artist_name = t.get('artist', '').strip().lower()
                exclude_set.add((track_name, artist_name))
                exclude_tracks_lines.append(f"- {t.get('track')} - {t.get('artist')}")

        for play in recent_tracks[:50]:
            track = play.get("track", {})
            name = track.get("name", "").strip().lower()
            artist = ", ".join([a["name"] for a in track.get("artists", [])]).strip().lower()
            if (name, artist) not in exclude_set:
                exclude_set.add((name, artist))
                exclude_tracks_lines.append(f"- {track.get('name')} - {', '.join([a['name'] for a in track.get('artists', [])])}")

        exclude_tracks_text = "\n".join(exclude_tracks_lines) if exclude_tracks_lines else "Ninguna."

        # Definir la regla específica de Mood / Estado de ánimo
        mood_instructions = {
            "gym": "ESTADO DE ÁNIMO / ACTIVIDAD: GIMNASIO Y ENTRENAMIENTO (Workout). Filtra canciones de tempo rápido (BPM elevado), potentes, con mucha energía, motivadoras o pesadas ideales para entrenar con máxima intensidad.",
            "roadtrip": "ESTADO DE ÁNIMO / ACTIVIDAD: VIAJE EN CARRETERA (Road Trip). Filtra canciones épicas, cantables, dinámicas y pegadizas ideales para escuchar en el coche mientras conduces.",
            "chill": "ESTADO DE ÁNIMO / ACTIVIDAD: RELAX Y CONCENTRACIÓN (Chill). Filtra canciones de tempo suave, melodías atmosféricas, acústicas, lo-fi o relajantes ideales para trabajar, estudiar o descansar.",
            "party": "ESTADO DE ÁNIMO / ACTIVIDAD: FIESTA (Party). Filtra canciones sumamente rítmicas, festivas, bailables y llenas de vibra bailable para un ambiente de fiesta.",
            "general": "ESTADO DE ÁNIMO / ACTIVIDAD: GENERAL / BALANCEADO. Selección equilibrada representativa de todos tus gustos principales."
        }
        mood_text = mood_instructions.get(mood.lower(), mood_instructions["general"])

        prompt = f"""
        Eres un DJ de Inteligencia Artificial profesional y un curador de música experto apodado "SpodjAI".
        Tu tarea es analizar el perfil completo del usuario para crear una playlist vibrante y equilibrada de {limit} recomendaciones adaptada a su estado de ánimo deseado.

        AQUÍ ESTÁ EL PERFIL DE GUSTOS REALES Y ESTABLES DEL USUARIO (Mezclado aleatoriamente para mayor variedad):
        ---
        CANCIONES GUARDADAS EN SU BIBLIOTECA (ME GUSTA - ANCLA DE GUSTOS REALES):
        {saved_tracks_text}

        CANCIONES MÁS ESCUCHADAS POR EL USUARIO (TOP):
        {top_tracks_text}

        GÉNEROS PREFERIDOS:
        {genres_text}
        ---

        ESTADO DE ÁNIMO / MOOD SELECCIONADO PARA ESTA SESIÓN:
        >>> {mood_text} <<<

        REGLAS DE RECOMENDACIÓN:
        1. Genera una lista equilibrada de EXACTAMENTE {limit} canciones recomendadas. Es obligatorio que la lista contenga exactamente {limit} elementos en formato JSON, no te detengas antes de alcanzar este número.
        2. Aplica estrictamente una proporción del {comfort_pct}% / {discovery_pct}%:
           - {comfort_pct}% "Zona de Confort y Hits del Momento": Incluye canciones de sus artistas favoritos, temas guardados en su biblioteca o éxitos/temas de moda del momento que encajen perfectamente con su estilo y con el mood seleccionado.
           - {discovery_pct}% "Descubrimiento y Exploración": Canciones frescas de nuevos artistas, joyas ocultas o temas de micro-géneros compatibles que encajen con el mood seleccionado.
        3. Prioriza canciones que coincidan con la vibra del MOOD SELECCIONADO: {mood_text}
        4. EVITA ABSOLUTAMENTE REPETIR las siguientes canciones (tanto las que están en la playlist actual del usuario como las que ha reproducido recientemente en su historial):
        {exclude_tracks_text}
        5. Variedad y secuencia del DJ: Distribuye los artistas a lo largo de la playlist. Evita agrupar canciones del mismo artista de forma consecutiva. No sigas el orden de los datos de entrada del perfil. Queremos una lista con un flujo dinámico, variado y bien mezclado, como en una sesión de DJ real.
        6. Recomienda solo canciones reales de artistas reales.
        7. Devuelve la salida únicamente en formato JSON válido en una lista plana con esta estructura:
        [
          {{
            "artist": "Nombre del artista o banda",
            "track": "Nombre del tema",
            "reason": "Explicación muy breve en español (1 oración) de por qué 'SpodjAI' eligió esta canción según sus gustos y el mood '{mood}'."
          }}
        ]
        """

        # Configurar salida estructurada JSON con soporte para tokens ampliado y temperatura de creatividad asombrosa
        generation_config = {
            "response_mime_type": "application/json",
            "max_output_tokens": 8192,
            "temperature": 1.0
        }

        logger.info("Enviando prompt de recomendación a Gemini API...")
        candidate_models = [
            "models/gemini-3.5-flash-lite",
            "models/gemini-3.1-flash-lite",
            "models/gemini-3.6-flash",
            "models/gemini-2.0-flash-lite",
            "models/gemini-flash-latest"
        ]
        response = None
        last_err = None
        for m_name in candidate_models:
            try:
                m = genai.GenerativeModel(m_name)
                try:
                    response = await m.generate_content_async(prompt, generation_config=generation_config)
                except Exception:
                    response = await m.generate_content_async(prompt, generation_config={"max_output_tokens": 8192, "temperature": 1.0})
                    
                if response and response.text:
                    logger.info(f"Éxito con la IA usando el modelo: {m_name}")
                    break
            except Exception as err:
                last_err = err
                logger.warning(f"No se pudo usar {m_name}: {err}")

        if not response or not response.text:
            raise last_err or Exception("Ningún modelo de IA respondió con éxito.")
        
        # Limpiar y parsear respuesta JSON
        text_response = response.text.strip()
        if text_response.startswith("```"):
            lines = text_response.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            text_response = "\n".join(lines).strip()

        recommendations = json.loads(text_response)
        
        if isinstance(recommendations, list) and len(recommendations) > 0:
            logger.info(f"La IA generó correctamente {len(recommendations)} canciones reales.")
            return recommendations
        else:
            raise ValueError("La respuesta de la IA no es una lista válida de canciones.")

    except Exception as e:
        logger.error(f"Error al llamar a la API de Gemini: {str(e)}. Usando Mock Mode de respaldo.")
        return get_mock_recommendations()
