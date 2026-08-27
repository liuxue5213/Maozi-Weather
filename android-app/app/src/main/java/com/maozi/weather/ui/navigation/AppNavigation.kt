package com.maozi.weather.ui.navigation

import androidx.compose.runtime.Composable
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import com.maozi.weather.ui.screens.CityManageScreen
import com.maozi.weather.ui.screens.HistoryScreen
import com.maozi.weather.ui.screens.HomeScreen
import com.maozi.weather.ui.screens.LoginScreen
import com.maozi.weather.ui.screens.SettingsScreen
import com.maozi.weather.ui.screens.WeatherDetailScreen

sealed class Screen(val route: String) {
    data object Login : Screen("login")
    data object Home : Screen("home")
    data object WeatherDetail : Screen("weather_detail/{cityId}") {
        fun createRoute(cityId: Int) = "weather_detail/$cityId"
    }
    data object CityManage : Screen("city_manage")
    data object History : Screen("history")
    data object Settings : Screen("settings")
}

@Composable
fun AppNavigation() {
    val navController = rememberNavController()

    NavHost(
        navController = navController,
        startDestination = Screen.Login.route
    ) {
        composable(Screen.Login.route) {
            LoginScreen(
                onLoginSuccess = {
                    navController.navigate(Screen.Home.route) {
                        popUpTo(Screen.Login.route) { inclusive = true }
                    }
                }
            )
        }

        composable(Screen.Home.route) {
            HomeScreen(
                onCityClick = { cityId ->
                    navController.navigate(Screen.WeatherDetail.createRoute(cityId))
                },
                onNavigateToCityManage = {
                    navController.navigate(Screen.CityManage.route)
                },
                onNavigateToHistory = {
                    navController.navigate(Screen.History.route)
                },
                onNavigateToSettings = {
                    navController.navigate(Screen.Settings.route)
                }
            )
        }

        composable(Screen.WeatherDetail.route) { backStackEntry ->
            val cityId = backStackEntry.arguments?.getString("cityId")?.toIntOrNull() ?: 0
            WeatherDetailScreen(
                cityId = cityId,
                onBack = { navController.popBackStack() }
            )
        }

        composable(Screen.CityManage.route) {
            CityManageScreen(onBack = { navController.popBackStack() })
        }

        composable(Screen.History.route) {
            HistoryScreen(onBack = { navController.popBackStack() })
        }

        composable(Screen.Settings.route) {
            SettingsScreen(
                onBack = { navController.popBackStack() },
                onLogout = {
                    navController.navigate(Screen.Login.route) {
                        popUpTo(navController.graph.startDestinationId) { inclusive = true }
                    }
                }
            )
        }
    }
}
