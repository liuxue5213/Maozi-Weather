package com.maozi.weather.ui.screens

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material3.Card
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.DropdownMenuItem
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.ExposedDropdownMenuBox
import androidx.compose.material3.ExposedDropdownMenuDefaults
import androidx.compose.material3.FilterChip
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
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
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.maozi.weather.data.model.UserCity
import com.maozi.weather.data.model.WeatherHistory
import com.maozi.weather.data.repository.WeatherRepository
import kotlinx.coroutines.launch
import java.time.LocalDate
import java.time.format.DateTimeFormatter

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun HistoryScreen(onBack: () -> Unit) {
    val scope = rememberCoroutineScope()
    var cities by remember { mutableStateOf<List<UserCity>>(emptyList()) }
    var selectedCity by remember { mutableStateOf<UserCity?>(null) }
    var days by remember { mutableStateOf(7) }
    var history by remember { mutableStateOf<List<WeatherHistory>>(emptyList()) }
    var loading by remember { mutableStateOf(false) }
    var error by remember { mutableStateOf<String?>(null) }
    var loaded by remember { mutableStateOf(false) }
    var cityExpanded by remember { mutableStateOf(false) }

    val fmt = DateTimeFormatter.ISO_DATE

    fun fetch() {
        val city = selectedCity ?: return
        val lat = city.city.latitude ?: return
        val lon = city.city.longitude ?: return
        val end = LocalDate.now()
        val start = end.minusDays((days - 1).toLong())
        loading = true
        error = null
        scope.launch {
            try {
                history = WeatherRepository.getHistorical(
                    cityId = city.cityId,
                    lat = lat,
                    lon = lon,
                    start = start.format(fmt),
                    end = end.format(fmt),
                )
                loaded = true
            } catch (e: Exception) {
                error = e.message ?: "加载失败"
            } finally {
                loading = false
            }
        }
    }

    LaunchedEffect(Unit) {
        scope.launch {
            try {
                cities = WeatherRepository.getMyCities()
                if (cities.isNotEmpty()) {
                    selectedCity = cities.first()
                    fetch()
                }
            } catch (e: Exception) {
                error = e.message ?: "加载城市失败"
            }
        }
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("历史天气") },
                navigationIcon = {
                    IconButton(onClick = onBack) {
                        Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = "返回")
                    }
                },
                actions = {
                    if (selectedCity != null) {
                        TextButton(onClick = { fetch() }) { Text("刷新") }
                    }
                },
            )
        },
    ) { padding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
                .padding(16.dp),
        ) {
            if (cities.isEmpty() && error == null && !loaded) {
                Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                    CircularProgressIndicator()
                }
                return@Scaffold
            }

            // 城市选择
            ExposedDropdownMenuBox(
                expanded = cityExpanded,
                onExpandedChange = { cityExpanded = it },
            ) {
                OutlinedTextField(
                    value = selectedCity?.city?.cityName ?: "请选择城市",
                    onValueChange = {},
                    readOnly = true,
                    label = { Text("城市") },
                    trailingIcon = { ExposedDropdownMenuDefaults.TrailingIcon(expanded = cityExpanded) },
                    modifier = Modifier.menuAnchor().fillMaxWidth(),
                )
                ExposedDropdownMenu(
                    expanded = cityExpanded,
                    onDismissRequest = { cityExpanded = false },
                ) {
                    cities.forEach { uc ->
                        DropdownMenuItem(
                            text = { Text(uc.city.cityName) },
                            onClick = {
                                selectedCity = uc
                                cityExpanded = false
                                fetch()
                            },
                        )
                    }
                }
            }

            Spacer(Modifier.height(12.dp))

            // 时间范围
            Text("时间范围", style = MaterialTheme.typography.labelMedium)
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                listOf(7 to "近7天", 30 to "近30天", 90 to "近90天").forEach { (d, label) ->
                    FilterChip(
                        selected = days == d,
                        onClick = {
                            days = d
                            fetch()
                        },
                        label = { Text(label) },
                    )
                }
            }

            Spacer(Modifier.height(16.dp))

            when {
                loading -> Box(Modifier.fillMaxWidth(), contentAlignment = Alignment.Center) {
                    CircularProgressIndicator()
                }
                error != null -> Text(error!!, color = MaterialTheme.colorScheme.error)
                !loaded -> Text("暂无数据，请选择城市与时间范围后刷新")
                history.isEmpty() -> Text("该时间段暂无历史数据")
                else -> LazyColumn(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    items(history) { item -> HistoryItemCard(item) }
                }
            }
        }
    }
}

@Composable
private fun HistoryItemCard(item: WeatherHistory) {
    Card(Modifier.fillMaxWidth()) {
        Row(
            Modifier
                .padding(16.dp)
                .fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Column {
                Text(
                    item.date,
                    style = MaterialTheme.typography.titleMedium,
                    fontWeight = FontWeight.Bold,
                )
                Text(
                    "降水 ${item.precipitation?.let { "%.1f".format(it) } ?: "--"} mm · " +
                        "最大风速 ${item.windSpeedMax?.let { "%.1f".format(it) } ?: "--"} m/s",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }
            Column(horizontalAlignment = Alignment.End) {
                Text(
                    "${item.tempMax?.let { "%.0f".format(it) } ?: "--"}° / " +
                        "${item.tempMin?.let { "%.0f".format(it) } ?: "--"}°",
                    style = MaterialTheme.typography.titleMedium,
                )
                Text(
                    "最高 / 最低",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }
        }
    }
}
