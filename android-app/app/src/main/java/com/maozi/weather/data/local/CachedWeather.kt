package com.maozi.weather.data.local

import androidx.room.Dao
import androidx.room.Entity
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.PrimaryKey
import androidx.room.Query

/**
 * 缓存的天气数据（离线用）
 */
@Entity(tableName = "cached_weather")
data class CachedWeather(
    @PrimaryKey val cityId: Int,
    val cityName: String,
    val temperature: Double?,
    val weatherDesc: String?,
    val humidity: Double?,
    val windSpeed: Double?,
    val cachedAt: Long = System.currentTimeMillis(),
)

@Dao
interface CachedWeatherDao {

    @Query("SELECT * FROM cached_weather ORDER BY cityId ASC")
    suspend fun getAll(): List<CachedWeather>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertOrUpdate(weather: CachedWeather)

    @Query("DELETE FROM cached_weather WHERE cityId = :cityId")
    suspend fun deleteByCityId(cityId: Int)

    @Query("DELETE FROM cached_weather")
    suspend fun clearAll()
}
