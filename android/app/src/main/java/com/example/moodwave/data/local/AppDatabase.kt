package com.example.moodwave.data.local

import android.content.Context
import androidx.room.ColumnInfo
import androidx.room.Dao
import androidx.room.Database
import androidx.room.Delete
import androidx.room.Entity
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.PrimaryKey
import androidx.room.Query
import androidx.room.Room
import androidx.room.RoomDatabase
import androidx.room.Transaction
import androidx.room.TypeConverters
import kotlinx.coroutines.flow.Flow

// ─────────────────────────────────────────────────────────────────
// Entities
// ─────────────────────────────────────────────────────────────────

/**
 * Caches a full recommendation response keyed by a normalised query string
 * (lowercase-trimmed query + mode, e.g. "chill study|familiar").
 * [savedAt] is epoch-millis; the repository uses it to detect 7-day staleness.
 */
@Entity(tableName = "cached_recommendations")
data class CachedRecommendation(
    @PrimaryKey val queryKey: String,
    val itemsJson: String,   // JSON array of RecommendItemDto
    val intentJson: String,  // JSON object of IntentDto (or "{}" when null)
    val savedAt: Long        // epoch millis
)

/**
 * Stores any track that has been shown to the user or saved.
 * [moodTags] is stored as a pipe-separated string (e.g. "calm|relaxing|study").
 * [trackUrl] is nullable — older cached entries may arrive without it.
 */
@Entity(tableName = "tracks")
data class TrackEntity(
    @PrimaryKey val trackId: String,
    val title: String,
    val artist: String,
    val genre: String,
    @ColumnInfo(name = "mood_tags") val moodTags: String, // pipe-separated
    val explanation: String,
    val semanticId: String,
    val trackUrl: String?
)

/**
 * Offline feedback queue.
 * Rows are inserted immediately (synced = false) and flipped to synced = true
 * after a successful POST /v1/feedback.
 * Rows with [attempts] >= 10 are permanently skipped but never deleted — they
 * form an audit trail and must not be silently lost.
 */
@Entity(tableName = "feedback")
data class FeedbackEntity(
    @PrimaryKey(autoGenerate = true) val id: Int = 0,
    val userId: String,
    val trackId: String,
    val action: String,       // "skip" | "save" | "replay"
    val createdAt: Long,      // epoch millis
    val synced: Boolean = false,
    val attempts: Int = 0
)

/**
 * Tracks explicitly saved by the user via the Save action.
 * [savedAt] epoch millis; used to order the Saved list newest-first.
 */
@Entity(tableName = "saved_tracks")
data class SavedTrack(
    @PrimaryKey val trackId: String,
    val savedAt: Long         // epoch millis
)

/**
 * Records each query submitted by the user, trimmed and lowercased.
 * Maximum 20 entries kept at any time (enforced in [RecentQueryDao.insert]).
 */
@Entity(tableName = "recent_queries")
data class RecentQuery(
    @PrimaryKey val query: String,
    val usedAt: Long          // epoch millis
)

// ─────────────────────────────────────────────────────────────────
// DAOs
// ─────────────────────────────────────────────────────────────────

@Dao
interface CachedRecommendationDao {

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertOrReplace(rec: CachedRecommendation)

    @Query("SELECT * FROM cached_recommendations WHERE queryKey = :queryKey LIMIT 1")
    suspend fun getByQueryKey(queryKey: String): CachedRecommendation?

    /** Remove stale cache rows (older than [cutoff] epoch millis). */
    @Query("DELETE FROM cached_recommendations WHERE savedAt < :cutoff")
    suspend fun deleteOlderThan(cutoff: Long)
}

@Dao
interface SavedTrackDao {

    /** Live list of saved tracks, newest first. */
    @Query("SELECT * FROM saved_tracks ORDER BY savedAt DESC")
    fun observeAll(): Flow<List<SavedTrack>>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insert(savedTrack: SavedTrack)

    @Query("DELETE FROM saved_tracks WHERE trackId = :trackId")
    suspend fun deleteByTrackId(trackId: String)

    /** Emits true if the track is currently in the saved list. */
    @Query("SELECT COUNT(*) > 0 FROM saved_tracks WHERE trackId = :trackId")
    fun exists(trackId: String): Flow<Boolean>
}

@Dao
interface FeedbackDao {

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insert(feedback: FeedbackEntity)

    /** Returns up to [limit] rows that have not yet been synced and still have attempts < 10. */
    @Query("SELECT * FROM feedback WHERE synced = 0 AND attempts < 10 ORDER BY createdAt ASC LIMIT :limit")
    suspend fun getUnsynced(limit: Int = 100): List<FeedbackEntity>

    @Query("UPDATE feedback SET synced = 1 WHERE id = :id")
    suspend fun markSynced(id: Int)

    @Query("UPDATE feedback SET attempts = attempts + 1 WHERE id = :id")
    suspend fun incrementAttempts(id: Int)

    /**
     * Deletes synced rows older than [cutoff] epoch millis.
     * NEVER deletes unsynced rows — feedback must not be silently lost.
     */
    @Query("DELETE FROM feedback WHERE synced = 1 AND createdAt < :cutoff")
    suspend fun deleteSyncedOlderThan(cutoff: Long)
}

@Dao
interface RecentQueryDao {

    /** Emits the most recent 20 queries, newest first. */
    @Query("SELECT * FROM recent_queries ORDER BY usedAt DESC LIMIT 20")
    fun observeRecent(): Flow<List<RecentQuery>>

    /** Upsert a query and trim the table to 20 entries in a single transaction. */
    @Transaction
    suspend fun insert(query: RecentQuery) {
        upsert(query)
        trimToMaxEntries()
    }

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun upsert(query: RecentQuery)

    /** Keep only the 20 newest rows. */
    @Query(
        """DELETE FROM recent_queries WHERE query NOT IN
           (SELECT query FROM recent_queries ORDER BY usedAt DESC LIMIT 20)"""
    )
    suspend fun trimToMaxEntries()

    @Query("DELETE FROM recent_queries")
    suspend fun deleteAll()
}

@Dao
interface TrackDao {

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertOrReplace(track: TrackEntity)

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertAll(tracks: List<TrackEntity>)

    @Query("SELECT * FROM tracks WHERE trackId = :trackId LIMIT 1")
    suspend fun getById(trackId: String): TrackEntity?

    /**
     * Deletes track rows that are NOT in the saved list.
     * Called during clearAll() to reclaim space without touching saved tracks.
     */
    @Query("DELETE FROM tracks WHERE trackId NOT IN (SELECT trackId FROM saved_tracks)")
    suspend fun deleteNotInSaved()
}

// ─────────────────────────────────────────────────────────────────
// Database
// ─────────────────────────────────────────────────────────────────

@Database(
    entities = [
        CachedRecommendation::class,
        TrackEntity::class,
        FeedbackEntity::class,
        SavedTrack::class,
        RecentQuery::class
    ],
    version = 1,
    exportSchema = true   // schema written to $projectDir/schemas by KSP arg
)
@TypeConverters(JsonConverters::class)
abstract class AppDatabase : RoomDatabase() {

    abstract fun cachedRecommendationDao(): CachedRecommendationDao
    abstract fun savedTrackDao(): SavedTrackDao
    abstract fun feedbackDao(): FeedbackDao
    abstract fun recentQueryDao(): RecentQueryDao
    abstract fun trackDao(): TrackDao

    companion object {
        @Volatile
        private var INSTANCE: AppDatabase? = null

        fun getDatabase(context: Context): AppDatabase {
            return INSTANCE ?: synchronized(this) {
                val instance = Room.databaseBuilder(
                    context.applicationContext,
                    AppDatabase::class.java,
                    "moodwave.db"
                )
                    // Destructive migration is acceptable for a hackathon prototype.
                    // Production apps should supply proper migrations.
                    .fallbackToDestructiveMigration()
                    .build()
                INSTANCE = instance
                instance
            }
        }
    }
}
