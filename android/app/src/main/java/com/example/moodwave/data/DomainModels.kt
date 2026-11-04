package com.example.moodwave.data

import com.example.moodwave.data.network.ErrorCategory
import com.example.moodwave.data.network.dto.IntentDto
import com.example.moodwave.data.network.dto.RecommendItemDto

// ─────────────────────────────────────────────────────────────────
// Discovery mode — mirrors the API "mode" field
// ─────────────────────────────────────────────────────────────────

enum class Mode(val apiValue: String) {
    FAMILIAR("familiar"),
    NON_HABITUAL("non_habitual")
}

// ─────────────────────────────────────────────────────────────────
// Feedback action — mirrors valid API "action" values
// ─────────────────────────────────────────────────────────────────

enum class FeedbackAction(val apiValue: String) {
    SKIP("skip"),
    SAVE("save"),
    REPLAY("replay")
}

// ─────────────────────────────────────────────────────────────────
// Recommendation state emitted by RecommendationRepository
// ─────────────────────────────────────────────────────────────────

/**
 * Sealed hierarchy representing every possible outcome of a recommendation
 * request, combining network results and cache state.
 *
 * The UI observes this as a Flow and renders banners / skeletons accordingly.
 */
sealed class RecommendationState {

    /** Network call is in-flight; UI should show a loading skeleton. */
    object Loading : RecommendationState()

    /**
     * Response came from the live backend.
     * [degraded] is true when the backend fell back to the rule parser.
     * [degradedReason] is a human-readable explanation string (never null when degraded).
     */
    data class Fresh(
        val items: List<RecommendItemDto>,
        val intent: IntentDto?,
        val degraded: Boolean,
        val degradedReason: String?
    ) : RecommendationState()

    /**
     * Response came from the local Room cache (network failed or cache still fresh).
     * [savedAt] is the epoch-millis timestamp of the cache entry.
     * [isStale] is true when the cache is older than 7 days.
     * [bannerReason] is shown in the UI (e.g. "Offline — showing cached results").
     */
    data class Cached(
        val items: List<RecommendItemDto>,
        val intent: IntentDto?,
        val savedAt: Long,
        val isStale: Boolean,
        val bannerReason: String? = null
    ) : RecommendationState()

    /**
     * All attempts failed and there is no usable cache.
     * [category] drives retry logic and error icon selection in the UI.
     */
    data class Failed(
        val category: ErrorCategory,
        val message: String
    ) : RecommendationState()
}
