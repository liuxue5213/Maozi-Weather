package com.maozi.weather.ui.screens

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.Air
import androidx.compose.material.icons.filled.Cloud
import androidx.compose.material.icons.filled.Thermostat
import androidx.compose.material.icons.filled.WaterDrop
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.unit.dp
import com.maozi.weather.data.model.AirQuality
import com.maozi.weather.data.model.LifeIndex
import com.maozi.weather.data.model.SunInfo
import com.maozi.weather.data.model.WeatherForecastResponse
import com.maozi.weather.data.model.WeatherRealtime
import com.maozi.weather.data.repository.WeatherRepository
import kotlinx.coroutines.launch

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
                try {
                    air = WeatherRepository.getAirQuality(cityId, lat, lon)
                } catch (_: Exception) { }
            }
            scope.launch {
                try {
                    forecast = WeatherRepository.getForecast(cityId, lat, lon, 7)
                } catch (_: Exception) { }
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
                try {
                    sun = WeatherRepository.getSunInfo(cityId, lat, lon)
                } catch (_: Exception) { }
            }
        } catch (e: Exception) {
            error = "获取天气失败，请稍后重试"
        } finally {
            loading = false
        }
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text(WeatherRepository.selectedUserCity?.city?.cityName ?: "天气详情") },
                navigationIcon = {
                    IconButton(onClick = onBack) {
                        Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = "返回")
                    }
                },
            )
        },
    ) { padding ->
        if (loading) {
            BoxLoading(padding)
            return@Scaffold
        }
        if (error != null) {
            Column(
                modifier = Modifier.fillMaxSize().padding(padding).padding(16.dp),
                verticalArrangement = Arrangement.Center,
                horizontalAlignment = Alignment.CenterHorizontally,
            ) {
                Text(error ?: "", color = MaterialTheme.colorScheme.error)
            }
            return@Scaffold
        }

        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
                .verticalScroll(rememberScrollState())
                .padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp),
        ) {
            // 当前温度大卡片
            Card(
                modifier = Modifier.fillMaxWidth(),
                elevation = CardDefaults.cardElevation(defaultElevation = 4.dp),
            ) {
                Column(
                    modifier = Modifier.fillMaxWidth().padding(24.dp),
                    horizontalAlignment = Alignment.CenterHorizontally,
                ) {
                    Icon(
                        Icons.Default.Cloud,
                        contentDescription = null,
                        modifier = Modifier.size(48.dp),
                        tint = MaterialTheme.colorScheme.primary,
                    )
                    Spacer(modifier = Modifier.height(8.dp))
                    Text(
                        text = if (realtime?.temperature != null) "${realtime!!.temperature}°C" else "—",
                        style = MaterialTheme.typography.displayMedium,
                        color = MaterialTheme.colorScheme.primary,
                    )
                    Text(
                        text = realtime?.weatherDesc ?: "—",
                        style = MaterialTheme.typography.titleMedium,
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                    )
                }
            }

            // 详细信息网格
            Card(modifier = Modifier.fillMaxWidth()) {
                Column(modifier = Modifier.padding(16.dp)) {
                    Text("详细信息", style = MaterialTheme.typography.titleMedium)
                    Spacer(modifier = Modifier.height(12.dp))
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceEvenly,
                    ) {
                        WeatherDetailItem("体感", realtime?.feelsLike?.let { "${it}°C" } ?: "—", Icons.Default.Thermostat)
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

            // 未来预报
            val daily = forecast?.daily ?: emptyList()
            if (daily.isNotEmpty()) {
                Card(modifier = Modifier.fillMaxWidth()) {
                    Column(modifier = Modifier.padding(16.dp)) {
                        Text("未来 ${daily.size} 天预报", style = MaterialTheme.typography.titleMedium)
                        Spacer(modifier = Modifier.height(12.dp))
                        daily.take(7).forEach { d ->
                            Row(
                                modifier = Modifier.fillMaxWidth().padding(vertical = 4.dp),
                                horizontalArrangement = Arrangement.SpaceBetween,
                            ) {
                                Text(
                                    (d.forecastTime ?: "").take(10),
                                    style = MaterialTheme.typography.bodyMedium,
                                )
                                Text(
                                    d.weatherDesc ?: "—",
                                    style = MaterialTheme.typography.bodyMedium,
                                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                                )
                                Text(
                                    "${d.tempMin ?: "-"}~${d.tempMax ?: "-"}°C",
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
                            Text(sun?.sunrise ?: "—", style = MaterialTheme.typography.titleLarge)
                        }
                        Column(horizontalAlignment = Alignment.CenterHorizontally) {
                            Text("日落", style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.onSurfaceVariant)
                            Text(sun?.sunset ?: "—", style = MaterialTheme.typography.titleLarge)
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

@Composable
private fun BoxLoading(padding: androidx.compose.foundation.layout.PaddingValues) {
    Box(
        modifier = Modifier.fillMaxSize().padding(padding),
        contentAlignment = Alignment.Center,
    ) { CircularProgressIndicator() }
}

/**
 * 国标 AQI 颜色（与 Web 端一致）
 */
fun aqiColor(aqi: Int?): Color {
    if (aqi == null) return Color(0xFF909399)
    return when {
        aqi <= 50 -> Color(0xFF67C23A)
        aqi <= 100 -> Color(0xFFE6A23C)
        aqi <= 150 -> Color(0xFFF56C6C)
        aqi <= 200 -> Color(0xFFF56C6C)
        else -> Color(0xFF8B0000)
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
