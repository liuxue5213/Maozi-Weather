package com.maozi.weather.data.model

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
data class LoginRequest(
    val username: String,
    val password: String,
)

@Serializable
data class TokenResponse(
    @SerialName("access_token") val accessToken: String,
    @SerialName("token_type") val tokenType: String = "bearer",
    val user: User,
)

@Serializable
data class User(
    val id: Int,
    val username: String,
    @SerialName("real_name") val realName: String? = null,
    @SerialName("is_active") val isActive: Boolean = true,
    @SerialName("is_admin") val isAdmin: Boolean = false,
)

@Serializable
data class City(
    val id: Int,
    @SerialName("city_name") val cityName: String,
    @SerialName("city_code") val cityCode: String? = null,
    @SerialName("station_id") val stationId: String? = null,
    val province: String? = null,
    val longitude: Double? = null,
    val latitude: Double? = null,
)

@Serializable
data class UserCity(
    val id: Int,
    @SerialName("city_id") val cityId: Int,
    @SerialName("sort_order") val sortOrder: Int = 0,
    @SerialName("view_mode") val viewMode: String = "city",
    val city: City,
)

@Serializable
data class WeatherRealtime(
    @SerialName("city_id") val cityId: Int,
    @SerialName("station_id") val stationId: String? = null,
    val temperature: Double? = null,
    @SerialName("feels_like") val feelsLike: Double? = null,
    val humidity: Double? = null,
    val pressure: Double? = null,
    @SerialName("wind_direction") val windDirection: String? = null,
    @SerialName("wind_speed") val windSpeed: Double? = null,
    val precipitation: Double? = null,
    @SerialName("weather_desc") val weatherDesc: String? = null,
    @SerialName("observe_time") val observeTime: String? = null,
    @SerialName("data_source") val dataSource: String = "CMA",
)

@Serializable
data class WeatherForecast(
    @SerialName("city_id") val cityId: Int,
    @SerialName("forecast_type") val forecastType: String,
    @SerialName("forecast_time") val forecastTime: String,
    val temperature: Double? = null,
    @SerialName("temp_max") val tempMax: Double? = null,
    @SerialName("temp_min") val tempMin: Double? = null,
    val humidity: Double? = null,
    @SerialName("weather_desc") val weatherDesc: String? = null,
    @SerialName("wind_direction") val windDirection: String? = null,
    @SerialName("wind_speed") val windSpeed: Double? = null,
    val pop: Double? = null,
)

/**
 * 后端 /api/weather/forecast/{cityId} 返回结构（实况/预报/日出日落分离）
 */
@Serializable
data class WeatherForecastResponse(
    val daily: List<WeatherForecast> = emptyList(),
    val hourly: List<WeatherForecast> = emptyList(),
    val sun: SunInfo? = null,
)

@Serializable
data class WeatherWarning(
    @SerialName("city_id") val cityId: Int,
    @SerialName("warning_id") val warningId: String? = null,
    @SerialName("warning_type") val warningType: String? = null,
    @SerialName("warning_level") val warningLevel: String? = null,
    val title: String? = null,
    val content: String? = null,
    @SerialName("publish_time") val publishTime: String? = null,
    val effective: Int = 1,
)

@Serializable
data class HistoryObservation(
    val id: Int,
    @SerialName("station_id") val stationId: String,
    @SerialName("observe_time") val observeTime: String,
    val temperature: Double? = null,
    val pressure: Double? = null,
    val humidity: Double? = null,
    @SerialName("wind_direction") val windDirection: Double? = null,
    @SerialName("wind_speed") val windSpeed: Double? = null,
    val precipitation: Double? = null,
    @SerialName("is_missing") val isMissing: Int = 0,
    @SerialName("missing_fields") val missingFields: String? = null,
)

/**
 * 后端 /api/weather/historical/{city_id} 返回结构（Open-Meteo 历史天气，按日）
 */
@Serializable
data class WeatherHistory(
    @SerialName("city_id") val cityId: Int,
    val date: String,
    @SerialName("temp_max") val tempMax: Double? = null,
    @SerialName("temp_min") val tempMin: Double? = null,
    val precipitation: Double? = null,
    @SerialName("wind_speed_max") val windSpeedMax: Double? = null,
    @SerialName("data_source") val dataSource: String = "Open-Meteo",
)

// ===== 空气质量 & 生活指数 & 日出日落 =====

@Serializable
data class AirQuality(
    @SerialName("city_id") val cityId: Int,
    @SerialName("station_id") val stationId: String? = null,
    val aqi: Int? = null,
    @SerialName("aqi_level") val aqiLevel: String? = null,
    @SerialName("aqi_primary") val aqiPrimary: String? = null,
    val pm25: Double? = null,
    val pm10: Double? = null,
    val so2: Double? = null,
    val no2: Double? = null,
    val co: Double? = null,
    val o3: Double? = null,
    @SerialName("data_type") val dataType: String = "realtime",
    @SerialName("forecast_time") val forecastTime: String? = null,
    @SerialName("data_source") val dataSource: String = "CMA",
)

@Serializable
data class LifeIndex(
    @SerialName("index_type") val indexType: String,
    @SerialName("index_name") val indexName: String,
    @SerialName("index_level") val indexLevel: String? = null,
    @SerialName("index_desc") val indexDesc: String? = null,
    @SerialName("forecast_date") val forecastDate: String? = null,
)

@Serializable
data class SunInfo(
    val sunrise: String? = null,
    val sunset: String? = null,
    @SerialName("daylight_hours") val daylightHours: Double? = null,
)
