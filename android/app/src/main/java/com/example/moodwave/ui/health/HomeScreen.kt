package com.example.moodwave.ui.health

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.material3.TopAppBarDefaults
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.moodwave.data.network.dto.HealthDto

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun HomeScreen(
    viewModel: HealthViewModel,
    modifier: Modifier = Modifier
) {
    val uiState by viewModel.uiState.collectAsState()

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Moodwave — Health Check") },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = MaterialTheme.colorScheme.primaryContainer,
                    titleContentColor = MaterialTheme.colorScheme.onPrimaryContainer
                )
            )
        },
        modifier = modifier
    ) { innerPadding ->
        Box(
            modifier = Modifier
                .fillMaxSize()
                .padding(innerPadding)
                .padding(16.dp),
            contentAlignment = Alignment.Center
        ) {
            when (val state = uiState) {
                is HealthUiState.Loading -> {
                    Column(
                        horizontalAlignment = Alignment.CenterHorizontally,
                        verticalArrangement = Arrangement.Center
                    ) {
                        CircularProgressIndicator()
                        Spacer(modifier = Modifier.height(16.dp))
                        Text("Connecting to Moodwave Backend...")
                    }
                }

                is HealthUiState.Ready -> {
                    Column(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalAlignment = Alignment.CenterHorizontally,
                        verticalArrangement = Arrangement.spacedBy(16.dp)
                    ) {
                        if (state.isAmber) {
                            AmberHealthCard(
                                health = state.health,
                                message = state.message ?: "Data catalog not loaded."
                            )
                        } else {
                            GreenHealthCard(health = state.health)
                        }

                        Button(onClick = { viewModel.checkHealth() }) {
                            Text("Retry / Refresh")
                        }
                    }
                }

                is HealthUiState.Error -> {
                    Column(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalAlignment = Alignment.CenterHorizontally,
                        verticalArrangement = Arrangement.spacedBy(16.dp)
                    ) {
                        RedHealthCard(
                            category = state.category.name,
                            message = state.message
                        )

                        Button(onClick = { viewModel.checkHealth() }) {
                            Text("Retry")
                        }
                    }
                }
            }
        }
    }
}

@Composable
fun GreenHealthCard(health: HealthDto) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(
            containerColor = Color(0xFFE8F5E9), // Light Green
            contentColor = Color(0xFF1B5E20)
        )
    ) {
        Column(modifier = Modifier.padding(20.dp)) {
            Text(
                text = "● Backend Healthy & Ready",
                fontWeight = FontWeight.Bold,
                fontSize = 18.sp,
                color = Color(0xFF2E7D32)
            )
            Spacer(modifier = Modifier.height(12.dp))
            HealthAttributeRow(label = "Status", value = health.status)
            HealthAttributeRow(label = "Catalog Data Loaded", value = health.dataLoaded.toString())
            HealthAttributeRow(label = "Catalog Size", value = "${health.catalogSize} tracks")
            HealthAttributeRow(label = "Feedback DB OK", value = health.feedbackDbOk.toString())
            HealthAttributeRow(label = "LLM Configured", value = health.llmConfigured.toString())
        }
    }
}

@Composable
fun AmberHealthCard(health: HealthDto, message: String) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(
            containerColor = Color(0xFFFFF8E1), // Light Amber
            contentColor = Color(0xFFF57F17)
        )
    ) {
        Column(modifier = Modifier.padding(20.dp)) {
            Text(
                text = "▲ Service Partially Available",
                fontWeight = FontWeight.Bold,
                fontSize = 18.sp,
                color = Color(0xFFE65100)
            )
            Spacer(modifier = Modifier.height(8.dp))
            Text(text = message, fontSize = 14.sp)
            Spacer(modifier = Modifier.height(12.dp))
            HealthAttributeRow(label = "Status", value = health.status)
            HealthAttributeRow(label = "Catalog Data Loaded", value = health.dataLoaded.toString())
            HealthAttributeRow(label = "Catalog Size", value = "${health.catalogSize} tracks")
            HealthAttributeRow(label = "Feedback DB OK", value = health.feedbackDbOk.toString())
            HealthAttributeRow(label = "LLM Configured", value = health.llmConfigured.toString())
        }
    }
}

@Composable
fun RedHealthCard(category: String, message: String) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(
            containerColor = Color(0xFFFFEBEE), // Light Red
            contentColor = Color(0xFFB71C1C)
        )
    ) {
        Column(modifier = Modifier.padding(20.dp)) {
            Text(
                text = "✕ Backend Unreachable",
                fontWeight = FontWeight.Bold,
                fontSize = 18.sp,
                color = Color(0xFFC62828)
            )
            Spacer(modifier = Modifier.height(8.dp))
            Text(
                text = "Error Category: $category",
                fontWeight = FontWeight.SemiBold,
                fontSize = 15.sp
            )
            Spacer(modifier = Modifier.height(4.dp))
            Text(text = message, fontSize = 14.sp)
        }
    }
}

@Composable
fun HealthAttributeRow(label: String, value: String) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .padding(vertical = 3.dp),
        horizontalArrangement = Arrangement.SpaceBetween
    ) {
        Text(text = label, fontWeight = FontWeight.Medium, fontSize = 14.sp)
        Text(text = value, fontWeight = FontWeight.Bold, fontSize = 14.sp)
    }
}
