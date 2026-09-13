package com.maozi.weather.ui.widget

import android.content.Context
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.glance.GlanceId
import androidx.glance.GlanceModifier
import androidx.glance.GlanceTheme
import androidx.glance.appwidget.cornerRadius
import androidx.glance.background
import androidx.glance.unit.ColorProvider as UnitColorProvider
import androidx.glance.appwidget.GlanceAppWidget
import androidx.glance.appwidget.GlanceAppWidgetReceiver
import androidx.glance.appwidget.provideContent
import androidx.glance.layout.Alignment
import androidx.glance.layout.Column
import androidx.glance.layout.Row
import androidx.glance.layout.Spacer
import androidx.glance.layout.fillMaxSize
import androidx.glance.layout.fillMaxWidth
import androidx.glance.layout.height
import androidx.glance.layout.padding
import androidx.glance.layout.width
import androidx.glance.text.FontWeight
import androidx.glance.text.Text
import androidx.glance.text.TextStyle
import com.maozi.weather.data.local.CachedWeather
import com.maozi.weather.data.repository.WeatherRepository
import com.maozi.weather.ui.WeatherIcons
import java.time.LocalTime
import java.time.format.DateTimeFormatter

/**
 * 桌面小组件：时钟 + 关注城市当前天气（取自 Room 本地缓存）。
 * 后台刷新（WeatherRefreshWorker）或 App 打开后会调用 updateAll 刷新。
 */
class WeatherWidget : GlanceAppWidget() {

    override suspend fun provideGlance(context: Context, id: GlanceId) {
        val cities: List<CachedWeather> = runCatching {
            WeatherRepository.getCachedCities()
        }.getOrDefault(emptyList())

        val now = LocalTime.now().format(DateTimeFormatter.ofPattern("HH:mm"))
        val night = WeatherIcons.isNight(LocalTime.now().hour)
        val (bgTop, bgBottom) = WeatherIcons.gradientFor(
            cities.firstOrNull()?.weatherDesc,
            night,
        )

        provideContent {
            GlanceTheme {
                WidgetContent(cities, now, bgTop, bgBottom)
            }
        }
    }

    @Composable
    private fun WidgetContent(cities: List<CachedWeather>, now: String, bgTop: Long, bgBottom: Long) {
        Column(
            modifier = GlanceModifier
                .fillMaxSize()
                .cornerRadius(20.dp)
                .background(UnitColorProvider(Color(bgTop)))
                .padding(14.dp),
        ) {
            Row(
                modifier = GlanceModifier.fillMaxWidth(),
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Text(
                    text = now,
                    style = TextStyle(
                        fontSize = 26.sp,
                        fontWeight = FontWeight.Bold,
                        color = UnitColorProvider(Color.White),
                    ),
                )
                Spacer(GlanceModifier.defaultWeight())
                Text(
                    text = "帽子天气",
                    style = TextStyle(fontSize = 12.sp, color = UnitColorProvider(Color(0xCCFFFFFF))),
                )
            }
            Spacer(GlanceModifier.height(8.dp))
            if (cities.isEmpty()) {
                Text(
                    text = "打开 App 添加关注城市",
                    style = TextStyle(fontSize = 12.sp, color = UnitColorProvider(Color.White)),
                )
            } else {
                cities.take(3).forEach { c ->
                    Row(
                        modifier = GlanceModifier.fillMaxWidth().padding(vertical = 3.dp),
                        verticalAlignment = Alignment.CenterVertically,
                    ) {
                        Text(
                            text = WeatherIcons.iconFor(c.weatherDesc),
                            style = TextStyle(fontSize = 16.sp),
                        )
                        Spacer(GlanceModifier.width(6.dp))
                        Text(
                            text = c.cityName,
                            style = TextStyle(
                                fontSize = 13.sp,
                                color = UnitColorProvider(Color.White),
                            ),
                        )
                        Spacer(GlanceModifier.defaultWeight())
                        Text(
                            text = c.temperature?.let { "${it.toInt()}°" } ?: "--",
                            style = TextStyle(
                                fontSize = 15.sp,
                                fontWeight = FontWeight.Bold,
                                color = UnitColorProvider(Color.White),
                            ),
                        )
                    }
                }
            }
        }
    }
}

class WeatherWidgetReceiver : GlanceAppWidgetReceiver() {
    override val glanceAppWidget: GlanceAppWidget = WeatherWidget()
}
