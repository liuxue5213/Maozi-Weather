package com.maozi.weather.data.api

import com.maozi.weather.data.model.AirQuality
import com.maozi.weather.data.model.City
import com.maozi.weather.data.model.HistoryObservation
import com.maozi.weather.data.model.LifeIndex
import com.maozi.weather.data.model.LoginRequest
import com.maozi.weather.data.model.SunInfo
import com.maozi.weather.data.model.TokenResponse
import com.maozi.weather.data.model.UserCity
import com.maozi.weather.data.model.WeatherForecast
import com.maozi.weather.data.model.WeatherHistory
import com.maozi.weather.data.model.WeatherForecastResponse
import com.maozi.weather.data.model.WeatherRealtime
import com.maozi.weather.data.model.WeatherWarning
import retrofit2.http.Body
import retrofit2.http.DELETE
import retrofit2.http.GET
import retrofit2.http.POST
import retrofit2.http.Path
import retrofit2.http.Query

interface ApiService {

    // ===== 鉴权 =====
    @POST("/api/auth/login")
    suspend fun login(@Body request: LoginRequest): TokenResponse

    @POST("/api/auth/logout")
    suspend fun logout(): Map<String, String>

    // ===== 城市 =====
    @GET("/api/cities/list")
    suspend fun getMyCities(): List<UserCity>

    @POST("/api/cities/add")
    suspend fun addCity(@Body body: Map<String, String>): UserCity

    @DELETE("/api/cities/delete/{id}")
    suspend fun deleteCity(@Path("id") id: Int): Map<String, String>

    @GET("/api/cities/search")
    suspend fun searchCities(@Query("keyword") keyword: String): List<City>

    // ===== 天气 =====
    @GET("/api/weather/realtime/{cityId}")
    suspend fun getRealtime(
        @Path("cityId") cityId: Int,
        @Query("latitude") latitude: Double,
        @Query("longitude") longitude: Double,
    ): WeatherRealtime

    @GET("/api/weather/forecast/{cityId}")
    suspend fun getForecast(
        @Path("cityId") cityId: Int,
        @Query("latitude") latitude: Double,
        @Query("longitude") longitude: Double,
        @Query("days") days: Int = 7,
    ): WeatherForecastResponse

    @GET("/api/weather/warning/{cityId}")
    suspend fun getWarning(@Path("cityId") cityId: Int): List<WeatherWarning>

    // ===== 空气质量 & 生活指数 & 日出日落 =====
    @GET("/api/weather/air_quality/{cityId}")
    suspend fun getAirQuality(
        @Path("cityId") cityId: Int,
        @Query("latitude") latitude: Double,
        @Query("longitude") longitude: Double,
    ): AirQuality

    @GET("/api/weather/life_index/{cityId}")
    suspend fun getLifeIndex(
        @Path("cityId") cityId: Int,
        @Query("temperature") temperature: Double = 20.0,
        @Query("humidity") humidity: Double = 50.0,
        @Query("precipitation") precipitation: Double = 0.0,
        @Query("wind_speed") windSpeed: Double = 0.0,
        @Query("uv") uv: Double = 5.0,
    ): List<LifeIndex>

    @GET("/api/weather/sun/{cityId}")
    suspend fun getSunInfo(
        @Path("cityId") cityId: Int,
        @Query("latitude") latitude: Double,
        @Query("longitude") longitude: Double,
    ): SunInfo

    // ===== 历史数据 =====
    @GET("/api/history/query")
    suspend fun queryHistory(
        @Query("station_id") stationId: String,
        @Query("start_time") startTime: String,
        @Query("end_time") endTime: String,
        @Query("page") page: Int = 1,
        @Query("page_size") pageSize: Int = 100,
    ): List<HistoryObservation>

    @GET("/api/weather/historical/{cityId}")
    suspend fun getHistorical(
        @Path("cityId") cityId: Int,
        @Query("latitude") latitude: Double,
        @Query("longitude") longitude: Double,
        @Query("start_date") startDate: String,
        @Query("end_date") endDate: String,
    ): List<WeatherHistory>
}
