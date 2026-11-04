package com.example.moodwave

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.viewModels
import com.example.moodwave.ui.health.HomeScreen
import com.example.moodwave.ui.health.HealthViewModel
import com.example.moodwave.ui.theme.MoodwaveTheme

class MainActivity : ComponentActivity() {

    private val healthViewModel: HealthViewModel by viewModels {
        val app = application as MoodwaveApplication
        HealthViewModel.provideFactory(app.container.apiService)
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            MoodwaveTheme {
                HomeScreen(viewModel = healthViewModel)
            }
        }
    }
}
