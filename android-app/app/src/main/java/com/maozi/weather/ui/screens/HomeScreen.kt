package com.maozi.weather.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
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
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Add
import androidx.compose.material.icons.filled.History
import androidx.compose.material.icons.filled.Settings
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.FloatingActionButton
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.material3.pulltorefresh.PullToRefreshBox
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
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.unit.sp
import com.maozi.weather.data.local.CachedWeather
import com.maozi.weather.data.model.City
import com.maozi.weather.data.model.UserCity
import com.maozi.weather.data.model.WeatherRealtime
import com.maozi.weather.data.repository.WeatherRepository
import com.maozi.weather.ui.WeatherIcons
import kotlinx.coroutines.launch

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun HomeScreen(
    onCityClick: (Int) -> Unit,
    onNavigateToCityManage: () -> Unit,
    onNavigateToHistory: () -> Unit,
    onNavigateToSettings: () -> Unit,
) {
    val scope = rememberCoroutineScope()
    var cities by remember { mutableStateOf<List<UserCity>>(emptyList()) }
    var realtimeMap by remember { mutableStateOf<Map<Int, WeatherRealtime?>>(emptyMap()) }
    var heroToday by remember { mutableStateOf<com.maozi.weather.data.model.WeatherForecast?>(null) }
    var loading by remember { mutableStateOf(true) }
    var refreshing by remember { mutableStateOf(false) }
    var error by remember { mutableStateOf<String?>(null) }

    // 加载关注城市 + 实况；网络失败回退本地缓存
    suspend fun loadData() {
        try {
            val list = WeatherRepository.getMyCities()
            cities = list
            error = null
            val map = mutableMapOf<Int, WeatherRealtime?>()
            list.forEach { uc ->
                val lat = uc.city.latitude
                val lon = uc.city.longitude
                if (lat != null && lon != null) {
                    try {
                        val rt = WeatherRepository.getRealtime(uc.cityId, lat, lon)
                        map[uc.cityId] = rt
                        WeatherRepository.cacheRealtime(
                            CachedWeather(
                                uc.cityId,
                                uc.city.cityName,
                                rt.temperature,
                                rt.weatherDesc,
                                rt.humidity,
                                rt.windSpeed,
                            )
                        )
                    } catch (e: Exception) {
                        map[uc.cityId] = null
                    }
                }
            }
            realtimeMap = map

            // 首页顶部大卡：取第一个城市的今日预报（最高/最低温），失败静默
            val first = list.firstOrNull()
            val flat = first?.city?.latitude
            val flon = first?.city?.longitude
            heroToday = if (first != null && flat != null && flon != null) {
                runCatching {
                    WeatherRepository.getForecast(first.cityId, flat, flon, 1).daily.firstOrNull()
                }.getOrNull()
            } else null
        } catch (e: Exception) {
            // 网络异常时回退到本地缓存
            error = "网络异常，已加载本地缓存"
            val cached = WeatherRepository.getCachedCities()
            cities = cached.map { c ->
                UserCity(
                    id = c.cityId,
                    cityId = c.cityId,
                    city = City(id = c.cityId, cityName = c.cityName),
                )
            }
            realtimeMap = cached.associate { c ->
                c.cityId to WeatherRealtime(
                    cityId = c.cityId,
                    temperature = c.temperature,
                    weatherDesc = c.weatherDesc,
                    humidity = c.humidity,
                    windSpeed = c.windSpeed,
                )
            }
        }
    }

    LaunchedEffect(Unit) {
        loading = true
        loadData()
        loading = false
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("帽子天气") },
                actions = {
                    IconButton(onClick = onNavigateToHistory) {
                        Icon(Icons.Default.History, contentDescription = "历史")
                    }
                    IconButton(onClick = onNavigateToSettings) {
                        Icon(Icons.Default.Settings, contentDescription = "设置")
                    }
                },
            )
        },
        floatingActionButton = {
            FloatingActionButton(onClick = onNavigateToCityManage) {
                Icon(Icons.Default.Add, contentDescription = "添加城市")
            }
        },
    ) { padding ->
        when {
            loading -> {
                Box(
                    modifier = Modifier.fillMaxSize().padding(padding),
                    contentAlignment = Alignment.Center,
                ) { CircularProgressIndicator() }
            }
            cities.isEmpty() -> {
                Box(
                    modifier = Modifier.fillMaxSize().padding(padding),
                    contentAlignment = Alignment.Center,
                ) {
                    Column(horizontalAlignment = Alignment.CenterHorizontally) {
                        Icon(
                            Icons.Default.Add,
                            contentDescription = null,
                            modifier = Modifier.size(48.dp),
                            tint = MaterialTheme.colorScheme.onSurfaceVariant,
                        )
                        Spacer(modifier = Modifier.height(8.dp))
                        Text(
                            "点击右下角 + 添加关注城市",
                            color = MaterialTheme.colorScheme.onSurfaceVariant,
                        )
                    }
                }
            }
            else -> {
                PullToRefreshBox(
                    isRefreshing = refreshing,
                    onRefresh = {
                        scope.launch {
                            refreshing = true
                            loadData()
                            refreshing = false
                        }
                    },
                    modifier = Modifier
                        .fillMaxSize()
                        .padding(padding),
                ) {
                    LazyColumn(
                        modifier = Modifier
                            .fillMaxSize()
                            .padding(horizontal = 16.dp),
                        verticalArrangement = Arrangement.spacedBy(12.dp),
                    ) {
                        item { Spacer(modifier = Modifier.height(4.dp)) }
                        // 顶部大卡：第一个关注城市
                        val hero = cities.firstOrNull()
                        if (hero != null) {
                            val heroRt = realtimeMap[hero.cityId]
                            item(key = "hero") {
                                HeroWeatherCard(
                                    cityName = hero.city.cityName,
                                    temperature = heroRt?.temperature,
                                    weatherDesc = heroRt?.weatherDesc,
                                    tempMax = heroToday?.tempMax,
                                    tempMin = heroToday?.tempMin,
                                    onClick = {
                                        WeatherRepository.selectedUserCity = hero
                                        onCityClick(hero.cityId)
                                    },
                                )
                            }
                        }
                        items(cities.drop(1), key = { it.id }) { uc ->
                            val rt = realtimeMap[uc.cityId]
                            WeatherCard(
                                cityId = uc.cityId,
                                cityName = uc.city.cityName,
                                temperature = rt?.temperature,
                                weatherDesc = rt?.weatherDesc,
                                onClick = {
                                    WeatherRepository.selectedUserCity = uc
                                    onCityClick(uc.cityId)
                                },
                            )
                        }
                        item { Spacer(modifier = Modifier.height(4.dp)) }
                    }
                }
            }
        }
    }
}

/**
 * 首页顶部大卡：渐变背景 + 大字温度 + 今日最高/最低温
 */
@Composable
fun HeroWeatherCard(
    cityName: String,
    temperature: Double?,
    weatherDesc: String?,
    tempMax: Double?,
    tempMin: Double?,
    onClick: () -> Unit,
) {
    val night = WeatherIcons.isNight(java.time.LocalTime.now().hour)
    val (gradStart, gradEnd) = WeatherIcons.gradientFor(weatherDesc, night)
    val gradStartColor = Color(gradStart)
    val gradEndColor = Color(gradEnd)

    Card(
        modifier = Modifier
            .fillMaxWidth()
            .clickable(onClick = onClick),
        shape = RoundedCornerShape(24.dp),
        colors = CardDefaults.cardColors(containerColor = Color.Transparent),
        elevation = CardDefaults.cardElevation(defaultElevation = 0.dp),
    ) {
        Box(
            modifier = Modifier
                .fillMaxWidth()
                .background(
                    Brush.verticalGradient(listOf(gradStartColor, gradEndColor)),
                )
                .padding(vertical = 26.dp, horizontal = 20.dp),
        ) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Column {
                    Text(
                        text = cityName,
                        style = MaterialTheme.typography.titleLarge,
                        color = androidx.compose.ui.graphics.Color.White,
                    )
                    Text(
                        text = weatherDesc ?: "—",
                        style = MaterialTheme.typography.bodyLarge,
                        color = androidx.compose.ui.graphics.Color.White.copy(alpha = 0.9f),
                    )
                    if (tempMax != null || tempMin != null) {
                        Spacer(modifier = Modifier.height(6.dp))
                        Text(
                            text = "最高 ${tempMax?.toInt() ?: "-"}° · 最低 ${tempMin?.toInt() ?: "-"}°",
                            style = MaterialTheme.typography.bodyMedium,
                            color = androidx.compose.ui.graphics.Color.White.copy(alpha = 0.8f),
                        )
                    }
                }
                Column(horizontalAlignment = Alignment.CenterHorizontally) {
                    Text(
                        text = WeatherIcons.iconFor(weatherDesc),
                        fontSize = 44.sp,
                    )
                    Text(
                        text = if (temperature != null) "${temperature.toInt()}°" else "—",
                        style = MaterialTheme.typography.displaySmall,
                        color = androidx.compose.ui.graphics.Color.White,
                    )
                }
            }
        }
    }
}

@Composable
fun WeatherCard(    cityId: Int,
    cityName: String,
    temperature: Double?,
    weatherDesc: String?,
    onClick: () -> Unit,
) {
    Card(
        modifier = Modifier
            .fillMaxWidth()
            .clickable(onClick = onClick),
        shape = RoundedCornerShape(18.dp),
        elevation = CardDefaults.cardElevation(defaultElevation = 2.dp),
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Text(
                    text = WeatherIcons.iconFor(weatherDesc),
                    fontSize = 30.sp,
                )
                Spacer(modifier = Modifier.width(12.dp))
                Column {
                    Text(
                        text = cityName,
                        style = MaterialTheme.typography.titleMedium,
                    )
                    Text(
                        text = weatherDesc ?: "—",
                        style = MaterialTheme.typography.bodyMedium,
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                    )
                }
            }
            Text(
                text = if (temperature != null) "${temperature.toInt()}°" else "—",
                style = MaterialTheme.typography.headlineMedium,
                color = MaterialTheme.colorScheme.primary,
            )
        }
    }
}
