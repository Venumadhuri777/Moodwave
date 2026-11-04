package com.example.moodwave.ui.health

import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.viewModelScope
import com.example.moodwave.data.network.ApiService
import com.example.moodwave.data.network.ErrorCategory
import com.example.moodwave.data.network.NetResult
import com.example.moodwave.data.network.NetworkHandler
import com.example.moodwave.data.network.dto.HealthDto
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

sealed interface HealthUiState {
    object Loading : HealthUiState

    data class Ready(
        val health: HealthDto,
        val isAmber: Boolean = false,
        val message: String? = null
    ) : HealthUiState

    data class Error(
        val category: ErrorCategory,
        val message: String
    ) : HealthUiState
}

class HealthViewModel(private val apiService: ApiService) : ViewModel() {

    private val _uiState = MutableStateFlow<HealthUiState>(HealthUiState.Loading)
    val uiState: StateFlow<HealthUiState> = _uiState.asStateFlow()

    init {
        checkHealth()
    }

    fun checkHealth() {
        _uiState.value = HealthUiState.Loading
        viewModelScope.launch {
            val result = NetworkHandler.safeApiCall { apiService.getHealth() }
            when (result) {
                is NetResult.Success -> {
                    val health = result.data
                    if (health.status == "ok" && health.dataLoaded) {
                        _uiState.value = HealthUiState.Ready(
                            health = health,
                            isAmber = false,
                            message = "Backend service operational & data loaded."
                        )
                    } else {
                        _uiState.value = HealthUiState.Ready(
                            health = health,
                            isAmber = true,
                            message = "Backend online, but catalog data is not yet loaded."
                        )
                    }
                }
                is NetResult.Degraded -> {
                    _uiState.value = HealthUiState.Ready(
                        health = result.data,
                        isAmber = true,
                        message = result.reason ?: "Backend running in degraded mode."
                    )
                }
                is NetResult.Error -> {
                    _uiState.value = HealthUiState.Error(
                        category = result.category,
                        message = result.message
                    )
                }
            }
        }
    }

    companion object {
        fun provideFactory(apiService: ApiService): ViewModelProvider.Factory =
            object : ViewModelProvider.Factory {
                @Suppress("UNCHECKED_CAST")
                override fun <T : ViewModel> create(modelClass: Class<T>): T {
                    return HealthViewModel(apiService) as T
                }
            }
    }
}
