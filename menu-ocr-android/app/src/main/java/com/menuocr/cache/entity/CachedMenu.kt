package com.menuocr.cache.entity

import androidx.room.Entity
import androidx.room.PrimaryKey

@Entity(tableName = "cached_menus")
data class CachedMenu(
    @PrimaryKey
    val userId: String,
    val menuData: String, // JSON string of menu data
    val timestamp: Long = System.currentTimeMillis()
)