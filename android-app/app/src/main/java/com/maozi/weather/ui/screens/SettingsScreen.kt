package com.maozi.weather.ui.screens

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.DeleteSweep
import androidx.compose.material.icons.filled.Info
import androidx.compose.material.icons.filled.Logout
import androidx.compose.material.icons.filled.NewReleases
import androidx.compose.material.icons.filled.Notifications
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.ListItem
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Switch
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
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import com.maozi.weather.data.local.SettingsManager
import com.maozi.weather.data.repository.WeatherRepository
import kotlinx.coroutines.launch

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun SettingsScreen(
    onBack: () -> Unit,
    onLogout: () -> Unit,
) {
    val context = LocalContext.current
    val scope = rememberCoroutineScope()
    var notificationsEnabled by remember { mutableStateOf(true) }
    var showLogoutConfirm by remember { mutableStateOf(false) }
    var showClearConfirm by remember { mutableStateOf(false) }
    var clearing by remember { mutableStateOf(false) }

    LaunchedEffect(Unit) {
        scope.launch { notificationsEnabled = SettingsManager.isNotificationsEnabled(context) }
    }

    if (showLogoutConfirm) {
        AlertDialog(
            onDismissRequest = { showLogoutConfirm = false },
            title = { Text("退出登录") },
            text = { Text("确定要退出当前账号吗？") },
            confirmButton = {
                TextButton(onClick = {
                    showLogoutConfirm = false
                    scope.launch {
                        WeatherRepository.logout()
                        onLogout()
                    }
                }) { Text("退出") }
            },
            dismissButton = {
                TextButton(onClick = { showLogoutConfirm = false }) { Text("取消") }
            },
        )
    }

    if (showClearConfirm) {
        AlertDialog(
            onDismissRequest = { showClearConfirm = false },
            title = { Text("清除本地缓存") },
            text = { Text("将删除设备上的离线天气缓存，下次查看需重新联网加载。") },
            confirmButton = {
                TextButton(onClick = {
                    showClearConfirm = false
                    clearing = true
                    scope.launch {
                        WeatherRepository.clearCache()
                        clearing = false
                    }
                }) { Text("清除") }
            },
            dismissButton = {
                TextButton(onClick = { showClearConfirm = false }) { Text("取消") }
            },
        )
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("设置") },
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
        ) {
            Text(
                "账号",
                style = MaterialTheme.typography.labelMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
            ListItem(
                headlineContent = { Text("退出登录") },
                leadingContent = { Icon(Icons.Filled.Logout, contentDescription = null) },
                modifier = Modifier.clickable { showLogoutConfirm = true },
            )
            HorizontalDivider()

            Text(
                "通用",
                style = MaterialTheme.typography.labelMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
            ListItem(
                headlineContent = { Text("预警推送通知") },
                supportingContent = { Text(if (notificationsEnabled) "已开启" else "已关闭") },
                leadingContent = { Icon(Icons.Filled.Notifications, contentDescription = null) },
                trailingContent = {
                    Switch(
                        checked = notificationsEnabled,
                        onCheckedChange = { v ->
                            notificationsEnabled = v
                            scope.launch { SettingsManager.setNotificationsEnabled(context, v) }
                        },
                    )
                },
            )
            ListItem(
                headlineContent = { Text("清除本地缓存") },
                supportingContent = { Text(if (clearing) "清除中…" else "删除离线天气数据") },
                leadingContent = { Icon(Icons.Filled.DeleteSweep, contentDescription = null) },
                modifier = Modifier.clickable { showClearConfirm = true },
            )
            HorizontalDivider()

            Text(
                "关于",
                style = MaterialTheme.typography.labelMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
            ListItem(
                headlineContent = { Text("数据来源") },
                supportingContent = { Text("Open-Meteo（免费气象数据）") },
                leadingContent = { Icon(Icons.Filled.Info, contentDescription = null) },
            )
            ListItem(
                headlineContent = { Text("版本") },
                supportingContent = { Text("0.1.0") },
                leadingContent = { Icon(Icons.Filled.NewReleases, contentDescription = null) },
            )
        }
    }
}
