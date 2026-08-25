package com.maozi.weather.data.api

import android.content.Context
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.stringPreferencesKey
import androidx.datastore.preferences.preferencesDataStore
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.flow.map
import kotlinx.coroutines.runBlocking

private val Context.authDataStore by preferencesDataStore(name = "auth")

object TokenManager {
    private val TOKEN_KEY = stringPreferencesKey("jwt_token")

    /**
     * 保存 Token（异步）
     */
    suspend fun saveToken(context: Context, token: String) {
        context.authDataStore.edit { prefs ->
            prefs[TOKEN_KEY] = token
        }
    }

    /**
     * 获取 Token（异步）
     */
    suspend fun getToken(context: Context): String? {
        return context.authDataStore.data
            .map { prefs -> prefs[TOKEN_KEY] }
            .first()
    }

    /**
     * 获取 Token（同步，用于 OkHttp 拦截器）
     */
    fun getTokenSync(context: Context): String? {
        return runBlocking { getToken(context) }
    }

    /**
     * 清除 Token
     */
    suspend fun clearToken(context: Context) {
        context.authDataStore.edit { prefs ->
            prefs.remove(TOKEN_KEY)
        }
    }

    /**
     * 检查是否已登录
     */
    suspend fun isLoggedIn(context: Context): Boolean {
        return getToken(context)?.isNotBlank() == true
    }
}
