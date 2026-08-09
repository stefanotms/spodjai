package com.smartaidj.ui

import android.content.Intent
import android.net.Uri
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.draw.shadow
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.smartaidj.R
import com.smartaidj.network.SmartAiDjClient

@Composable
fun LoginScreen(viewModel: SmartAiDjViewModel) {
    val context = LocalContext.current

    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(
                Brush.verticalGradient(
                    colors = listOf(
                        Color(0xFF09090B),
                        Color(0xFF141419),
                        Color(0xFF0D0D11)
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
            // Logotipo Oficial SpodjAI generado por IA
            Box(
                modifier = Modifier
                    .size(130.dp)
                    .shadow(
                        elevation = 24.dp,
                        shape = CircleShape,
                        spotColor = Color(0xFF1DB954),
                        ambientColor = Color(0xFF1DB954)
                    )
                    .clip(CircleShape)
                    .border(2.dp, Brush.linearGradient(listOf(Color(0xFF1DB954), Color(0xFF104A23))), CircleShape),
                contentAlignment = Alignment.Center
            ) {
                Image(
                    painter = painterResource(id = R.drawable.ic_spodjai_logo),
                    contentDescription = "SpodjAI Logo",
                    contentScale = ContentScale.Crop,
                    modifier = Modifier.fillMaxSize()
                )
            }

            Spacer(modifier = Modifier.height(32.dp))

            Text(
                text = "SpodjAI",
                fontSize = 36.sp,
                fontWeight = FontWeight.Black,
                color = Color.White,
                letterSpacing = 2.sp,
                textAlign = TextAlign.Center
            )

            Spacer(modifier = Modifier.height(10.dp))

            Text(
                text = "Tu DJ personal con Inteligencia Artificial. Recomendaciones diarias adaptadas exactamente a tu vibra.",
                fontSize = 14.sp,
                color = Color(0xFFA0A0AB),
                textAlign = TextAlign.Center,
                lineHeight = 22.sp,
                modifier = Modifier.padding(horizontal = 8.dp)
            )

            Spacer(modifier = Modifier.height(56.dp))

            // Botón de Acción Principal de Alto Impacto
            Button(
                onClick = {
                    val loginUrl = "${SmartAiDjClient.BASE_URL}/login?platform=mobile"
                    val intent = Intent(Intent.ACTION_VIEW, Uri.parse(loginUrl))
                    context.startActivity(intent)
                },
                colors = ButtonDefaults.buttonColors(
                    containerColor = Color(0xFF1DB954),
                    contentColor = Color.Black
                ),
                shape = RoundedCornerShape(28.dp),
                elevation = ButtonDefaults.buttonElevation(defaultElevation = 8.dp),
                modifier = Modifier
                    .fillMaxWidth()
                    .height(56.dp)
            ) {
                Text(
                    text = "VINCULAR CON SPOTIFY",
                    fontSize = 15.sp,
                    fontWeight = FontWeight.ExtraBold,
                    letterSpacing = 1.5.sp
                )
            }
        }
    }
}
