package com.example.moodwave.data.network.dto

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
data class FeedbackRequestDto(
    @SerialName("user_id") val userId: String = "",
    @SerialName("track_id") val trackId: String = "",
    @SerialName("action") val action: String = "save"
)

@Serializable
data class FeedbackResponseDto(
    @SerialName("status") val status: String = "",
    @SerialName("user_id") val userId: String = "",
    @SerialName("track_id") val trackId: String = "",
    @SerialName("action") val action: String = "",
    @SerialName("timestamp") val timestamp: String = ""
)
