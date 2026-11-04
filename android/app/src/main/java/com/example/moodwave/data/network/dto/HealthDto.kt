package com.example.moodwave.data.network.dto

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
data class HealthDto(
    @SerialName("status") val status: String = "",
    @SerialName("data_loaded") val dataLoaded: Boolean = false,
    @SerialName("feedback_db_ok") val feedbackDbOk: Boolean = false,
    @SerialName("llm_configured") val llmConfigured: Boolean = false,
    @SerialName("catalog_size") val catalogSize: Int = 0
)
