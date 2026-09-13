package com.maozi.weather.ui

/**
 * 天气描述/天气代码 → 展示用图标（emoji）与主题渐变色。
 * emoji 方案无需引入额外图标库，Compose 与 Glance 小组件均可直接渲染。
 */
object WeatherIcons {

    /** 按天气描述关键词返回图标，兜底返回 ❓ 的近亲 ☁️ */
    fun iconFor(desc: String?): String {
        if (desc.isNullOrBlank()) return "☁️"
        val d = desc
        return when {
            d.contains("雷") -> "⛈️"
            d.contains("冰雹") -> "🌨️"
            d.contains("大雨") || d.contains("暴雨") || d.contains("大暴雨") -> "🌧️"
            d.contains("雨") -> "🌦️"
            d.contains("雪") || d.contains("冰") -> "❄️"
            d.contains("雾") || d.contains("霾") -> "🌫️"
            d.contains("沙") || d.contains("尘") -> "💨"
            d.contains("阴") -> "☁️"
            d.contains("多云") -> "⛅"
            d.contains("晴") -> "☀️"
            else -> "☁️"
        }
    }

    /** 是否适合用"夜间"配色（无日出日落信息时按 6:00-19:00 粗略判断） */
    fun isNight(hour: Int): Boolean = hour < 6 || hour >= 19

    /**
     * 顶部渐变背景色对 [start, end]，按天气 + 昼夜区分。
     * 返回 ARGB 十六进制颜色。
     */
    fun gradientFor(desc: String?, night: Boolean): Pair<Long, Long> = when {
        desc != null && (desc.contains("雷")) ->
            if (night) 0xFF1A1A2E to 0xFF16213E else 0xFF4B6CB7 to 0xFF182848
        desc != null && (desc.contains("雨")) ->
            if (night) 0xFF16222A to 0xFF3A6073 else 0xFF5B86E5 to 0xFF36D1DC
        desc != null && (desc.contains("雪") || desc.contains("冰")) ->
            if (night) 0xFF232526 to 0xFF414345 else 0xFF83A4D4 to 0xFFB6FBFF
        desc != null && (desc.contains("雾") || desc.contains("霾") || desc.contains("沙") || desc.contains("尘")) ->
            if (night) 0xFF2C3E50 to 0xFF4CA1AF else 0xFF9796F0 to 0xFFFBC7D4
        desc != null && desc.contains("阴") ->
            if (night) 0xFF141E30 to 0xFF243B55 else 0xFF757F9A to 0xFFD7DDE8
        desc != null && desc.contains("多云") ->
            if (night) 0xFF0F2027 to 0xFF2C5364 else 0xFF56A7E8 to 0xFF8EC9F5
        else -> // 晴
            if (night) 0xFF0F2027 to 0xFF203A43 else 0xFF4A90E2 to 0xFFF5AF19
    }
}
