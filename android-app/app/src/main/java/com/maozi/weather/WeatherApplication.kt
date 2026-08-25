package com.maozi.weather

import android.app.Application
import android.app.NotificationChannel
import android.app.NotificationManager
import android.os.Build
import com.maozi.weather.data.api.RetrofitClient
import com.maozi.weather.data.local.WeatherDatabase

class WeatherApplication : Application() {

    val database: WeatherDatabase by lazy { WeatherDatabase.getInstance(this) }

    override fun onCreate() {
        super.onCreate()

        // 初始化 Retrofit
        RetrofitClient.init(this)

        // 创建通知渠道
        createNotificationChannel()
    }

    private fun createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channel = NotificationChannel(
                WARNING_CHANNEL_ID,
                "气象预警",
                NotificationManager.IMPORTANCE_HIGH
            ).apply {
                description = "关注城市的气象预警通知"
            }
            val manager = getSystemService(NotificationManager::class.java)
            manager.createNotificationChannel(channel)
        }
    }

    companion object {
        const val WARNING_CHANNEL_ID = "weather_warning"
    }
}
