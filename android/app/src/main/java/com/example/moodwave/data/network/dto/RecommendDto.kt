package com.example.moodwave.data.network.dto

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
data class RecommendRequestDto(
    @SerialName("query") val query: String = "",
    @SerialName("mode") val mode: String = "familiar",
    @SerialName("user_id") val userId: String = "",
    @SerialName("limit") val limit: Int = 10
)

@Serializable
data class IntentDto(
    @SerialName("moods") val moods: List<String> = emptyList(),
    @SerialName("genres") val genres: List<String> = emptyList(),
    @SerialName("avoid_genres") val avoidGenres: List<String> = emptyList(),
    @SerialName("context") val context: String? = null,
    @SerialName("confidence") val confidence: Float = 1.0f
)

@Serializable
data class RecommendItemDto(
    @SerialName("track_id") val trackId: String = "",
    @SerialName("title") val title: String = "",
    @SerialName("artist") val artist: String = "",
    @SerialName("genre") val genre: String = "",
    @SerialName("mood_tags") val moodTags: List<String> = emptyList(),
    @SerialName("explanation") val explanation: String = "",
    @SerialName("semantic_id") val semanticId: String = "",
    @SerialName("track_url") val trackUrl: String = ""
)

@Serializable
data class RecommendResponseDto(
    @SerialName("intent") val intent: IntentDto? = null,
    @SerialName("source") val source: String = "rules",
    @SerialName("items") val items: List<RecommendItemDto> = emptyList(),
    @SerialName("degraded") val degraded: Boolean = false,
    @SerialName("degraded_reason") val degradedReason: String? = null
)
