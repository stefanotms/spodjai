package com.smartaidj.ui

import android.content.Intent
import android.net.Uri
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.smartaidj.network.SmartAiDjClient

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun LoginScreen(viewModel: SmartAiDjViewModel) {
    val context = LocalContext.current
    var ipInput by remember { mutableStateOf(viewModel.backendIp) }

    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(
                Brush.verticalGradient(
                    colors = listOf(
                        Color(0xFF1E1E1E),
                        Color(0xFF121212)
                    )
                )
            )
    ) {
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(32.dp),
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.Center
        ) {
            // Logotipo circular simulado del DJ de IA
            Box(
                modifier = Modifier
                    .size(100.dp)
                    .background(Color(0xFF1DB954), shape = RoundedCornerShape(50.dp)),
                contentAlignment = Alignment.Center
            ) {
                Text(
                    text = "🎧",
                    fontSize = 48.sp
                )
            }

            Spacer(modifier = Modifier.height(24.dp))

            Text(
                text = "SpodjAI",
                fontSize = 32.sp,
                fontWeight = FontWeight.Bold,
                color = Color.White,
                textAlign = TextAlign.Center
            )

            Spacer(modifier = Modifier.height(8.dp))

            Text(
                text = "Tu playlist de Spotify regenerada diariamente por Inteligencia Artificial y adaptada a tu vibra.",
                fontSize = 14.sp,
                color = Color(0xFFB3B3B3),
                textAlign = TextAlign.Center,
                lineHeight = 20.sp
            )

            // Campo editable con la URL del servidor en la nube
            OutlinedTextField(
                value = ipInput,
                onValueChange = {
                    ipInput = it
                    viewModel.updateIpAddress(it)
                },
                label = { Text("URL del Servidor Render", color = Color(0xFF1DB954)) },
                placeholder = { Text("spodjai-backend.onrender.com") },
                singleLine = true,
                shape = RoundedCornerShape(12.dp),
                colors = TextFieldDefaults.outlinedTextFieldColors(
                    focusedBorderColor = Color(0xFF1DB954),
                    unfocusedBorderColor = Color(0xFF404040),
                    focusedTextColor = Color.White,
                    unfocusedTextColor = Color.White
                ),
                modifier = Modifier.fillMaxWidth()
            )

            Spacer(modifier = Modifier.height(24.dp))

            // Botón de Login a la Nube
            Button(
                onClick = {
                    val protocol = when {
                        ipInput.startsWith("http://") || ipInput.startsWith("https://") -> ""
                        else -> "https://"
                    }
                    val loginUrl = "$protocol$ipInput/login?platform=mobile"
                    val intent = Intent(Intent.ACTION_VIEW, Uri.parse(loginUrl))
                    context.startActivity(intent)
                },
                colors = ButtonDefaults.buttonColors(
                    containerColor = Color(0xFF1DB954),
                    contentColor = Color.White
                ),
                shape = RoundedCornerShape(30.dp),
                modifier = Modifier
                    .fillMaxWidth()
                    .height(56.dp)
            ) {
                Text(
                    text = "VINCULAR CON SPOTIFY",
                    fontSize = 16.sp,
                    fontWeight = FontWeight.Bold,
                    letterSpacing = 1.sp
                )
            }
        }
    }
}
