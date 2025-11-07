package com.menuocr.cache.dao

import androidx.room.*
import com.menuocr.cache.entity.CachedMenu

@Dao
interface MenuDao {
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertMenu(menu: CachedMenu)

    @Query("SELECT * FROM cached_menus WHERE userId = :userId ORDER BY timestamp DESC LIMIT 1")
    suspend fun getMenuForUser(userId: String): CachedMenu?

    @Query("DELETE FROM cached_menus WHERE timestamp < :cutoffTime")
    suspend fun deleteOldMenus(cutoffTime: Long)

    @Query("DELETE FROM cached_menus WHERE userId = :userId")
    suspend fun deleteMenuForUser(userId: String)

    @Query("SELECT COUNT(*) FROM cached_menus")
    suspend fun getMenuCount(): Int
}