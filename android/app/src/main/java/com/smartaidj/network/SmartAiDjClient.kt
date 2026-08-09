package com.smartaidj.network

import android.util.Log
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import org.json.JSONArray
import org.json.JSONObject
import java.io.BufferedReader
import java.io.InputStreamReader
import java.io.OutputStreamWriter
import java.net.HttpURLConnection
import java.net.URL
import java.net.URLEncoder

object SmartAiDjClient {
    // URL del servidor backend en la nube (Render.com 24/7)
    var BASE_URL = "https://spodjai.onrender.com"

    private const val TAG = "SmartAiDjClient"

    init {
        trustAllCertificates()
    }

    private fun trustAllCertificates() {
        try {
            val trustAllCerts = arrayOf<javax.net.ssl.TrustManager>(object : javax.net.ssl.X509TrustManager {
                override fun getAcceptedIssuers(): Array<java.security.cert.X509Certificate> = arrayOf()
                override fun checkClientTrusted(certs: Array<java.security.cert.X509Certificate>, authType: String) {}
                override fun checkServerTrusted(certs: Array<java.security.cert.X509Certificate>, authType: String) {}
            })

            val sc = javax.net.ssl.SSLContext.getInstance("SSL")
            sc.init(null, trustAllCerts, java.security.SecureRandom())
            javax.net.ssl.HttpsURLConnection.setDefaultSSLSocketFactory(sc.socketFactory)
            javax.net.ssl.HttpsURLConnection.setDefaultHostnameVerifier { _, _ -> true }
        } catch (e: Exception) {
            Log.e(TAG, "Error setting up SSL trust all", e)
        }
    }

    data class ScheduleConfig(
        val enabled: Boolean,
        val hour: Int,
        val minute: Int,
        val limit: Int,
        val discoveryRatio: Float,
        val mood: String
    )

    data class RefreshResponse(
        val accessToken: String?,
        val refreshToken: String?,
        val expiresIn: Int?
    )

    data class Recommendation(
        val artist: String,
        val track: String,
        val reason: String
    )

    data class RecommendationResult(
        val playlistId: String,
        val playlistUrl: String,
        val recommendations: List<Recommendation>
    )

    /**
     * Hace una petición GET al backend para refrescar el token de Spotify.
     */
    suspend fun refreshTokens(refreshToken: String): RefreshResponse = withContext(Dispatchers.IO) {
        val urlStr = "$BASE_URL/refresh?refresh_token=${URLEncoder.encode(refreshToken, "UTF-8")}"
        Log.d(TAG, "Refrescando tokens: $urlStr")
        try {
            val url = URL(urlStr)
            val conn = url.openConnection() as HttpURLConnection
            conn.requestMethod = "GET"
            conn.connectTimeout = 10000
            conn.readTimeout = 10000

            val code = conn.responseCode
            if (code == 200) {
                val reader = BufferedReader(InputStreamReader(conn.inputStream))
                val response = StringBuilder()
                var line: String?
                while (reader.readLine().also { line = it } != null) {
                    response.append(line)
                }
                reader.close()

                val json = JSONObject(response.toString())
                RefreshResponse(
                    accessToken = json.optString("access_token", null),
                    refreshToken = json.optString("refresh_token", null),
                    expiresIn = json.optInt("expires_in", 3600)
                )
            } else {
                Log.e(TAG, "Error al refrescar tokens: Código $code")
                RefreshResponse(null, null, null)
            }
        } catch (e: Exception) {
            Log.e(TAG, "Error de red al refrescar tokens: ${e.message}", e)
            RefreshResponse(null, null, null)
        }
    }

    /**
     * Envía la solicitud al endpoint POST /api/recommend para regenerar la playlist.
     */
    suspend fun generateRecommendations(
        accessToken: String,
        limit: Int,
        discoveryRatio: Float,
        mood: String = "general",
        refreshToken: String? = null
    ): RecommendationResult? = withContext(Dispatchers.IO) {
        var urlStr = "$BASE_URL/api/recommend?limit=$limit&discovery_ratio=$discoveryRatio&mood=${URLEncoder.encode(mood, "UTF-8")}"
        if (!refreshToken.isNullOrEmpty()) {
            urlStr += "&refresh_token=${URLEncoder.encode(refreshToken, "UTF-8")}"
        }
        Log.d(TAG, "Solicitando recomendaciones: $urlStr")
        try {
            val url = URL(urlStr)
            val conn = url.openConnection() as HttpURLConnection
            conn.requestMethod = "POST"
            conn.setRequestProperty("Authorization", "Bearer $accessToken")
            conn.setRequestProperty("Content-Type", "application/json")
            conn.connectTimeout = 90000 // 90 segundos para dar tiempo a Gemini y búsquedas en Spotify
            conn.readTimeout = 90000
            conn.doOutput = true

            // Enviar un body vacío
            val writer = OutputStreamWriter(conn.outputStream)
            writer.write("{}")
            writer.flush()
            writer.close()

            val code = conn.responseCode
            if (code == 200) {
                val reader = BufferedReader(InputStreamReader(conn.inputStream))
                val response = StringBuilder()
                var line: String?
                while (reader.readLine().also { line = it } != null) {
                    response.append(line)
                }
                reader.close()

                val json = JSONObject(response.toString())
                val playlistId = json.getString("playlist_id")
                val playlistUrl = json.getString("playlist_url")
                val recsArray = json.getJSONArray("recommendations")
                
                val recsList = mutableListOf<Recommendation>()
                for (i in 0 until recsArray.length()) {
                    val item = recsArray.getJSONObject(i)
                    recsList.add(
                        Recommendation(
                            artist = item.optString("artist", "Desconocido"),
                            track = item.optString("track", "Desconocido"),
                            reason = item.optString("reason", "")
                        )
                    )
                }
                RecommendationResult(playlistId, playlistUrl, recsList)
            } else {
                Log.e(TAG, "Error al generar recomendaciones: Código $code")
                null
            }
        } catch (e: Exception) {
            Log.e(TAG, "Error de red al generar recomendaciones: ${e.message}", e)
            null
        }
    }

    suspend fun getScheduleConfig(): ScheduleConfig? = withContext(Dispatchers.IO) {
        val urlStr = "$BASE_URL/api/schedule"
        try {
            val url = URL(urlStr)
            val conn = url.openConnection() as HttpURLConnection
            conn.requestMethod = "GET"
            conn.connectTimeout = 10000
            conn.readTimeout = 10000
            if (conn.responseCode == 200) {
                val reader = BufferedReader(InputStreamReader(conn.inputStream))
                val response = StringBuilder()
                var line: String?
                while (reader.readLine().also { line = it } != null) {
                    response.append(line)
                }
                reader.close()

                val json = JSONObject(response.toString())
                ScheduleConfig(
                    enabled = json.optBoolean("enabled", false),
                    hour = json.optInt("hour", 8),
                    minute = json.optInt("minute", 0),
                    limit = json.optInt("limit", 75),
                    discoveryRatio = json.optDouble("discovery_ratio", 0.3).toFloat(),
                    mood = json.optString("mood", "general")
                )
            } else null
        } catch (e: Exception) {
            Log.e(TAG, "Error al obtener configuración de horario: ${e.message}", e)
            null
        }
    }

    suspend fun saveScheduleConfig(
        enabled: Boolean,
        hour: Int,
        minute: Int,
        limit: Int,
        discoveryRatio: Float,
        mood: String,
        refreshToken: String? = null
    ): Boolean = withContext(Dispatchers.IO) {
        val urlStr = "$BASE_URL/api/schedule"
        try {
            val url = URL(urlStr)
            val conn = url.openConnection() as HttpURLConnection
            conn.requestMethod = "POST"
            conn.setRequestProperty("Content-Type", "application/json")
            conn.connectTimeout = 10000
            conn.readTimeout = 10000
            conn.doOutput = true

            val body = JSONObject().apply {
                put("enabled", enabled)
                put("hour", hour)
                put("minute", minute)
                put("limit", limit)
                put("discovery_ratio", discoveryRatio.toDouble())
                put("mood", mood)
                if (!refreshToken.isNullOrEmpty()) {
                    put("refresh_token", refreshToken)
                }
            }

            val writer = OutputStreamWriter(conn.outputStream)
            writer.write(body.toString())
            writer.flush()
            writer.close()

            conn.responseCode == 200
        } catch (e: Exception) {
            Log.e(TAG, "Error al guardar configuración de horario: ${e.message}", e)
            false
        }
    }
}
