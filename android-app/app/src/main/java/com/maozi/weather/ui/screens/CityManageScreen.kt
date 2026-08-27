package com.maozi.weather.ui.screens

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
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.Add
import androidx.compose.material.icons.filled.Delete
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
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
import androidx.compose.ui.unit.dp
import com.maozi.weather.data.model.City
import com.maozi.weather.data.model.UserCity
import com.maozi.weather.data.repository.WeatherRepository
import kotlinx.coroutines.launch

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun CityManageScreen(onBack: () -> Unit) {
    val scope = rememberCoroutineScope()
    var myCities by remember { mutableStateOf<List<UserCity>>(emptyList()) }
    var searchResults by remember { mutableStateOf<List<City>>(emptyList()) }
    var keyword by remember { mutableStateOf("") }
    var loading by remember { mutableStateOf(false) }
    var error by remember { mutableStateOf<String?>(null) }

    suspend fun refresh() {
        myCities = WeatherRepository.getMyCities()
    }

    LaunchedEffect(Unit) {
        try {
            refresh()
        } catch (e: Exception) {
            error = "加载关注城市失败"
        }
    }

    fun doSearch() {
        if (keyword.isBlank()) return
        loading = true
        error = null
        scope.launch {
            try {
                searchResults = WeatherRepository.searchCities(keyword)
            } catch (e: Exception) {
                error = "搜索失败"
            } finally {
                loading = false
            }
        }
    }

    fun add(city: City) {
        scope.launch {
            try {
                WeatherRepository.addCity(city.id)
                searchResults = emptyList()
                keyword = ""
                refresh()
            } catch (e: Exception) {
                error = "添加失败：${e.message ?: "未知错误"}"
            }
        }
    }

    fun remove(uc: UserCity) {
        scope.launch {
            try {
                WeatherRepository.deleteCity(uc.id)
                refresh()
            } catch (e: Exception) {
                error = "删除失败"
            }
        }
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("城市管理") },
                navigationIcon = {
                    IconButton(onClick = onBack) {
                        Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = "返回")
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
            verticalArrangement = Arrangement.spacedBy(12.dp),
        ) {
            if (error != null) {
                Text(error ?: "", color = MaterialTheme.colorScheme.error)
            }

            // 搜索
            OutlinedTextField(
                value = keyword,
                onValueChange = { keyword = it },
                label = { Text("搜索城市") },
                singleLine = true,
                modifier = Modifier.fillMaxWidth(),
                trailingIcon = {
                    IconButton(onClick = { doSearch() }) {
                        Icon(Icons.Default.Add, contentDescription = "搜索")
                    }
                },
            )

            if (loading) {
                CircularProgressIndicator()
            }

            // 搜索结果
            if (searchResults.isNotEmpty()) {
                Text("搜索结果", style = MaterialTheme.typography.titleMedium)
                LazyColumn(
                    modifier = Modifier.fillMaxWidth().height(200.dp),
                    verticalArrangement = Arrangement.spacedBy(8.dp),
                ) {
                    items(searchResults) { c ->
                        Card(
                            modifier = Modifier
                                .fillMaxWidth()
                                .clickable { add(c) },
                            elevation = CardDefaults.cardElevation(defaultElevation = 2.dp),
                        ) {
                            Row(
                                modifier = Modifier.fillMaxWidth().padding(16.dp),
                                horizontalArrangement = Arrangement.SpaceBetween,
                                verticalAlignment = Alignment.CenterVertically,
                            ) {
                                Column {
                                    Text(c.cityName, style = MaterialTheme.typography.titleMedium)
                                    Text(
                                        c.province ?: "",
                                        style = MaterialTheme.typography.bodySmall,
                                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                                    )
                                }
                                Icon(Icons.Default.Add, contentDescription = "添加")
                            }
                        }
                    }
                }
            }

            // 已关注城市
            Text("我的关注", style = MaterialTheme.typography.titleMedium)
            if (myCities.isEmpty()) {
                Box(modifier = Modifier.fillMaxWidth().padding(16.dp)) {
                    Text("暂无关注城市，搜索并添加", color = MaterialTheme.colorScheme.onSurfaceVariant)
                }
            } else {
                LazyColumn(
                    modifier = Modifier.fillMaxWidth().weight(1f, fill = false),
                    verticalArrangement = Arrangement.spacedBy(8.dp),
                ) {
                    items(myCities) { uc ->
                        Card(
                            modifier = Modifier.fillMaxWidth(),
                            elevation = CardDefaults.cardElevation(defaultElevation = 2.dp),
                        ) {
                            Row(
                                modifier = Modifier.fillMaxWidth().padding(16.dp),
                                horizontalArrangement = Arrangement.SpaceBetween,
                                verticalAlignment = Alignment.CenterVertically,
                            ) {
                                Text(uc.city.cityName, style = MaterialTheme.typography.titleMedium)
                                IconButton(onClick = { remove(uc) }) {
                                    Icon(Icons.Default.Delete, contentDescription = "删除")
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}
