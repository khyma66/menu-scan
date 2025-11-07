package com.menuocr.cache

import android.content.Context
import androidx.room.Database
import androidx.room.Room
import androidx.room.RoomDatabase
import androidx.room.TypeConverters
import com.menuocr.cache.dao.MenuDao
import com.menuocr.cache.dao.UserPreferencesDao
import com.menuocr.cache.entity.CachedMenu
import com.menuocr.cache.entity.CachedUserPreferences
import com.menuocr.cache.converter.Converters

@Database(
    entities = [CachedMenu::class, CachedUserPreferences::class],
    version = 1,
    exportSchema = false
)
@TypeConverters(Converters::class)
abstract class AppDatabase : RoomDatabase() {
    abstract fun menuDao(): MenuDao
    abstract fun userPreferencesDao(): UserPreferencesDao

    companion object {
        @Volatile
        private var INSTANCE: AppDatabase? = null

        fun getDatabase(context: Context): AppDatabase {
            return INSTANCE ?: synchronized(this) {
                val instance = Room.databaseBuilder(
                    context.applicationContext,
                    AppDatabase::class.java,
                    "menu_ocr_database"
                )
                    .fallbackToDestructiveMigration()
                    .build()
                INSTANCE = instance
                instance
            }
        }
    }
}

class CacheManager(private val database: AppDatabase) {

    private val menuDao = database.menuDao()
    private val preferencesDao = database.userPreferencesDao()

    suspend fun cacheMenu(userId: String, menuData: String, timestamp: Long) {
        val cachedMenu = CachedMenu(
            userId = userId,
            menuData = menuData,
            timestamp = timestamp
        )
        menuDao.insertMenu(cachedMenu)
    }

    suspend fun getCachedMenu(userId: String): CachedMenu? {
        return menuDao.getMenuForUser(userId)
    }

    suspend fun cacheUserPreferences(userId: String, preferencesData: String, timestamp: Long) {
        val cachedPrefs = CachedUserPreferences(
            userId = userId,
            preferencesData = preferencesData,
            timestamp = timestamp
        )
        preferencesDao.insertPreferences(cachedPrefs)
    }

    suspend fun getCachedUserPreferences(userId: String): CachedUserPreferences? {
        return preferencesDao.getPreferencesForUser(userId)
    }

    suspend fun clearOldCache(maxAgeMillis: Long) {
        val cutoffTime = System.currentTimeMillis() - maxAgeMillis
        menuDao.deleteOldMenus(cutoffTime)
        preferencesDao.deleteOldPreferences(cutoffTime)
    }

    suspend fun clearUserCache(userId: String) {
        menuDao.deleteMenuForUser(userId)
        preferencesDao.deletePreferencesForUser(userId)
    }
}