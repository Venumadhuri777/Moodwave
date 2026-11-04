package com.example.moodwave.data.local

import androidx.room.TypeConverter
import com.example.moodwave.data.network.dto.IntentDto
import com.example.moodwave.data.network.dto.RecommendItemDto
import kotlinx.serialization.builtins.ListSerializer
import kotlinx.serialization.json.Json

/**
 * Room TypeConverters for fields that are stored as JSON strings in the database.
 * Uses kotlinx.serialization exclusively — no Gson anywhere in this project.
 *
 * [itemsJson] → List<RecommendItemDto>
 * [intentJson] → IntentDto?
 */
class JsonConverters {

    private val json = Json {
        ignoreUnknownKeys = true
        isLenient = true
        coerceInputValues = true
        encodeDefaults = true
    }

    // ── RecommendItemDto list ──────────────────────────────────────

    @TypeConverter
    fun itemsToJson(items: List<RecommendItemDto>): String =
        json.encodeToString(ListSerializer(RecommendItemDto.serializer()), items)

    @TypeConverter
    fun jsonToItems(value: String): List<RecommendItemDto> =
        json.decodeFromString(ListSerializer(RecommendItemDto.serializer()), value)

    // ── IntentDto (nullable) ───────────────────────────────────────

    /**
     * Stores null intent as the string "null" so the column is never empty.
     */
    @TypeConverter
    fun intentToJson(intent: IntentDto?): String =
        if (intent == null) "null" else json.encodeToString(IntentDto.serializer(), intent)

    @TypeConverter
    fun jsonToIntent(value: String): IntentDto? =
        if (value == "null") null
        else json.decodeFromString(IntentDto.serializer(), value)
}
