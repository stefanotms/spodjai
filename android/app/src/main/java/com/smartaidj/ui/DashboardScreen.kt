package com.smartaidj.ui

import android.content.Intent
import android.net.Uri
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
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(paddingValues)
                .padding(horizontal = 20.dp)
        ) {
            Spacer(modifier = Modifier.height(16.dp))

            // Controles de Configuración
            Card(
                colors = CardDefaults.cardColors(containerColor = Color(0xFF1E1E1E)),
                shape = RoundedCornerShape(16.dp),
                modifier = Modifier.fillMaxWidth()
            ) {
                Column(modifier = Modifier.padding(16.dp)) {
                    Text(
                        text = "Configuración del DJ",
                        fontSize = 18.sp,
                        fontWeight = FontWeight.Bold,
                        color = Color.White
                    )

                    Spacer(modifier = Modifier.height(16.dp))

                    // Slider de Cantidad de Canciones
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween
                    ) {
                        Text("Tamaño de Playlist", color = Color(0xFFB3B3B3))
                        Text("${viewModel.limit} temas", color = Color(0xFF1DB954), fontWeight = FontWeight.Bold)
                    }
                    Slider(
                        value = viewModel.limit.toFloat(),
                        onValueChange = { viewModel.limit = it.toInt() },
                        valueRange = 10f..100f,
                        steps = 9,
                        colors = SliderDefaults.colors(
                            thumbColor = Color(0xFF1DB954),
                            activeTrackColor = Color(0xFF1DB954),
                            inactiveTrackColor = Color(0xFF404040)
                        )
                    )

                    Spacer(modifier = Modifier.height(12.dp))

                    // Slider de Proporción Descubrimiento / Confort
                    val comfortPercent = ((1f - viewModel.discoveryRatio) * 100).toInt()
                    val discoveryPercent = (viewModel.discoveryRatio * 100).toInt()
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween
                    ) {
                        Text("Balance (Comfort / Descubrir)", color = Color(0xFFB3B3B3))
                        Text("$comfortPercent% / $discoveryPercent%", color = Color(0xFF1DB954), fontWeight = FontWeight.Bold)
                    }
                    Slider(
                        value = viewModel.discoveryRatio,
                        onValueChange = { viewModel.discoveryRatio = it },
                        valueRange = 0.0f..1.0f,
                        colors = SliderDefaults.colors(
                            thumbColor = Color(0xFF1DB954),
                            activeTrackColor = Color(0xFF1DB954),
                            inactiveTrackColor = Color(0xFF404040)
                        )
                    )

                    Spacer(modifier = Modifier.height(12.dp))

                    // Selector de Mood (Estado de Ánimo)
                    Text("Estado de Ánimo (Mood)", color = Color(0xFFB3B3B3))
                    Spacer(modifier = Modifier.height(8.dp))

                    val moods = listOf(
                        "general" to "⚡ General",
                        "gym" to "🏋️‍♂️ Gym",
                        "roadtrip" to "🚗 Road Trip",
                        "chill" to "🌙 Chill",
                        "party" to "🎉 Fiesta"
                    )

                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.spacedBy(8.dp)
                    ) {
                        moods.forEach { (key, label) ->
                            val isSelected = viewModel.selectedMood == key
                            Surface(
                                onClick = { viewModel.selectedMood = key },
                                shape = RoundedCornerShape(20.dp),
                                color = if (isSelected) Color(0xFF1DB954) else Color(0xFF2A2A2A),
                                contentColor = if (isSelected) Color.White else Color(0xFFB3B3B3),
                                modifier = Modifier.weight(1f)
                            ) {
                                Box(
                                    contentAlignment = Alignment.Center,
                                    modifier = Modifier.padding(vertical = 8.dp)
                                ) {
                                    Text(
                                        text = label,
                                        fontSize = 11.sp,
                                        fontWeight = if (isSelected) FontWeight.Bold else FontWeight.Normal,
                                        maxLines = 1
                                    )
                                }
                            }
                        }
                    }
                }
            }

            Spacer(modifier = Modifier.height(12.dp))

            // Tarjeta de Programación Automática (Cron Job Diario)
            Card(
                colors = CardDefaults.cardColors(containerColor = Color(0xFF1E1E1E)),
                shape = RoundedCornerShape(16.dp),
                modifier = Modifier.fillMaxWidth()
            ) {
                Column(modifier = Modifier.padding(16.dp)) {
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Column(modifier = Modifier.weight(1f)) {
                            Text(
                                text = "⏰ Auto-Update Diario",
                                fontSize = 16.sp,
                                fontWeight = FontWeight.Bold,
                                color = Color.White
                            )
                            Text(
                                text = if (viewModel.scheduleEnabled) 
                                    "Actualización programada a las ${viewModel.scheduleHour.toString().padStart(2, '0')}:00 hs" 
                                    else "Desactivado",
                                fontSize = 12.sp,
                                color = Color(0xFFB3B3B3)
                            )
                        }

                        Switch(
                            checked = viewModel.scheduleEnabled,
                            onCheckedChange = { isChecked ->
                                viewModel.updateSchedule(isChecked, viewModel.scheduleHour, viewModel.scheduleMinute)
                            },
                            colors = SwitchDefaults.colors(
                                checkedThumbColor = Color.White,
                                checkedTrackColor = Color(0xFF1DB954)
                            )
                        )
                    }

                    if (viewModel.scheduleEnabled) {
                        Spacer(modifier = Modifier.height(12.dp))
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.SpaceBetween,
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Text("Hora de ejecución:", color = Color(0xFFB3B3B3), fontSize = 14.sp)
                            Row(verticalAlignment = Alignment.CenterVertically) {
                                OutlinedButton(
                                    onClick = {
                                        val newHour = if (viewModel.scheduleHour > 0) viewModel.scheduleHour - 1 else 23
                                        viewModel.updateSchedule(true, newHour, 0)
                                    },
                                    contentPadding = PaddingValues(horizontal = 12.dp, vertical = 4.dp),
                                    shape = RoundedCornerShape(12.dp)
                                ) {
                                    Text("-", fontSize = 18.sp, color = Color.White)
                                }

                                Spacer(modifier = Modifier.width(8.dp))
                                Text(
                                    text = "${viewModel.scheduleHour.toString().padStart(2, '0')}:00",
                                    fontSize = 16.sp,
                                    fontWeight = FontWeight.Bold,
                                    color = Color(0xFF1DB954)
                                )
                                Spacer(modifier = Modifier.width(8.dp))

                                OutlinedButton(
                                    onClick = {
                                        val newHour = if (viewModel.scheduleHour < 23) viewModel.scheduleHour + 1 else 0
                                        viewModel.updateSchedule(true, newHour, 0)
                                    },
                                    contentPadding = PaddingValues(horizontal = 12.dp, vertical = 4.dp),
                                    shape = RoundedCornerShape(12.dp)
                                ) {
                                    Text("+", fontSize = 18.sp, color = Color.White)
                                }
                            }
                        }
                    }
                }
            }

            Spacer(modifier = Modifier.height(16.dp))

            // Botón de Acción Principal
            Button(
                onClick = { viewModel.generatePlaylist() },
                colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF1DB954)),
                shape = RoundedCornerShape(30.dp),
                modifier = Modifier
                    .fillMaxWidth()
                    .height(50.dp)
            ) {
                Icon(Icons.Default.Refresh, contentDescription = null)
                Spacer(modifier = Modifier.width(8.dp))
                Text("REGENERAR PLAYLIST INTELIGENTE", fontWeight = FontWeight.Bold)
            }

            Spacer(modifier = Modifier.height(12.dp))

            // Botón para abrir en Spotify si está disponible
            if (!state.playlistUrl.isNullOrEmpty()) {
                OutlinedButton(
                    onClick = {
                        val intent = Intent(Intent.ACTION_VIEW, Uri.parse(state.playlistUrl))
                        context.startActivity(intent)
                    },
                    colors = ButtonDefaults.outlinedButtonColors(contentColor = Color(0xFF1DB954)),
                    border = ButtonDefaults.outlinedButtonBorder.copy(width = 2.dp),
                    shape = RoundedCornerShape(30.dp),
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(50.dp)
                ) {
                    Icon(Icons.Default.PlayArrow, contentDescription = null, tint = Color(0xFF1DB954))
                    Spacer(modifier = Modifier.width(8.dp))
                    Text("ABRIR EN SPOTIFY", fontWeight = FontWeight.Bold)
                }
            }

            Spacer(modifier = Modifier.height(24.dp))

            // Listado de Canciones
            Text(
                text = "Recomendaciones Generadas (${state.songs.size})",
                fontSize = 18.sp,
                fontWeight = FontWeight.Bold,
                color = Color.White
            )

            Spacer(modifier = Modifier.height(12.dp))

            if (state.songs.isEmpty()) {
                Box(
                    modifier = Modifier
                        .fillMaxWidth()
                        .weight(1f),
                    contentAlignment = Alignment.Center
                ) {
                    Text(
                        text = "No hay canciones generadas todavía.\nPresiona 'Regenerar Playlist' arriba.",
                        color = Color(0xFFB3B3B3),
                        lineHeight = 22.sp
                    )
                }
            } else {
                LazyColumn(
                    modifier = Modifier.weight(1f),
                    verticalArrangement = Arrangement.spacedBy(10.dp)
                ) {
                    items(state.songs) { song ->
                        SongItemCard(song)
                    }
                }
            }
        }
    }
}

@Composable
fun SongItemCard(song: SmartAiDjClient.Recommendation) {
    Card(
        colors = CardDefaults.cardColors(containerColor = Color(0xFF1E1E1E)),
        shape = RoundedCornerShape(12.dp),
        modifier = Modifier.fillMaxWidth()
    ) {
        Column(modifier = Modifier.padding(14.dp)) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Column(modifier = Modifier.weight(1f)) {
                    Text(
                        text = song.track,
                        fontSize = 16.sp,
                        fontWeight = FontWeight.Bold,
                        color = Color.White,
                        maxLines = 1,
                        overflow = TextOverflow.Ellipsis
                    )
                    Text(
                        text = song.artist,
                        fontSize = 13.sp,
                        color = Color(0xFF1DB954),
                        maxLines = 1,
                        overflow = TextOverflow.Ellipsis
                    )
                }
            }
            if (song.reason.isNotEmpty()) {
                Spacer(modifier = Modifier.height(8.dp))
                Text(
                    text = song.reason,
                    fontSize = 12.sp,
                    color = Color(0xFFB3B3B3),
                    lineHeight = 16.sp
                )
            }
        }
    }
}
