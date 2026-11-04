package com.example.moodwave.data.network.dto

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
data class CatalogItemDto(
    @SerialName("track_id") val trackId: String = "",
    @SerialName("title") val title: String = "",
    @SerialName("artist") val artist: String = "",
    @SerialName("album") val album: String? = null,
    @SerialName("genre") val genre: String = "",
    @SerialName("mood_tags") val moodTags: List<String> = emptyList(),
    @SerialName("semantic_id") val semanticId: String = "",
    @SerialName("duration_seconds") val durationSeconds: Int? = null,
    @SerialName("track_url") val trackUrl: String = "",
    @SerialName("license") val license: String? = "CC BY-NC-SA 4.0"
)
