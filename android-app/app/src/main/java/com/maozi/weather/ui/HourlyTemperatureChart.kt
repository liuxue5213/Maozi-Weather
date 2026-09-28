package com.maozi.weather.ui

import androidx.compose.foundation.Canvas
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.graphics.nativeCanvas
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.maozi.weather.data.model.WeatherForecast
import java.time.LocalDateTime
import java.time.format.DateTimeFormatter
import kotlin.math.max
import kotlin.math.min

private val CURVE_COLOR = Color(0xFFF56C6C)
private val FILL_COLOR = Color(0x1FF56C6C)
private val BAR_COLOR = Color(0x6642A5F5)
private val LABEL_COLOR = android.graphics.Color.parseColor("#909399")
private val AXIS_COLOR = Color(0xFFC0C4CC)

/**
 * 24 小时温度曲线 + 降水柱状 Canvas 图表（无第三方库）。
 * 横轴逐小时，主曲线为温度，底部浅蓝柱为降水量，每 3 小时标注时刻与温度。
 */
@Composable
fun HourlyTemperatureChart(
    hourly: List<WeatherForecast>,
    modifier: Modifier = Modifier,
) {
    if (hourly.size < 2) return
    val density = LocalDensity.current
    val labelPx = with(density) { 10.sp.toPx() }
    val strokePx = with(density) { 2.5.dp.toPx() }

    val temps = hourly.map { it.temperature?.toFloat() ?: 0f }
    // 降水柱按降水概率（0-100 → 0-1）绘制
    val precips = hourly.map { ((it.pop ?: it.precipitation ?: 0.0) / 100.0).toFloat().coerceIn(0f, 1f) }
    val tempLo = (temps.minOrNull() ?: 0f) - 1f
    val tempHi = max(temps.maxOrNull() ?: 0f, tempLo + 2f)
    val maxPrecip = max(precips.maxOrNull() ?: 0.1f, 0.1f)

    Canvas(
        modifier = modifier
            .fillMaxWidth()
            .height(150.dp),
    ) {
        val left = 12.dp.toPx()
        val right = size.width - 12.dp.toPx()
        val top = 26.dp.toPx()
        val bottom = size.height - 30.dp.toPx()
        val chartH = bottom - top
        val stepX = (right - left) / (hourly.size - 1)

        fun xPos(i: Int) = left + stepX * i
        fun yPos(t: Float) = top + (tempHi - t) / (tempHi - tempLo) * chartH

        val textPaint = android.graphics.Paint().apply {
            isAntiAlias = true
            color = LABEL_COLOR
            textSize = labelPx
            textAlign = android.graphics.Paint.Align.CENTER
        }

        // ---- 降水柱（底部 30% 区域，隐藏坐标：高度按 mm 归一化）----
        val barBase = bottom
        val barArea = chartH * 0.35f
        val barW = stepX * 0.42f
        hourly.forEachIndexed { i, _ ->
            val p = precips[i]
            if (p > 0.02f) {
                val h = barArea * min(p / maxPrecip, 1f)
                drawRoundRect(
                    color = BAR_COLOR,
                    topLeft = Offset(xPos(i) - barW / 2, barBase - h),
                    size = androidx.compose.ui.geometry.Size(barW, h),
                    cornerRadius = androidx.compose.ui.geometry.CornerRadius(4f, 4f),
                )
            }
        }

        // ---- 温度平滑曲线（中点三次贝塞尔）----
        val points = temps.mapIndexed { i, t -> Offset(xPos(i), yPos(t)) }
        val path = Path().apply {
            moveTo(points[0].x, points[0].y)
            for (i in 1 until points.size) {
                val prev = points[i - 1]
                val cur = points[i]
                val midX = (prev.x + cur.x) / 2f
                cubicTo(midX, prev.y, midX, cur.y, cur.x, cur.y)
            }
        }
        // 曲线下方渐变填充
        val fillPath = Path().apply {
            addPath(path)
            lineTo(points.last().x, bottom)
            lineTo(points.first().x, bottom)
            close()
        }
        drawPath(fillPath, FILL_COLOR)
        drawPath(path, CURVE_COLOR, style = Stroke(width = strokePx))

        // ---- 数据点与标注（每 3 小时）----
        points.forEachIndexed { i, p ->
            if (i % 3 == 0 || i == points.size - 1) {
                drawCircle(CURVE_COLOR, radius = 5f, center = p)
                drawCircle(Color.White, radius = 2.5f, center = p)
                // 温度标注
                drawContext.canvas.nativeCanvas.drawText(
                    "${temps[i].toInt()}°",
                    p.x,
                    (p.y - 12.dp.toPx()).coerceAtLeast(top - 4.dp.toPx()),
                    textPaint,
                )
            }
        }

        // ---- 时刻标注（每 3 小时）----
        val hourFmt = DateTimeFormatter.ofPattern("HH时")
        hourly.forEachIndexed { i, h ->
            if (i % 3 == 0 || i == points.size - 1) {
                val label = h.forecastTime?.let {
                    runCatching { LocalDateTime.parse(it.take(19)).format(hourFmt) }.getOrNull()
                } ?: ""
                drawContext.canvas.nativeCanvas.drawText(label, xPos(i), size.height - 10.dp.toPx(), textPaint)
            }
        }

        // ---- 基线 ----
        drawLine(
            AXIS_COLOR,
            Offset(left, bottom),
            Offset(right, bottom),
            strokeWidth = 1.5f,
        )
    }
}
