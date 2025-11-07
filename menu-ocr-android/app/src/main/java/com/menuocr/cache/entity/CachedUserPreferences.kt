package com.menuocr.cache.entity

import androidx.room.Entity
import androidx.room.PrimaryKey

@Entity(tableName = "cached_user_preferences")
data class CachedUserPreferences(
    @PrimaryKey
    val userId: String,
    val preferencesData: String, // JSON string of preferences data
    val timestamp: Long = System.currentTimeMillis()
)