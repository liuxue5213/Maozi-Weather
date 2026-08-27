package com.maozi.weather.data.repository

import android.content.Context
import com.maozi.weather.data.api.RetrofitClient
import com.maozi.weather.data.api.TokenManager
import com.maozi.weather.data.local.WeatherDatabase
import com.maozi.weather.data.model.AirQuality
import com.maozi.weather.data.local.CachedWeather
import com.maozi.weather.data.model.City
import com.maozi.weather.data.model.LifeIndex
import com.maozi.weather.data.model.LoginRequest
import com.maozi.weather.data.model.SunInfo
import com.maozi.weather.data.model.TokenResponse
import com.maozi.weather.data.model.UserCity
import com.maozi.weather.data.model.WeatherForecast
import com.maozi.weather.data.model.WeatherWarning
import com.maozi.weather.data.model.WeatherForecastResponse
import com.maozi.weather.data.model.WeatherHistory
import com.maozi.weather.data.model.WeatherRealtime

/**
 * 统一的数据仓库：封装网络请求与本地（Room）离线缓存。
 * 在 WeatherApplication.onCreate 中调用 [init] 初始化。
 */
object WeatherRepository {

    private lateinit var appContext: Context
    private lateinit var database: WeatherDatabase

    fun init(context: Context) {
        appContext = context.applicationContext
        database = WeatherDatabase.getInstance(appContext)
    }

    private val api get() = RetrofitClient.apiService

    // ===== 鉴权 =====
    suspend fun login(username: String, password: String): TokenResponse {
        val resp = api.login(LoginRequest(username, password))
        TokenManager.saveToken(appContext, resp.accessToken)
        return resp
    }

    suspend fun logout() {
        try {
            api.logout()
        } finally {
            TokenManager.clearToken(appContext)
        }
    }

    // ===== 城市 =====
    suspend fun getMyCities(): List<UserCity> = api.getMyCities()

    suspend fun searchCities(keyword: String): List<City> = api.searchCities(keyword)

    suspend fun addCity(cityId: Int): UserCity =
        api.addCity(mapOf("city_id" to cityId.toString()))

    suspend fun deleteCity(id: Int): Map<String, String> = api.deleteCity(id)

    // ===== 天气 =====
    suspend fun getRealtime(cityId: Int, lat: Double, lon: Double): WeatherRealtime =
        api.getRealtime(cityId, lat, lon)

    suspend fun getWarning(cityId: Int): List<WeatherWarning> = api.getWarning(cityId)

    suspend fun getForecast(
        cityId: Int,
        lat: Double,
        lon: Double,
        days: Int = 7,
    ): WeatherForecastResponse = api.getForecast(cityId, lat, lon, days)

    suspend fun getAirQuality(cityId: Int, lat: Double, lon: Double): AirQuality =
        api.getAirQuality(cityId, lat, lon)

    suspend fun getLifeIndex(
        cityId: Int,
        temperature: Double,
        humidity: Double,
        precipitation: Double,
        windSpeed: Double,
        uv: Double,
    ): List<LifeIndex> = api.getLifeIndex(cityId, temperature, humidity, precipitation, windSpeed, uv)

    suspend fun getSunInfo(cityId: Int, lat: Double, lon: Double): SunInfo =
        api.getSunInfo(cityId, lat, lon)

    suspend fun getHistorical(
        cityId: Int,
        lat: Double,
        lon: Double,
        start: String,
        end: String,
    ): List<WeatherHistory> = api.getHistorical(cityId, lat, lon, start, end)

    // ===== 离线缓存 =====
    suspend fun cacheRealtime(item: CachedWeather) =
        database.cachedWeatherDao().insertOrUpdate(item)

    suspend fun getCachedCities(): List<CachedWeather> =
        database.cachedWeatherDao().getAll()

    suspend fun clearCache() =
        database.cachedWeatherDao().clearAll()

    // 当前选中城市（详情页用于取经纬度）
    var selectedUserCity: UserCity? = null
}
