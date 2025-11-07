package com.menuocr.cache.dao

import androidx.room.*
import com.menuocr.cache.entity.CachedUserPreferences

@Dao
interface UserPreferencesDao {
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertPreferences(preferences: CachedUserPreferences)

    @Query("SELECT * FROM cached_user_preferences WHERE userId = :userId ORDER BY timestamp DESC LIMIT 1")
    suspend fun getPreferencesForUser(userId: String): CachedUserPreferences?

    @Query("DELETE FROM cached_user_preferences WHERE timestamp < :cutoffTime")
    suspend fun deleteOldPreferences(cutoffTime: Long)

    @Query("DELETE FROM cached_user_preferences WHERE userId = :userId")
    suspend fun deletePreferencesForUser(userId: String)

    @Query("SELECT COUNT(*) FROM cached_user_preferences")
    suspend fun getPreferencesCount(): Int
}