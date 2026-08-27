package com.maozi.weather

import android.app.Application
import android.app.NotificationChannel
import android.app.NotificationManager
import android.os.Build
import androidx.work.ExistingPeriodicWorkPolicy
import androidx.work.PeriodicWorkRequestBuilder
import androidx.work.WorkManager
import com.maozi.weather.data.api.RetrofitClient
import com.maozi.weather.data.local.WeatherDatabase
import com.maozi.weather.data.repository.WeatherRepository
import com.maozi.weather.worker.WeatherRefreshWorker
import java.util.concurrent.TimeUnit

class WeatherApplication : Application() {

    val database: WeatherDatabase by lazy { WeatherDatabase.getInstance(this) }

    override fun onCreate() {
        super.onCreate()

        // 初始化 Retrofit 与数据仓库
        RetrofitClient.init(this)
        WeatherRepository.init(this)

        // 创建通知渠道
        createNotificationChannel()

        // 注册后台周期刷新（实况缓存 + 预警通知 + 小组件刷新）
        scheduleBackgroundRefresh()
    }

    /**
     * 每 15 分钟执行一次后台刷新（WorkManager 最小间隔）。
     * 未登录时工体内会自行跳过。
     */
    private fun scheduleBackgroundRefresh() {
        val request = PeriodicWorkRequestBuilder<WeatherRefreshWorker>(15, TimeUnit.MINUTES)
            .setInitialDelay(1, TimeUnit.MINUTES)
            .build()
        WorkManager.getInstance(this).enqueueUniquePeriodicWork(
            "weather_refresh",
            ExistingPeriodicWorkPolicy.UPDATE,
            request,
        )
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
