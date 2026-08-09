package com.smartaidj

import android.content.Intent
import android.net.Uri
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.viewModels
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.smartaidj.ui.DashboardScreen
import com.smartaidj.ui.LoginScreen
import com.smartaidj.ui.SmartAiDjViewModel
import com.smartaidj.ui.UiState

class MainActivity : ComponentActivity() {

    private val viewModel: SmartAiDjViewModel by viewModels()

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        
        // Manejar el token que viene desde el Deep Link al abrir por primera vez
        handleIntent(intent)

        setContent {
            MaterialTheme {
                Surface(
                    modifier = Modifier.fillMaxSize(),
                    color = Color(0xFF121212)
                ) {
                    AppContent(viewModel = viewModel)
                }
            }
        }
    }

    override fun onNewIntent(intent: Intent) {
        super.onNewIntent(intent)
        // Manejar el token si la app ya estaba abierta en segundo plano
        handleIntent(intent)
    }

    private fun handleIntent(intent: Intent?) {
        val data: Uri? = intent?.data
        if (data != null && data.scheme == "spodjai" && data.host == "auth") {
            val refreshToken = data.getQueryParameter("refresh_token")
            val accessToken = data.getQueryParameter("access_token")
            if (refreshToken != null && accessToken != null) {
                viewModel.handleAuthCallback(refreshToken, accessToken)
            }
        }
    }
}

@Composable
fun AppContent(viewModel: SmartAiDjViewModel) {
    when (val state = viewModel.uiState) {
        is UiState.Welcome -> {
            LoginScreen(viewModel = viewModel)
        }
        is UiState.Loading -> {
            LoadingScreen()
        }
        is UiState.LoggedIn -> {
            DashboardScreen(state = state, viewModel = viewModel)
        }
        is UiState.Error -> {
            ErrorScreen(message = state.message, onRetry = { viewModel.logout() })
        }
    }
}

@Composable
fun LoadingScreen() {
    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(Color(0xFF121212)),
        contentAlignment = Alignment.Center
    ) {
        Column(horizontalAlignment = Alignment.CenterHorizontally) {
            CircularProgressIndicator(color = Color(0xFF1DB954))
            Spacer(modifier = Modifier.height(16.dp))
            Text("Procesando con la IA de Gemini...", color = Color.White, fontSize = 16.sp)
        }
    }
}

@Composable
fun ErrorScreen(message: String, onRetry: () -> Unit) {
    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(Color(0xFF121212))
            .padding(32.dp),
        contentAlignment = Alignment.Center
    ) {
        Column(
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.Center
        ) {
            Text(
                text = "⚠️",
                fontSize = 48.sp
            )
            Spacer(modifier = Modifier.height(16.dp))
            Text(
                text = "Ups, algo salió mal",
                fontSize = 20.sp,
                fontWeight = FontWeight.Bold,
                color = Color.White
            )
            Spacer(modifier = Modifier.height(8.dp))
            Text(
                text = message,
                fontSize = 14.sp,
                color = Color(0xFFB3B3B3),
                modifier = Modifier.padding(horizontal = 16.dp)
            )
            Spacer(modifier = Modifier.height(32.dp))
            Button(
                onClick = onRetry,
                colors = ButtonDefaults.buttonColors(containerColor = Color(0xFFFF5555))
            ) {
                Text("Volver", fontWeight = FontWeight.Bold)
            }
        }
    }
}
