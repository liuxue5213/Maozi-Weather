package com.maozi.weather.data.local

import android.content.Context
import androidx.room.Database
import androidx.room.Room
import androidx.room.RoomDatabase

/**
 * Room 本地数据库
 * 用于离线缓存天气数据
 */
@Database(
    entities = [CachedWeather::class],
    version = 1,
    exportSchema = false,
)
abstract class WeatherDatabase : RoomDatabase() {

    abstract fun cachedWeatherDao(): CachedWeatherDao

    companion object {
        @Volatile
        private var INSTANCE: WeatherDatabase? = null

        fun getInstance(context: Context): WeatherDatabase {
            return INSTANCE ?: synchronized(this) {
                val instance = Room.databaseBuilder(
                    context.applicationContext,
                    WeatherDatabase::class.java,
                    "maozi_weather.db"
                ).build()
                INSTANCE = instance
                instance
            }
        }
    }
}
