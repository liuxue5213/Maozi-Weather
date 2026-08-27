package com.maozi.weather.data.local

import android.content.Context
import androidx.datastore.preferences.core.booleanPreferencesKey
import androidx.datastore.preferences.core.edit
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

    suspend fun isNotificationsEnabled(context: Context): Boolean =
        context.settingsDataStore.data
            .map { it[NOTIFICATIONS_KEY] ?: true }
            .first()

    suspend fun setNotificationsEnabled(context: Context, enabled: Boolean) {
        context.settingsDataStore.edit { it[NOTIFICATIONS_KEY] = enabled }
    }
}
