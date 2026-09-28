package com.maozi.weather.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.statusBarsPadding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.Air
import androidx.compose.material.icons.filled.Speed
import androidx.compose.material.icons.filled.WaterDrop
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.maozi.weather.data.model.AirQuality
import com.maozi.weather.data.model.LifeIndex
import com.maozi.weather.data.model.MinutelyPrecip
import com.maozi.weather.data.model.SunInfo
import com.maozi.weather.data.model.WeatherForecastResponse
import com.maozi.weather.data.model.WeatherRealtime
import com.maozi.weather.data.model.WeatherWarning
import com.maozi.weather.data.repository.WeatherRepository
import com.maozi.weather.ui.HourlyTemperatureChart
import com.maozi.weather.ui.WeatherIcons
import kotlinx.coroutines.launch
import java.time.LocalDate
import java.time.LocalDateTime
import java.time.LocalTime
import java.time.format.DateTimeFormatter

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun WeatherDetailScreen(
    cityId: Int,
    onBack: () -> Unit,
) {
    val scope = rememberCoroutineScope()
    var realtime by remember { mutableStateOf<WeatherRealtime?>(null) }
    var air by remember { mutableStateOf<AirQuality?>(null) }
    var forecast by remember { mutableStateOf<WeatherForecastResponse?>(null) }
    var lifeIndices by remember { mutableStateOf<List<LifeIndex>>(emptyList()) }
    var sun by remember { mutableStateOf<SunInfo?>(null) }
    var warnings by remember { mutableStateOf<List<WeatherWarning>>(emptyList()) }
    var loading by remember { mutableStateOf(true) }
    var error by remember { mutableStateOf<String?>(null) }

    LaunchedEffect(cityId) {
        loading = true
        error = null
        val uc = WeatherRepository.selectedUserCity
        val lat = uc?.city?.latitude
        val lon = uc?.city?.longitude
        if (lat == null || lon == null) {
            loading = false
            error = "缺少城市经纬度，无法获取天气"
            return@LaunchedEffect
        }
        try {
            val rt = WeatherRepository.getRealtime(cityId, lat, lon)
            realtime = rt
            scope.launch {
                try { air = WeatherRepository.getAirQuality(cityId, lat, lon) } catch (_: Exception) { }
            }
            scope.launch {
                try { forecast = WeatherRepository.getForecast(cityId, lat, lon, 7) } catch (_: Exception) { }
            }
            scope.launch {
                try {
                    lifeIndices = WeatherRepository.getLifeIndex(
                        cityId,
                        rt.temperature ?: 20.0,
                        rt.humidity ?: 50.0,
                        rt.precipitation ?: 0.0,
                        rt.windSpeed ?: 0.0,
                        rt.temperature ?: 5.0,
                    )
                } catch (_: Exception) { }
            }
            scope.launch {
                try { sun = WeatherRepository.getSunInfo(cityId, lat, lon) } catch (_: Exception) { }
            }
            scope.launch {
                try { warnings = WeatherRepository.getWarning(cityId) } catch (_: Exception) { }
            }
        } catch (e: Exception) {
            error = "获取天气失败，请稍后重试"
        } finally {
            loading = false
        }
    }

    if (loading) {
        Box(
            modifier = Modifier.fillMaxSize().background(MaterialTheme.colorScheme.background),
            contentAlignment = Alignment.Center,
        ) { CircularProgressIndicator() }
        return
    }
    if (error != null) {
        Box(
            modifier = Modifier.fillMaxSize().background(MaterialTheme.colorScheme.background),
            contentAlignment = Alignment.Center,
        ) {
            Text(error ?: "", color = MaterialTheme.colorScheme.error)
        }
        return
    }

    val desc = realtime?.weatherDesc
    val night = remember(sun) {
        val now = LocalTime.now()
        val sunrise = sun?.sunrise?.let { parseTime(it) }
        val sunset = sun?.sunset?.let { parseTime(it) }
        if (sunrise != null && sunset != null) now < sunrise || now > sunset
        else WeatherIcons.isNight(now.hour)
    }
    val (gradStart, gradEnd) = WeatherIcons.gradientFor(desc, night)

    // 沉浸式布局：渐变头部直接顶到状态栏，无 Scaffold 顶栏
    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(MaterialTheme.colorScheme.background),
    ) {
        Column(
            modifier = Modifier
                .fillMaxSize()
                .verticalScroll(rememberScrollState()),
        ) {
            // ===== 渐变头部（含状态栏区域 + 返回栏） =====
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .background(Brush.verticalGradient(listOf(Color(gradStart), Color(gradEnd)))),
            ) {
                Column(
                    modifier = Modifier
                        .statusBarsPadding()
                        .fillMaxWidth()
                        .padding(bottom = 28.dp),
                    horizontalAlignment = Alignment.CenterHorizontally,
                ) {
                    Row(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(horizontal = 4.dp),
                        verticalAlignment = Alignment.CenterVertically,
                    ) {
                        IconButton(onClick = onBack) {
                            Icon(
                                Icons.AutoMirrored.Filled.ArrowBack,
                                contentDescription = "返回",
                                tint = Color.White,
                            )
                        }
                        Text(
                            text = WeatherRepository.selectedUserCity?.city?.cityName ?: "天气详情",
                            style = MaterialTheme.typography.titleMedium,
                            color = Color.White,
                        )
                    }
                    Spacer(modifier = Modifier.height(12.dp))
                    Text(text = WeatherIcons.iconFor(desc), fontSize = 72.sp)
                    Spacer(modifier = Modifier.height(8.dp))
                    Text(
                        text = if (realtime?.temperature != null)
                            "${realtime!!.temperature!!.toInt()}°" else "—",
                        style = MaterialTheme.typography.displayLarge,
                        fontWeight = FontWeight.Light,
                        color = Color.White,
                    )
                    Text(
                        text = desc ?: "—",
                        style = MaterialTheme.typography.titleMedium,
                        color = Color.White.copy(alpha = 0.9f),
                    )
                    Spacer(modifier = Modifier.height(12.dp))
                    Row(horizontalArrangement = Arrangement.spacedBy(20.dp)) {
                        val today = forecast?.daily?.firstOrNull()
                        HeaderStat("体感", realtime?.feelsLike?.let { "${it.toInt()}°" } ?: "—")
                        HeaderStat("最高", today?.tempMax?.let { "${it.toInt()}°" } ?: "—")
                        HeaderStat("最低", today?.tempMin?.let { "${it.toInt()}°" } ?: "—")
                        HeaderStat("湿度", realtime?.humidity?.let { "${it.toInt()}%" } ?: "—")
                        HeaderStat("风向", realtime?.windDirection ?: "—")
                    }
                }
            }

            // ===== 内容卡片 =====
            Column(
                modifier = Modifier.padding(16.dp),
                verticalArrangement = Arrangement.spacedBy(16.dp),
            ) {
                // 气象预警横幅
                warnings.filter { it.effective == 1 }.forEach { w ->
                    WarningBanner(w)
                }

                // 降水临近预报（未来 2 小时，15 分钟粒度）
                val minutely = forecast?.minutely ?: emptyList()
                RainNowcastCard(minutely)

                // 详细信息网格
                Card(modifier = Modifier.fillMaxWidth()) {
                    Column(modifier = Modifier.padding(16.dp)) {
                        Text("详细信息", style = MaterialTheme.typography.titleMedium)
                        Spacer(modifier = Modifier.height(12.dp))
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.SpaceEvenly,
                        ) {
                            WeatherDetailItem("气压", realtime?.pressure?.let { "${it.toInt()}hPa" } ?: "—", Icons.Default.Speed)
                            WeatherDetailItem("湿度", realtime?.humidity?.let { "${it}%" } ?: "—", Icons.Default.WaterDrop)
                            WeatherDetailItem("空气质量", air?.aqiLevel ?: "—", Icons.Default.Air)
                        }
                    }
                }

                // 空气质量卡片
                Card(modifier = Modifier.fillMaxWidth()) {
                    Column(modifier = Modifier.padding(16.dp)) {
                        Text("空气质量", style = MaterialTheme.typography.titleMedium)
                        Spacer(modifier = Modifier.height(12.dp))
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.Center,
                            verticalAlignment = Alignment.Bottom,
                        ) {
                            Text(
                                text = air?.aqi?.toString() ?: "—",
                                style = MaterialTheme.typography.displaySmall,
                                color = aqiColor(air?.aqi),
                            )
                            Spacer(modifier = Modifier.padding(horizontal = 4.dp))
                            Text(
                                text = air?.aqiLevel ?: "—",
                                style = MaterialTheme.typography.titleMedium,
                                color = aqiColor(air?.aqi),
                            )
                        }
                        Spacer(modifier = Modifier.height(12.dp))
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.SpaceEvenly,
                        ) {
                            AirQualityItem("PM2.5", air?.pm25?.toString() ?: "—")
                            AirQualityItem("PM10", air?.pm10?.toString() ?: "—")
                            AirQualityItem("SO₂", air?.so2?.toString() ?: "—")
                            AirQualityItem("NO₂", air?.no2?.toString() ?: "—")
                        }
                    }
                }

                // 逐小时预报
                val hourly = forecast?.hourly?.take(24) ?: emptyList()
                if (hourly.isNotEmpty()) {
                    Card(
                        modifier = Modifier.fillMaxWidth(),
                        shape = RoundedCornerShape(20.dp),
                    ) {
                        Column(modifier = Modifier.padding(16.dp)) {
                            Text("24 小时预报", style = MaterialTheme.typography.titleMedium)
                            Spacer(modifier = Modifier.height(4.dp))
                            HourlyTemperatureChart(hourly = hourly)
                            Spacer(modifier = Modifier.height(8.dp))
                            LazyRow(horizontalArrangement = Arrangement.spacedBy(18.dp)) {
                                items(hourly) { h ->
                                    val hour = h.forecastTime?.let { t ->
                                        runCatching {
                                            LocalDateTime.parse(t.take(19)).format(DateTimeFormatter.ofPattern("HH时"))
                                        }.getOrNull()
                                    } ?: "--"
                                    Column(horizontalAlignment = Alignment.CenterHorizontally) {
                                        Text(
                                            hour,
                                            style = MaterialTheme.typography.bodySmall,
                                            color = MaterialTheme.colorScheme.onSurfaceVariant,
                                        )
                                        Spacer(modifier = Modifier.height(4.dp))
                                        Text(WeatherIcons.iconFor(h.weatherDesc), fontSize = 22.sp)
                                        Spacer(modifier = Modifier.height(4.dp))
                                        Text(
                                            h.temperature?.let { "${it.toInt()}°" } ?: "—",
                                            style = MaterialTheme.typography.titleSmall,
                                        )
                                        if ((h.pop ?: 0.0) > 0) {
                                            Text(
                                                "${h.pop!!.toInt()}%",
                                                style = MaterialTheme.typography.labelSmall,
                                                color = Color(0xFF42A5F5),
                                            )
                                        }
                                    }
                                }
                            }
                        }
                    }
                }

                // 未来预报
                val daily = forecast?.daily ?: emptyList()
                if (daily.isNotEmpty()) {
                    Card(modifier = Modifier.fillMaxWidth()) {
                        Column(modifier = Modifier.padding(16.dp)) {
                            Text("未来 ${daily.size} 天预报", style = MaterialTheme.typography.titleMedium)
                            Spacer(modifier = Modifier.height(12.dp))
                            daily.take(7).forEach { d ->
                                val dateLabel = d.forecastTime?.let { t ->
                                    runCatching {
                                        val date = LocalDate.parse(t.take(10))
                                        when (date) {
                                            LocalDate.now() -> "今天"
                                            LocalDate.now().plusDays(1) -> "明天"
                                            else -> date.format(DateTimeFormatter.ofPattern("M/d"))
                                        }
                                    }.getOrNull()
                                } ?: (d.forecastTime ?: "").take(10)
                                Row(
                                    modifier = Modifier.fillMaxWidth().padding(vertical = 6.dp),
                                    horizontalArrangement = Arrangement.SpaceBetween,
                                    verticalAlignment = Alignment.CenterVertically,
                                ) {
                                    Text(dateLabel, style = MaterialTheme.typography.bodyMedium, modifier = Modifier.weight(1.2f))
                                    Text(WeatherIcons.iconFor(d.weatherDesc), fontSize = 18.sp, modifier = Modifier.weight(0.8f))
                                    Text(
                                        d.weatherDesc ?: "—",
                                        style = MaterialTheme.typography.bodyMedium,
                                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                                        modifier = Modifier.weight(1.5f),
                                    )
                                    Text(
                                        "${d.tempMin?.toInt() ?: "-"}~${d.tempMax?.toInt() ?: "-"}°",
                                        style = MaterialTheme.typography.bodyMedium,
                                    )
                                }
                            }
                        }
                    }
                }

                // 生活指数卡片
                if (lifeIndices.isNotEmpty()) {
                    Card(modifier = Modifier.fillMaxWidth()) {
                        Column(modifier = Modifier.padding(16.dp)) {
                            Text("生活指数", style = MaterialTheme.typography.titleMedium)
                            Spacer(modifier = Modifier.height(12.dp))
                            lifeIndices.forEach { idx ->
                                LifeIndexItem(
                                    idx.indexName,
                                    idx.indexLevel ?: "—",
                                    idx.indexDesc ?: "",
                                )
                                Spacer(modifier = Modifier.height(8.dp))
                            }
                        }
                    }
                }

                // 日出日落卡片
                Card(modifier = Modifier.fillMaxWidth()) {
                    Column(modifier = Modifier.padding(16.dp)) {
                        Text("日出日落", style = MaterialTheme.typography.titleMedium)
                        Spacer(modifier = Modifier.height(12.dp))
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.SpaceEvenly,
                        ) {
                            Column(horizontalAlignment = Alignment.CenterHorizontally) {
                                Text("日出", style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.onSurfaceVariant)
                                Text(sun?.sunrise?.take(5) ?: "—", style = MaterialTheme.typography.titleLarge)
                            }
                            Column(horizontalAlignment = Alignment.CenterHorizontally) {
                                Text("日落", style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.onSurfaceVariant)
                                Text(sun?.sunset?.take(5) ?: "—", style = MaterialTheme.typography.titleLarge)
                            }
                            Column(horizontalAlignment = Alignment.CenterHorizontally) {
                                Text("昼长", style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.onSurfaceVariant)
                                Text("${sun?.daylightHours ?: "—"}h", style = MaterialTheme.typography.titleLarge)
                            }
                        }
                    }
                }

                // 数据来源
                Text(
                    text = "数据来源：${realtime?.dataSource ?: "Open-Meteo（和风天气增强）"} | 帽子天气",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                    modifier = Modifier.align(Alignment.CenterHorizontally),
                )
            }
        }
    }
}

/**
 * 未来 2 小时降水临近预报卡片：
 * 有降水时展示 8 个 15 分钟时段的降水柱状图与开始时间提示；无降水不占版面。
 */
@Composable
private fun RainNowcastCard(minutely: List<MinutelyPrecip>) {
    if (minutely.isEmpty()) return
    val total = minutely.sumOf { it.precipitation ?: 0.0 }
    if (total < 0.1) return

    val firstRain = minutely.firstOrNull { (it.precipitation ?: 0.0) >= 0.1 }
    val startTime = firstRain?.forecastTime?.let { t ->
        runCatching { LocalDateTime.parse(t.take(19)).format(DateTimeFormatter.ofPattern("HH:mm")) }.getOrNull()
    }
    val maxPrecip = maxOf(minutely.maxOf { it.precipitation ?: 0.0 }, 0.5)

    Card(
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(20.dp),
        colors = CardDefaults.cardColors(containerColor = Color(0xFFE3F2FD)),
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Text("🌧️", fontSize = 20.sp)
                Spacer(modifier = Modifier.width(8.dp))
                Text(
                    text = if (startTime != null && firstRain !== minutely.firstOrNull())
                        "预计 $startTime 开始有雨"
                    else "未来 2 小时有降水",
                    style = MaterialTheme.typography.titleMedium,
                    color = Color(0xFF1565C0),
                )
                Spacer(modifier = Modifier.weight(1f))
                Text(
                    text = "约 %.1f mm".format(total),
                    style = MaterialTheme.typography.titleSmall,
                    color = Color(0xFF1565C0),
                )
            }
            Spacer(modifier = Modifier.height(12.dp))
            Row(
                modifier = Modifier.fillMaxWidth().height(56.dp),
                verticalAlignment = Alignment.Bottom,
                horizontalArrangement = Arrangement.spacedBy(6.dp),
            ) {
                minutely.forEach { m ->
                    val p = m.precipitation ?: 0.0
                    Box(
                        modifier = Modifier
                            .weight(1f)
                            .height((10 + 46 * (p / maxPrecip)).dp)
                            .background(
                                Color(0xFF42A5F5).copy(alpha = if (p >= 0.1) 0.9f else 0.25f),
                                RoundedCornerShape(3.dp),
                            ),
                    )
                }
            }
            Spacer(modifier = Modifier.height(4.dp))
            Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                Text("现在", style = MaterialTheme.typography.labelSmall, color = Color(0xFF1565C0))
                Text("2 小时后", style = MaterialTheme.typography.labelSmall, color = Color(0xFF1565C0))
            }
        }
    }
}

/** 气象预警横幅：按预警级别着色的描边卡片 */
@Composable
private fun WarningBanner(w: WeatherWarning) {
    val color = when (w.warningLevel) {
        "红色" -> Color(0xFFD32F2F)
        "橙色" -> Color(0xFFF57C00)
        "黄色" -> Color(0xFFF9A825)
        "蓝色" -> Color(0xFF1976D2)
        else -> Color(0xFF607D8B)
    }
    Card(
        modifier = Modifier
            .fillMaxWidth()
            .border(1.dp, color.copy(alpha = 0.5f), RoundedCornerShape(16.dp)),
        shape = RoundedCornerShape(16.dp),
        colors = CardDefaults.cardColors(containerColor = color.copy(alpha = 0.10f)),
    ) {
        Column(modifier = Modifier.padding(14.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Text("⚠️", fontSize = 18.sp)
                Spacer(modifier = Modifier.width(8.dp))
                Text(
                    text = w.title ?: listOfNotNull(
                        w.warningType,
                        w.warningLevel,
                    ).joinToString("") + "预警",
                    style = MaterialTheme.typography.titleSmall,
                    color = color,
                    fontWeight = FontWeight.Bold,
                )
            }
            if (!w.content.isNullOrBlank()) {
                Spacer(modifier = Modifier.height(6.dp))
                Text(
                    text = w.content,
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurface,
                    maxLines = 3,
                )
            }
        }
    }
}

@Composable
private fun HeaderStat(label: String, value: String) {
    Column(horizontalAlignment = Alignment.CenterHorizontally) {
        Text(value, style = MaterialTheme.typography.titleSmall, color = Color.White)
        Text(label, style = MaterialTheme.typography.labelSmall, color = Color.White.copy(alpha = 0.75f))
    }
}

private fun parseTime(s: String): LocalTime? = runCatching {
    LocalTime.parse(s.take(8))
}.getOrNull()

/**
 * 国标 AQI 颜色：优绿 / 良黄 / 轻度橙 / 中度红 / 重度紫 / 严重褐红
 */
fun aqiColor(aqi: Int?): Color {
    if (aqi == null) return Color(0xFF909399)
    return when {
        aqi <= 50 -> Color(0xFF4CAF50)
        aqi <= 100 -> Color(0xFFFFC107)
        aqi <= 150 -> Color(0xFFFF9800)
        aqi <= 200 -> Color(0xFFF44336)
        aqi <= 300 -> Color(0xFF9C27B0)
        else -> Color(0xFF8D2E2E)
    }
}

@Composable
fun WeatherDetailItem(label: String, value: String, icon: ImageVector) {
    Column(
        horizontalAlignment = Alignment.CenterHorizontally,
    ) {
        Icon(
            icon,
            contentDescription = null,
            modifier = Modifier.size(24.dp),
            tint = MaterialTheme.colorScheme.primary,
        )
        Spacer(modifier = Modifier.height(4.dp))
        Text(value, style = MaterialTheme.typography.titleMedium)
        Text(label, style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
    }
}

@Composable
fun AirQualityItem(label: String, value: String) {
    Column(
        horizontalAlignment = Alignment.CenterHorizontally,
    ) {
        Text(value, style = MaterialTheme.typography.titleMedium)
        Text(label, style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
    }
}

@Composable
fun LifeIndexItem(name: String, level: String, desc: String) {
    Row(
        modifier = Modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.SpaceBetween,
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Column(modifier = Modifier.weight(1f)) {
            Text(name, style = MaterialTheme.typography.bodyMedium)
            Text(desc, style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
        }
        Text(
            level,
            style = MaterialTheme.typography.titleSmall,
            color = MaterialTheme.colorScheme.primary,
        )
    }
}
