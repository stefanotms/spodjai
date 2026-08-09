package com.smartaidj.ui

import android.app.Application
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.smartaidj.data.TokenManager
import com.smartaidj.network.SmartAiDjClient
import kotlinx.coroutines.launch

sealed interface UiState {
    object Welcome : UiState
    object Loading : UiState
    data class LoggedIn(
        val playlistId: String? = null,
        val playlistUrl: String? = null,
        val songs: List<SmartAiDjClient.Recommendation> = emptyList()
    ) : UiState
    data class Error(val message: String) : UiState
}

class SmartAiDjViewModel(application: Application) : AndroidViewModel(application) {
    private val tokenManager = TokenManager(application)

    // Estados reactivos de Compose
    var uiState by mutableStateOf<UiState>(UiState.Welcome)
        private set

    var limit by mutableStateOf(75)
    var discoveryRatio by mutableStateOf(0.3f)
    var selectedMood by mutableStateOf("general")
    var scheduleEnabled by mutableStateOf(false)
    var scheduleHour by mutableStateOf(8)
    var scheduleMinute by mutableStateOf(0)
    var backendIp by mutableStateOf("spodjai-backend.onrender.com")

    init {
        // Establecer URL en la nube por defecto
        updateIpAddress("spodjai-backend.onrender.com")
        
        // Al arrancar, verificamos si ya existe una sesión guardada
        val savedRefreshToken = tokenManager.getRefreshToken()
        if (savedRefreshToken != null) {
            refreshAndLogin(savedRefreshToken)
        }
    }

    fun updateIpAddress(newIp: String) {
        backendIp = newIp
        val protocol = when {
            newIp.startsWith("http://") || newIp.startsWith("https://") -> ""
            newIp.startsWith("10.0.2.2") || newIp.startsWith("127.0.0.1") || newIp.startsWith("localhost") -> "http://"
            else -> "https://"
        }
        SmartAiDjClient.BASE_URL = "$protocol$newIp"
    }

    /**
     * Guarda el refresh token obtenido del Deep Link e inicia sesión.
     */
    fun handleAuthCallback(refreshToken: String, accessToken: String) {
        tokenManager.saveRefreshToken(refreshToken)
        tokenManager.saveAccessToken(accessToken)
        uiState = UiState.LoggedIn(playlistId = null, playlistUrl = null, songs = emptyList())
        loadSchedule()
    }

    private fun loadSchedule() {
        viewModelScope.launch {
            val config = SmartAiDjClient.getScheduleConfig()
            if (config != null) {
                scheduleEnabled = config.enabled
                scheduleHour = config.hour
                scheduleMinute = config.minute
                if (config.mood.isNotEmpty()) {
                    selectedMood = config.mood
                }
            }
        }
    }

    fun updateSchedule(enabled: Boolean, hour: Int, minute: Int) {
        scheduleEnabled = enabled
        scheduleHour = hour
        scheduleMinute = minute
        val refreshToken = tokenManager.getRefreshToken()
        viewModelScope.launch {
            SmartAiDjClient.saveScheduleConfig(
                enabled = enabled,
                hour = hour,
                minute = minute,
                limit = limit,
                discoveryRatio = discoveryRatio,
                mood = selectedMood,
                refreshToken = refreshToken
            )
        }
    }

    /**
     * Refresca el access token utilizando el refresh token guardado.
     */
    private fun refreshAndLogin(refreshToken: String) {
        uiState = UiState.Loading
        viewModelScope.launch {
            val response = SmartAiDjClient.refreshTokens(refreshToken)
            if (response.accessToken != null) {
                tokenManager.saveAccessToken(response.accessToken)
                if (response.refreshToken != null) {
                    tokenManager.saveRefreshToken(response.refreshToken)
                }
                uiState = UiState.LoggedIn()
                loadSchedule()
            } else {
                uiState = UiState.Error("No se pudo conectar con Spotify. Por favor, inicia sesión de nuevo.")
                tokenManager.clearTokens()
            }
        }
    }

    /**
     * Solicita al backend generar las canciones recomendadas según el Mood seleccionado.
     */
    fun generatePlaylist() {
        val refreshToken = tokenManager.getRefreshToken() ?: return
        val currentAccessToken = tokenManager.getAccessToken()

        uiState = UiState.Loading
        viewModelScope.launch {
            var tokenToUse = currentAccessToken
            
            // 1. Intentar refrescar el token de acceso para garantizar que no esté caducado
            val refreshResponse = SmartAiDjClient.refreshTokens(refreshToken)
            if (refreshResponse.accessToken != null) {
                tokenToUse = refreshResponse.accessToken
                tokenManager.saveAccessToken(refreshResponse.accessToken)
            }

            if (tokenToUse == null) {
                uiState = UiState.Error("Sesión expirada. Por favor, reautentícate.")
                return@launch
            }

            // 2. Solicitar las recomendaciones al backend
            val result = SmartAiDjClient.generateRecommendations(
                accessToken = tokenToUse,
                limit = limit,
                discoveryRatio = discoveryRatio,
                mood = selectedMood,
                refreshToken = refreshToken
            )
            if (result != null) {
                uiState = UiState.LoggedIn(
                    playlistId = result.playlistId,
                    playlistUrl = result.playlistUrl,
                    songs = result.recommendations
                )
            } else {
                uiState = UiState.Error("Error al generar las recomendaciones. Revisa que tu backend esté encendido.")
            }
        }
    }

    /**
     * Cierra la sesión borrando los tokens guardados.
     */
    fun logout() {
        tokenManager.clearTokens()
        uiState = UiState.Welcome
    }
}
