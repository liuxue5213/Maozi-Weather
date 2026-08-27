package com.maozi.weather.ui.widget

import android.content.Context
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.glance.GlanceId
import androidx.glance.GlanceModifier
import androidx.glance.GlanceTheme
import androidx.glance.background
import androidx.glance.color.ColorProvider
import androidx.glance.appwidget.GlanceAppWidget
import androidx.glance.appwidget.GlanceAppWidgetReceiver
import androidx.glance.appwidget.provideContent
import androidx.glance.layout.Column
import androidx.glance.layout.fillMaxSize
import androidx.glance.layout.padding
import androidx.glance.text.FontWeight
import androidx.glance.text.Text
import androidx.glance.text.TextStyle
import com.maozi.weather.data.local.CachedWeather
import com.maozi.weather.data.repository.WeatherRepository

/**
 * 桌面小组件：展示关注城市当前天气（取自 Room 本地缓存）。
 * 后台刷新（WeatherRefreshWorker）或 App 打开后会调用 updateAll 刷新。
 */
class WeatherWidget : GlanceAppWidget() {

    override suspend fun provideGlance(context: Context, id: GlanceId) {
        val cities: List<CachedWeather> = runCatching {
            WeatherRepository.getCachedCities()
        }.getOrDefault(emptyList())

        provideContent {
            GlanceTheme {
                WidgetContent(cities)
            }
        }
    }

    @Composable
    private fun WidgetContent(cities: List<CachedWeather>) {
        Column(
            modifier = GlanceModifier
                .fillMaxSize()
                .background(ColorProvider(Color(0xFF1B5E9B)))
                .padding(12.dp),
        ) {
            Text(
                text = "帽子天气",
                style = TextStyle(
                    fontSize = 14.sp,
                    fontWeight = FontWeight.Bold,
                    color = ColorProvider(Color.White),
                ),
            )
            if (cities.isEmpty()) {
                Text(
                    text = "打开 App 添加关注城市",
                    style = TextStyle(fontSize = 12.sp, color = ColorProvider(Color.White)),
                )
            } else {
                cities.take(3).forEach { c ->
                    val temp = c.temperature?.let { "${it.toInt()}°C" } ?: "--"
                    Text(
                        text = "${c.cityName}  $temp  ${c.weatherDesc ?: ""}",
                        style = TextStyle(fontSize = 13.sp, color = ColorProvider(Color.White)),
                    )
                }
            }
        }
    }
}

class WeatherWidgetReceiver : GlanceAppWidgetReceiver() {
    override val glanceAppWidget: GlanceAppWidget = WeatherWidget()
}
