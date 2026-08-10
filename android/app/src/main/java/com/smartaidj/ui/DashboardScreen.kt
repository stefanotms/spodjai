package com.smartaidj.ui

import android.content.Intent
import android.net.Uri
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.ExitToApp
import androidx.compose.material.icons.filled.PlayArrow
import androidx.compose.material.icons.filled.Refresh
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.smartaidj.R
import com.smartaidj.network.SmartAiDjClient

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun DashboardScreen(
    state: UiState.LoggedIn,
    viewModel: SmartAiDjViewModel
) {
    val context = LocalContext.current

    Scaffold(
        topBar = {
            TopAppBar(
                title = {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Image(
                            painter = painterResource(id = R.drawable.ic_spodjai_logo),
                            contentDescription = null,
                            modifier = Modifier
                                .size(34.dp)
                                .clip(CircleShape)
                                .border(1.dp, Color(0xFF1DB954), CircleShape)
                        )
                        Spacer(modifier = Modifier.width(12.dp))
                        Text("SpodjAI", fontWeight = FontWeight.Black, letterSpacing = 1.sp)
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = Color(0xFF111115),
                    titleContentColor = Color.White,
                    actionIconContentColor = Color.White
                ),
                actions = {
                    IconButton(onClick = { viewModel.logout() }) {
                        Icon(
                            imageVector = Icons.Default.ExitToApp,
                            contentDescription = "Cerrar Sesión",
                            tint = Color(0xFFFF5555)
                        )
                    }
                }
            )
        },
        containerColor = Color(0xFF09090B)
    ) { paddingValues ->
        LazyColumn(
            modifier = Modifier
                .fillMaxSize()
                .padding(paddingValues)
                .padding(horizontal = 20.dp),
            verticalArrangement = Arrangement.spacedBy(0.dp)
        ) {
            item {
                Spacer(modifier = Modifier.height(16.dp))

                // Controles de Configuración
                Card(
                    colors = CardDefaults.cardColors(containerColor = Color(0xFF131316)),
                    shape = RoundedCornerShape(18.dp),
                    modifier = Modifier
                        .fillMaxWidth()
                        .border(1.dp, Color(0xFF222227), RoundedCornerShape(18.dp))
                ) {
                    Column(modifier = Modifier.padding(20.dp)) {
                        Text(
                            text = "CONFIGURACIÓN DEL DJ",
                            fontSize = 12.sp,
                            fontWeight = FontWeight.ExtraBold,
                            letterSpacing = 1.5.sp,
                            color = Color(0xFFA0A0AB)
                        )

                        Spacer(modifier = Modifier.height(20.dp))

                        // Slider de Cantidad de Canciones
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.SpaceBetween
                        ) {
                            Text("Tamaño de Playlist", color = Color(0xFFA0A0AB), fontSize = 14.sp)
                            Text("${viewModel.limit} temas", color = Color(0xFF1DB954), fontWeight = FontWeight.Bold, fontSize = 14.sp)
                        }
                        Spacer(modifier = Modifier.height(4.dp))
                        Slider(
                            value = viewModel.limit.toFloat(),
                            onValueChange = { viewModel.limit = it.toInt() },
                            valueRange = 10f..100f,
                            steps = 9,
                            colors = SliderDefaults.colors(
                                thumbColor = Color(0xFF1DB954),
                                activeTrackColor = Color(0xFF1DB954),
                                inactiveTrackColor = Color(0xFF2A2A32)
                            )
                        )

                        Spacer(modifier = Modifier.height(16.dp))

                        // Slider de Proporción Descubrimiento / Confort
                        val comfortPercent = ((1f - viewModel.discoveryRatio) * 100).toInt()
                        val discoveryPercent = (viewModel.discoveryRatio * 100).toInt()
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.SpaceBetween
                        ) {
                            Text("Balance (Comfort / Descubrir)", color = Color(0xFFA0A0AB), fontSize = 14.sp)
                            Text("$comfortPercent% / $discoveryPercent%", color = Color(0xFF1DB954), fontWeight = FontWeight.Bold, fontSize = 14.sp)
                        }
                        Spacer(modifier = Modifier.height(4.dp))
                        Slider(
                            value = viewModel.discoveryRatio,
                            onValueChange = { viewModel.discoveryRatio = it },
                            valueRange = 0.0f..1.0f,
                            colors = SliderDefaults.colors(
                                thumbColor = Color(0xFF1DB954),
                                activeTrackColor = Color(0xFF1DB954),
                                inactiveTrackColor = Color(0xFF2A2A32)
                            )
                        )

                        Spacer(modifier = Modifier.height(16.dp))

                        // Selector de Mood (Estado de Ánimo)
                        Text("ESTADO DE ÁNIMO (MOOD)", fontSize = 11.sp, fontWeight = FontWeight.Bold, letterSpacing = 1.sp, color = Color(0xFFA0A0AB))
                        Spacer(modifier = Modifier.height(10.dp))

                        val moods = listOf(
                            "general" to "General",
                            "gym" to "Gym",
                            "roadtrip" to "Road",
                            "chill" to "Chill",
                            "party" to "Fiesta"
                        )

                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.spacedBy(8.dp)
                        ) {
                            moods.forEach { (key, label) ->
                                val isSelected = viewModel.selectedMood == key
                                Surface(
                                    onClick = { viewModel.selectedMood = key },
                                    shape = RoundedCornerShape(24.dp),
                                    color = if (isSelected) Color(0xFF1DB954) else Color(0xFF1F1F24),
                                    contentColor = if (isSelected) Color.Black else Color(0xFFA0A0AB),
                                    modifier = Modifier
                                        .weight(1f)
                                        .border(
                                            width = 1.dp,
                                            color = if (isSelected) Color(0xFF1DB954) else Color(0xFF2D2D34),
                                            shape = RoundedCornerShape(24.dp)
                                        )
                                ) {
                                    Box(
                                        contentAlignment = Alignment.Center,
                                        modifier = Modifier.padding(vertical = 8.dp)
                                    ) {
                                        Text(
                                            text = label,
                                            fontSize = 11.sp,
                                            fontWeight = if (isSelected) FontWeight.ExtraBold else FontWeight.Normal,
                                            maxLines = 1
                                        )
                                    }
                                }
                            }
                        }
                    }
                }
            }

            item {
                Spacer(modifier = Modifier.height(12.dp))

                // Tarjeta de Programación Automática (Cron Job Diario)
                Card(
                    colors = CardDefaults.cardColors(containerColor = Color(0xFF131316)),
                    shape = RoundedCornerShape(18.dp),
                    modifier = Modifier
                        .fillMaxWidth()
                        .border(1.dp, Color(0xFF222227), RoundedCornerShape(18.dp))
                ) {
                    Column(modifier = Modifier.padding(20.dp)) {
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.SpaceBetween,
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Column(modifier = Modifier.weight(1f)) {
                                Text(
                                    text = "AUTO-UPDATE DIARIO",
                                    fontSize = 12.sp,
                                    fontWeight = FontWeight.Bold,
                                    letterSpacing = 1.sp,
                                    color = Color.White
                                )
                                Spacer(modifier = Modifier.height(2.dp))
                                Text(
                                    text = if (viewModel.scheduleEnabled) 
                                        "Actualización programada a las ${viewModel.scheduleHour.toString().padStart(2, '0')}:00 hs" 
                                        else "Desactivado",
                                    fontSize = 12.sp,
                                    color = Color(0xFFA0A0AB)
                                )
                            }

                            Switch(
                                checked = viewModel.scheduleEnabled,
                                onCheckedChange = { isChecked ->
                                    viewModel.updateSchedule(isChecked, viewModel.scheduleHour, viewModel.scheduleMinute)
                                },
                                colors = SwitchDefaults.colors(
                                    checkedThumbColor = Color.Black,
                                    checkedTrackColor = Color(0xFF1DB954),
                                    uncheckedThumbColor = Color(0xFFA0A0AB),
                                    uncheckedTrackColor = Color(0xFF1F1F24)
                                )
                            )
                        }

                        if (viewModel.scheduleEnabled) {
                            Spacer(modifier = Modifier.height(16.dp))
                            Row(
                                modifier = Modifier.fillMaxWidth(),
                                horizontalArrangement = Arrangement.SpaceBetween,
                                verticalAlignment = Alignment.CenterVertically
                            ) {
                                Text("Hora de ejecución:", color = Color(0xFFA0A0AB), fontSize = 14.sp)
                                Row(verticalAlignment = Alignment.CenterVertically) {
                                    OutlinedButton(
                                        onClick = {
                                            val newHour = if (viewModel.scheduleHour > 0) viewModel.scheduleHour - 1 else 23
                                            viewModel.updateSchedule(true, newHour, 0)
                                        },
                                        contentPadding = PaddingValues(horizontal = 12.dp, vertical = 4.dp),
                                        shape = RoundedCornerShape(12.dp),
                                        colors = ButtonDefaults.outlinedButtonColors(contentColor = Color.White)
                                    ) {
                                        Text("-", fontSize = 18.sp, fontWeight = FontWeight.Bold)
                                    }

                                    Spacer(modifier = Modifier.width(12.dp))
                                    Text(
                                        text = "${viewModel.scheduleHour.toString().padStart(2, '0')}:00",
                                        fontSize = 16.sp,
                                        fontWeight = FontWeight.Black,
                                        color = Color(0xFF1DB954)
                                    )
                                    Spacer(modifier = Modifier.width(12.dp))

                                    OutlinedButton(
                                        onClick = {
                                            val newHour = if (viewModel.scheduleHour < 23) viewModel.scheduleHour + 1 else 0
                                            viewModel.updateSchedule(true, newHour, 0)
                                        },
                                        contentPadding = PaddingValues(horizontal = 12.dp, vertical = 4.dp),
                                        shape = RoundedCornerShape(12.dp),
                                        colors = ButtonDefaults.outlinedButtonColors(contentColor = Color.White)
                                    ) {
                                        Text("+", fontSize = 18.sp, fontWeight = FontWeight.Bold)
                                    }
                                }
                            }
                        }
                    }
                }
            }

            item {
                Spacer(modifier = Modifier.height(20.dp))

                // Botón de Acción Principal
                Button(
                    onClick = { viewModel.generatePlaylist() },
                    colors = ButtonDefaults.buttonColors(
                        containerColor = Color(0xFF1DB954),
                        contentColor = Color.Black
                    ),
                    shape = RoundedCornerShape(26.dp),
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(52.dp)
                ) {
                    Icon(Icons.Default.Refresh, contentDescription = null)
                    Spacer(modifier = Modifier.width(8.dp))
                    Text("REGENERAR PLAYLIST", fontWeight = FontWeight.ExtraBold, letterSpacing = 1.sp)
                }
            }

            item {
                // Botón para abrir en Spotify si está disponible
                if (!state.playlistUrl.isNullOrEmpty()) {
                    Spacer(modifier = Modifier.height(10.dp))
                    OutlinedButton(
                        onClick = {
                            val intent = Intent(Intent.ACTION_VIEW, Uri.parse(state.playlistUrl))
                            context.startActivity(intent)
                        },
                        colors = ButtonDefaults.outlinedButtonColors(contentColor = Color(0xFF1DB954)),
                        border = BorderStroke(1.5.dp, Color(0xFF1DB954)),
                        shape = RoundedCornerShape(26.dp),
                        modifier = Modifier
                            .fillMaxWidth()
                            .height(52.dp)
                    ) {
                        Icon(Icons.Default.PlayArrow, contentDescription = null, tint = Color(0xFF1DB954))
                        Spacer(modifier = Modifier.width(8.dp))
                        Text("ABRIR EN SPOTIFY", fontWeight = FontWeight.ExtraBold, letterSpacing = 1.sp)
                    }
                }
            }

            item {
                Spacer(modifier = Modifier.height(28.dp))

                // Listado de Canciones
                Text(
                    text = "Recomendaciones Generadas (${state.songs.size})",
                    fontSize = 18.sp,
                    fontWeight = FontWeight.ExtraBold,
                    color = Color.White,
                    letterSpacing = 0.5.sp
                )

                Spacer(modifier = Modifier.height(12.dp))
            }

            if (state.songs.isEmpty()) {
                item {
                    Box(
                        modifier = Modifier
                            .fillMaxWidth()
                            .height(150.dp),
                        contentAlignment = Alignment.Center
                    ) {
                        Text(
                            text = "No hay canciones generadas todavía.\nPresiona 'Regenerar Playlist' arriba.",
                            color = Color(0xFFA0A0AB),
                            lineHeight = 22.sp,
                            textAlign = TextAlign.Center
                        )
                    }
                }
            } else {
                items(state.songs) { song ->
                    SongItemCard(song)
                    Spacer(modifier = Modifier.height(10.dp))
                }
            }

            item {
                Spacer(modifier = Modifier.height(24.dp))
            }
        }
    }
}

@Composable
fun SongItemCard(song: SmartAiDjClient.Recommendation) {
    Card(
        colors = CardDefaults.cardColors(containerColor = Color(0xFF131316)),
        shape = RoundedCornerShape(16.dp),
        modifier = Modifier
            .fillMaxWidth()
            .border(1.dp, Color(0xFF222227), RoundedCornerShape(16.dp))
    ) {
        Row(modifier = Modifier.fillMaxWidth()) {
            // Línea neón lateral indicando que es curada por SpodjAI
            Box(
                modifier = Modifier
                    .width(4.dp)
                    .height(80.dp)
                    .background(Color(0xFF1DB954))
            )
            
            Column(modifier = Modifier.padding(14.dp)) {
                Text(
                    text = song.track,
                    fontSize = 15.sp,
                    fontWeight = FontWeight.ExtraBold,
                    color = Color.White,
                    maxLines = 1,
                    overflow = TextOverflow.Ellipsis
                )
                Spacer(modifier = Modifier.height(2.dp))
                Text(
                    text = song.artist,
                    fontSize = 13.sp,
                    color = Color(0xFF1DB954),
                    fontWeight = FontWeight.Bold,
                    maxLines = 1,
                    overflow = TextOverflow.Ellipsis
                )
                
                if (song.reason.isNotEmpty()) {
                    Spacer(modifier = Modifier.height(6.dp))
                    Text(
                        text = song.reason,
                        fontSize = 12.sp,
                        color = Color(0xFFA0A0AB),
                        lineHeight = 16.sp
                    )
                }
            }
        }
    }
}
