package com.example.moodwave.data

import com.example.moodwave.data.local.AppDatabase
import com.example.moodwave.data.local.CachedRecommendation
import com.example.moodwave.data.local.TrackEntity
import com.example.moodwave.data.network.ApiService
import com.example.moodwave.data.network.ErrorCategory
import com.example.moodwave.data.network.NetworkHandler
import com.example.moodwave.data.network.NetResult
import com.example.moodwave.data.network.dto.IntentDto
import com.example.moodwave.data.network.dto.RecommendItemDto
import com.example.moodwave.data.network.dto.RecommendRequestDto
import com.example.moodwave.data.local.JsonConverters
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.flow

/** Cache is considered stale after 7 days. */
private const val CACHE_TTL_MS = 7L * 24 * 60 * 60 * 1000

/**
 * Single source of truth for recommendation data.
 *
 * Flow diagram for [recommend]:
 *
 *   1. Emit [RecommendationState.Loading].
 *   2. Attempt live network call → POST /v1/recommend.
 *   3a. Success / Degraded → write to Room cache + track rows → emit [Fresh].
 *   3b. Network error + cache exists → emit [Cached] (isStale = savedAt > 7 days ago).
 *   3c. Network error + no cache → emit [Failed].
 */
class RecommendationRepository(
    private val apiService: ApiService,
    private val db: AppDatabase
) {
    private val converters = JsonConverters()

    /**
     * Returns a [queryKey] that uniquely identifies the request in the cache.
     * Format: "<normalised-query>|<mode>" e.g. "chill study|familiar".
     */
    private fun makeQueryKey(query: String, mode: Mode): String =
        "${query.trim().lowercase()}|${mode.apiValue}"

    /**
     * Emits [RecommendationState] events for the given [query] and [mode].
     * Writes successful responses to Room for offline use.
     */
    fun recommend(
        query: String,
        mode: Mode,
        userId: String,
        limit: Int = 10
    ): Flow<RecommendationState> = flow {

        emit(RecommendationState.Loading)

        val queryKey = makeQueryKey(query, mode)

        // ── Network attempt ───────────────────────────────────────────────
        val result = NetworkHandler.safeApiCall {
            apiService.getRecommendations(
                RecommendRequestDto(
                    query = query,
                    mode = mode.apiValue,
                    userId = userId,
                    limit = limit
                )
            )
        }

        when (result) {
            is NetResult.Success -> {
                val response = result.data
                cacheResponse(queryKey, response.items, response.intent)
                persistTracks(response.items)
                emit(
                    RecommendationState.Fresh(
                        items = response.items,
                        intent = response.intent,
                        degraded = false,
                        degradedReason = null
                    )
                )
            }

            is NetResult.Degraded -> {
                val response = result.data
                cacheResponse(queryKey, response.items, response.intent)
                persistTracks(response.items)
                emit(
                    RecommendationState.Fresh(
                        items = response.items,
                        intent = response.intent,
                        degraded = true,
                        degradedReason = result.reason
                    )
                )
            }

            is NetResult.Error -> {
                // Fall back to cache
                val cached = db.cachedRecommendationDao().getByQueryKey(queryKey)
                if (cached != null) {
                    val now = System.currentTimeMillis()
                    val isStale = (now - cached.savedAt) > CACHE_TTL_MS
                    val bannerReason = buildCacheBanner(result.category, isStale)
                    emit(
                        RecommendationState.Cached(
                            items = converters.jsonToItems(cached.itemsJson),
                            intent = converters.jsonToIntent(cached.intentJson),
                            savedAt = cached.savedAt,
                            isStale = isStale,
                            bannerReason = bannerReason
                        )
                    )
                } else {
                    emit(
                        RecommendationState.Failed(
                            category = result.category,
                            message = result.message
                        )
                    )
                }
            }
        }
    }

    // ── Helpers ───────────────────────────────────────────────────────────

    private suspend fun cacheResponse(
        queryKey: String,
        items: List<RecommendItemDto>,
        intent: IntentDto?
    ) {
        db.cachedRecommendationDao().insertOrReplace(
            CachedRecommendation(
                queryKey = queryKey,
                itemsJson = converters.itemsToJson(items),
                intentJson = converters.intentToJson(intent),
                savedAt = System.currentTimeMillis()
            )
        )
    }

    private suspend fun persistTracks(items: List<RecommendItemDto>) {
        val entities = items.map { item ->
            TrackEntity(
                trackId = item.trackId,
                title = item.title,
                artist = item.artist,
                genre = item.genre,
                moodTags = item.moodTags.joinToString("|"),
                explanation = item.explanation,
                semanticId = item.semanticId,
                trackUrl = item.trackUrl.ifBlank { null }
            )
        }
        db.trackDao().insertAll(entities)
    }

    private fun buildCacheBanner(category: ErrorCategory, isStale: Boolean): String {
        val prefix = when (category) {
            ErrorCategory.Offline  -> "Offline"
            ErrorCategory.Timeout  -> "Connection timed out"
            ErrorCategory.RateLimited -> "Rate limited"
            ErrorCategory.ServerDown  -> "Server error"
            else                   -> "Network unavailable"
        }
        return if (isStale) "$prefix — showing cached results (may be outdated)"
        else "$prefix — showing cached results"
    }

    /** Purges cache entries older than 7 days. Call during periodic cleanup. */
    suspend fun evictStaleCache() {
        db.cachedRecommendationDao()
            .deleteOlderThan(System.currentTimeMillis() - CACHE_TTL_MS)
    }
}
