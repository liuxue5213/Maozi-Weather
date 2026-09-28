package com.maozi.weather.worker

import android.app.NotificationManager
import android.content.Context
import androidx.core.app.NotificationCompat
import androidx.work.CoroutineWorker
import androidx.work.WorkerParameters
import com.maozi.weather.WeatherApplication
import com.maozi.weather.data.api.TokenManager
import com.maozi.weather.data.local.CachedWeather
import com.maozi.weather.data.local.SettingsManager
import com.maozi.weather.data.model.WeatherWarning
import com.maozi.weather.data.repository.WeatherRepository
import androidx.glance.appwidget.updateAll
import com.maozi.weather.ui.widget.WeatherWidget

/**
 * 后台周期任务：刷新关注城市实况到本地缓存（供离线/小组件使用），
 * 并在开启预警推送时，对生效中的气象预警发送通知。
 *
 * 通过 WorkManager 每 15 分钟执行一次（系统最小间隔），未登录时跳过。
 */
class WeatherRefreshWorker(
    private val appContext: Context,
    params: WorkerParameters,
) : CoroutineWorker(appContext, params) {

    override suspend fun doWork(): Result {
        // 未登录则不执行后台刷新
        if (!TokenManager.isLoggedIn(appContext)) return Result.success()

        return try {
            val cities = WeatherRepository.getMyCities()
            for (city in cities) {
                val lat = city.city.latitude ?: continue
                val lon = city.city.longitude ?: continue
                val cityId = city.city.id
                val cityName = city.city.cityName

                // 1. 拉取实况并写入本地缓存（离线兜底 / 小组件数据源）
                runCatching {
                    WeatherRepository.getRealtime(cityId, lat, lon)
                }.onSuccess { rt ->
                    WeatherRepository.cacheRealtime(
                        CachedWeather(
                            cityId = cityId,
                            cityName = cityName,
                            temperature = rt.temperature,
                            weatherDesc = rt.weatherDesc,
                            humidity = rt.humidity,
                            windSpeed = rt.windSpeed,
                        )
                    )
                }

                // 2. 预警通知（受设置开关控制）
                if (SettingsManager.isNotificationsEnabled(appContext)) {
                    runCatching {
                        WeatherRepository.getWarning(cityId)
                    }.getOrDefault(emptyList())
                        .filter { it.effective == 1 }
                        .forEach { postWarning(cityName, it) }
                }

                // 3. 降水提醒：未来 2 小时（15 分钟粒度）累计降水达到阈值时推送一次
                if (SettingsManager.isRainAlertEnabled(appContext)) {
                    runCatching {
                        WeatherRepository.getForecast(cityId, lat, lon, 1)
                    }.getOrNull()?.minutely?.let { minutely ->
                        val total = minutely.sumOf { it.precipitation ?: 0.0 }
                        if (total >= RAIN_ALERT_THRESHOLD_MM) {
                            val epochHour = System.currentTimeMillis() / 3_600_000
                            val bucket = epochHour / 2 // 2 小时窗口去重
                            val startTime = minutely
                                .firstOrNull { (it.precipitation ?: 0.0) >= 0.1 }
                                ?.forecastTime?.let { t ->
                                    runCatching {
                                        java.time.LocalDateTime.parse(t.take(19))
                                            .format(java.time.format.DateTimeFormatter.ofPattern("HH:mm"))
                                    }.getOrNull()
                                }
                            if (SettingsManager.shouldSendRainAlert(appContext, cityId, bucket)) {
                                postRainAlert(cityName, total, startTime)
                            }
                        }
                    }
                }
            }

            // 4. 数据更新后刷新桌面小组件
            try {
                WeatherWidget().updateAll(appContext)
            } catch (_: Exception) {
                // 小组件刷新失败不影响后台刷新结果
            }

            Result.success()
        } catch (e: Exception) {
            Result.retry()
        }
    }

    private fun postRainAlert(cityName: String, total: Double, startTime: String?) {
        val title = "$cityName 降水提醒"
        val text = buildString {
            append(if (startTime != null) "预计 $startTime 开始有雨" else "未来 2 小时有降水")
            append("，累计约 %.1f mm".format(total))
            append("，出门记得带伞 ☔")
        }
        val notification = NotificationCompat.Builder(appContext, WeatherApplication.WARNING_CHANNEL_ID)
            .setSmallIcon(android.R.drawable.ic_dialog_info)
            .setContentTitle(title)
            .setContentText(text)
            .setStyle(NotificationCompat.BigTextStyle().bigText(text))
            .setPriority(NotificationCompat.PRIORITY_DEFAULT)
            .setAutoCancel(true)
            .build()

        val manager = appContext.getSystemService(NotificationManager::class.java)
        manager.notify(("rain$cityName$startTime").hashCode(), notification)
    }

    private fun postWarning(cityName: String, warning: WeatherWarning) {        val title = buildString {
            append(cityName)
            warning.warningType?.let { append(" $it") }
            append("预警")
        }
        val notification = NotificationCompat.Builder(appContext, WeatherApplication.WARNING_CHANNEL_ID)
            .setSmallIcon(android.R.drawable.ic_dialog_alert)
            .setContentTitle(title)
            .setContentText(warning.title ?: warning.content ?: "请关注最新气象预警信息")
            .setPriority(NotificationCompat.PRIORITY_HIGH)
            .setAutoCancel(true)
            .build()

        val manager = appContext.getSystemService(NotificationManager::class.java)
        val notificationId = (cityName + (warning.warningId ?: "")).hashCode()
        manager.notify(notificationId, notification)
    }

    companion object {
        /** 未来 2 小时累计降水提醒阈值（mm），小雨起步量级 */
        const val RAIN_ALERT_THRESHOLD_MM = 0.5
    }
}
