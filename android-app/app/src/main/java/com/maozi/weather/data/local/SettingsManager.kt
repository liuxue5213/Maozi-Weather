package com.maozi.weather.data.local

import android.content.Context
import androidx.datastore.preferences.core.booleanPreferencesKey
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.longPreferencesKey
import androidx.datastore.preferences.preferencesDataStore
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.flow.map

/**
 * 本地偏好设置（DataStore）。
 * 用于持久化"预警推送"等用户开关，避免依赖后端。
 */
private val Context.settingsDataStore by preferencesDataStore(name = "settings")

object SettingsManager {

    private val NOTIFICATIONS_KEY = booleanPreferencesKey("notifications_enabled")
    private val RAIN_ALERT_KEY = booleanPreferencesKey("rain_alert_enabled")

    suspend fun isNotificationsEnabled(context: Context): Boolean =
        context.settingsDataStore.data
            .map { it[NOTIFICATIONS_KEY] ?: true }
            .first()

    suspend fun setNotificationsEnabled(context: Context, enabled: Boolean) {
        context.settingsDataStore.edit { it[NOTIFICATIONS_KEY] = enabled }
    }

    /** 降水提醒开关（默认开）：后台发现未来 2 小时有雨时推送通知 */
    suspend fun isRainAlertEnabled(context: Context): Boolean =
        context.settingsDataStore.data
            .map { it[RAIN_ALERT_KEY] ?: true }
            .first()

    suspend fun setRainAlertEnabled(context: Context, enabled: Boolean) {
        context.settingsDataStore.edit { it[RAIN_ALERT_KEY] = enabled }
    }

    /**
     * 降水提醒去重：同一城市同一 2 小时窗口只提醒一次。
     * 返回 true 表示应该提醒（bucket 比已记录的新）。
     */
    suspend fun shouldSendRainAlert(context: Context, cityId: Int, bucket: Long): Boolean {
        val key = longPreferencesKey("rain_alert_bucket_$cityId")
        val last = context.settingsDataStore.data
            .map { it[key] ?: 0L }
            .first()
        if (last >= bucket) return false
        context.settingsDataStore.edit { it[key] = bucket }
        return true
    }
}
