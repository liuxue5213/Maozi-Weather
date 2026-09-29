package com.maozi.weather.ui.widget

import android.content.Context
import android.content.Intent
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.glance.GlanceId
import androidx.glance.GlanceModifier
import androidx.glance.GlanceTheme
import androidx.glance.LocalContext
import androidx.glance.LocalSize
import androidx.glance.action.clickable
import androidx.glance.appwidget.action.actionStartActivity
import androidx.glance.appwidget.cornerRadius
import androidx.glance.appwidget.SizeMode
import androidx.glance.background
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
import androidx.glance.layout.size
import androidx.glance.layout.width
import androidx.glance.text.FontWeight
import androidx.glance.text.Text
import androidx.glance.text.TextStyle
import androidx.compose.ui.unit.DpSize
import androidx.compose.ui.unit.dp
import androidx.glance.unit.ColorProvider
import com.maozi.weather.MainActivity
import com.maozi.weather.data.local.CachedWeather
import com.maozi.weather.data.repository.WeatherRepository
import com.maozi.weather.ui.WeatherIcons
import java.time.LocalDateTime
import java.time.LocalTime
import java.time.format.DateTimeFormatter

/**
 * 桌面小组件：时钟 + 关注城市当前天气（取自 Room 本地缓存）。
 * 支持两种尺寸自适应：小尺寸（2x1）只显示时钟+首个城市；大尺寸（4x2）显示至多 3 城。
 * 点击任意位置打开 App；底部显示数据更新时间。
 * 后台刷新（WeatherRefreshWorker）或 App 打开后会调用 updateAll 刷新。
 */
class WeatherWidget : GlanceAppWidget() {

    // 小/大两档目标尺寸，launcher 会取不超过实际单元格的最接近档
    override val sizeMode = SizeMode.Responsive(
        setOf(DpSize(110.dp, 40.dp), DpSize(220.dp, 110.dp)),
    )

    override suspend fun provideGlance(context: Context, id: GlanceId) {
        val cities: List<CachedWeather> = runCatching {
            WeatherRepository.getCachedCities()
        }.getOrDefault(emptyList())

        val night = WeatherIcons.isNight(LocalTime.now().hour)
        val bg = WeatherIcons.gradientFor(cities.firstOrNull()?.weatherDesc, night)

        provideContent {
            val size = LocalSize.current
            val compact = size.width < 160.dp
            GlanceTheme {
                WidgetContent(
                    cities = cities,
                    compact = compact,
                    bgTop = bg.first,
                )
            }
        }
    }

    @Composable
    private fun WidgetContent(
        cities: List<CachedWeather>,
        compact: Boolean,
        bgTop: Long,
    ) {
        val now = LocalTime.now().format(DateTimeFormatter.ofPattern("HH:mm"))
        val updatedAt = LocalDateTime.now().format(DateTimeFormatter.ofPattern("HH:mm"))

        Column(
            modifier = GlanceModifier
                .fillMaxSize()
                .cornerRadius(if (compact) 14.dp else 20.dp)
                .background(ColorProvider(Color(bgTop)))
                .clickable(actionStartActivity(Intent(LocalContext.current, MainActivity::class.java)))
                .padding(
                    start = if (compact) 10.dp else 14.dp,
                    top = if (compact) 8.dp else 12.dp,
                    end = if (compact) 10.dp else 14.dp,
                    bottom = if (compact) 6.dp else 10.dp,
                ),
        ) {
            Row(
                modifier = GlanceModifier.fillMaxWidth(),
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Text(
                    text = now,
                    style = TextStyle(
                        fontSize = if (compact) 20.sp else 26.sp,
                        fontWeight = FontWeight.Bold,
                        color = ColorProvider(Color.White),
                    ),
                )
                Spacer(GlanceModifier.defaultWeight())
                if (!compact) {
                    Text(
                        text = "帽子天气",
                        style = TextStyle(fontSize = 12.sp, color = ColorProvider(Color(0xCCFFFFFF))),
                    )
                }
            }
            Spacer(GlanceModifier.height(if (compact) 4.dp else 8.dp))
            when {
                cities.isEmpty() -> Text(
                    text = "打开 App 添加关注城市",
                    style = TextStyle(fontSize = if (compact) 11.sp else 12.sp, color = ColorProvider(Color.White)),
                )
                // 小尺寸：单行时钟 + 首城市
                compact -> {
                    val c = cities.first()
                    Row(
                        modifier = GlanceModifier.fillMaxWidth(),
                        verticalAlignment = Alignment.CenterVertically,
                    ) {
                        Text(WeatherIcons.iconFor(c.weatherDesc), style = TextStyle(fontSize = 14.sp))
                        Spacer(GlanceModifier.width(4.dp))
                        Text(
                            text = c.cityName,
                            style = TextStyle(fontSize = 12.sp, color = ColorProvider(Color.White)),
                        )
                        Spacer(GlanceModifier.defaultWeight())
                        Text(
                            text = c.temperature?.let { "${it.toInt()}°" } ?: "--",
                            style = TextStyle(
                                fontSize = 15.sp,
                                fontWeight = FontWeight.Bold,
                                color = ColorProvider(Color.White),
                            ),
                        )
                    }
                }
                // 大尺寸：至多 3 城 + 更新时间
                else -> {
                    cities.take(3).forEach { c ->
                        Row(
                            modifier = GlanceModifier.fillMaxWidth().padding(vertical = 3.dp),
                            verticalAlignment = Alignment.CenterVertically,
                        ) {
                            Text(WeatherIcons.iconFor(c.weatherDesc), style = TextStyle(fontSize = 16.sp))
                            Spacer(GlanceModifier.width(6.dp))
                            Text(
                                text = c.cityName,
                                style = TextStyle(fontSize = 13.sp, color = ColorProvider(Color.White)),
                            )
                            Spacer(GlanceModifier.defaultWeight())
                            Text(
                                text = c.temperature?.let { "${it.toInt()}°" } ?: "--",
                                style = TextStyle(
                                    fontSize = 15.sp,
                                    fontWeight = FontWeight.Bold,
                                    color = ColorProvider(Color.White),
                                ),
                            )
                        }
                    }
                    Spacer(GlanceModifier.defaultWeight())
                    Row(modifier = GlanceModifier.fillMaxWidth()) {
                        Spacer(GlanceModifier.defaultWeight())
                        Text(
                            text = "更新于 $updatedAt",
                            style = TextStyle(fontSize = 10.sp, color = ColorProvider(Color(0x99FFFFFF))),
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
