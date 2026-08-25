package com.maozi.weather.data.api

import android.content.Context
import com.jakewharton.retrofit2.converter.kotlinx.serialization.asConverterFactory
import kotlinx.serialization.json.Json
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import java.util.concurrent.TimeUnit

object RetrofitClient {

    // TODO: 替换为实际后端地址
    // 10.0.2.2 是 Android 模拟器访问宿主机的地址
    private const val BASE_URL = "http://10.0.2.2:60245/"

    private val json = Json {
        ignoreUnknownKeys = true
        coerceInputValues = true
    }

    private var apiService: ApiService? = null
    private var okHttpClient: OkHttpClient? = null

    /**
     * 初始化（在 Application.onCreate 中调用）
     */
    fun init(context: Context) {
        val appContext = context.applicationContext

        okHttpClient = OkHttpClient.Builder()
            .connectTimeout(30, TimeUnit.SECONDS)
            .readTimeout(30, TimeUnit.SECONDS)
            .writeTimeout(30, TimeUnit.SECONDS)
            .addInterceptor { chain ->
                // 自动携带 Token
                val token = TokenManager.getTokenSync(appContext)
                val request = if (!token.isNullOrBlank()) {
                    chain.request().newBuilder()
                        .addHeader("Authorization", "Bearer $token")
                        .build()
                } else {
                    chain.request()
                }
                chain.proceed(request)
            }
            .addInterceptor(HttpLoggingInterceptor().apply {
                level = HttpLoggingInterceptor.Level.BODY
            })
            .build()

        apiService = Retrofit.Builder()
            .baseUrl(BASE_URL)
            .client(okHttpClient!!)
            .addConverterFactory(json.asConverterFactory("application/json".toMediaType()))
            .build()
            .create(ApiService::class.java)
    }

    val apiService: ApiService
        get() = checkNotNull(apiService) {
            "RetrofitClient 未初始化，请在 Application.onCreate 中调用 init()"
        }
}
