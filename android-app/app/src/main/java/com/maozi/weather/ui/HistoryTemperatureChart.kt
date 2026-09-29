package com.maozi.weather.ui

import androidx.compose.foundation.Canvas
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.graphics.nativeCanvas
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.maozi.weather.data.model.WeatherHistory
import kotlin.math.max

private val HIGH_COLOR = Color(0xFFF56C6C)
private val LOW_COLOR = Color(0xFF409EFF)
private val PRECIP_COLOR = Color(0x5542A5F5)
private val LABEL_COLOR = android.graphics.Color.parseColor("#909399")

/**
 * 历史每日最高/最低温双折线 + 降水柱 Canvas 图表。
 * X 轴为日期（每天标注起点日期，最多标注 6 个），双 Y 温度线，底部降水柱。
 */
@Composable
fun HistoryTemperatureChart(
    history: List<WeatherHistory>,
    modifier: Modifier = Modifier,
) {
    if (history.size < 2) return
    val ordered = history.sortedBy { it.date }
    val density = LocalDensity.current
    val labelPx = with(density) { 9.sp.toPx() }
    val strokePx = with(density) { 2.dp.toPx() }

    val highs = ordered.map { it.tempMax?.toFloat() }
    val lows = ordered.map { it.tempMin?.toFloat() }
    val precips = ordered.map { (it.precipitation ?: 0.0).toFloat() }
    val valid = (highs + lows).filterNotNull()
    if (valid.size < 2) return
    val tempLo = valid.min() - 1f
    val tempHi = max(valid.max(), tempLo + 2f)
    val maxPrecip = max(precips.max(), 0.5f)

    Canvas(
        modifier = modifier
            .fillMaxWidth()
            .height(160.dp),
    ) {
        val left = 16.dp.toPx()
        val right = size.width - 16.dp.toPx()
        val top = 24.dp.toPx()
        val bottom = size.height - 28.dp.toPx()
        val chartH = bottom - top
        val stepX = (right - left) / (ordered.size - 1)

        fun xPos(i: Int) = left + stepX * i
        fun yPos(t: Float) = top + (tempHi - t) / (tempHi - tempLo) * chartH

        val textPaint = android.graphics.Paint().apply {
            isAntiAlias = true
            color = LABEL_COLOR
            textSize = labelPx
            textAlign = android.graphics.Paint.Align.CENTER
        }

        // ---- 降水柱（底部 30%）----
        val barBase = bottom
        val barArea = chartH * 0.30f
        val barW = stepX * 0.40f
        precips.forEachIndexed { i, p ->
            if (p > 0.05f) {
                val h = barArea * (p / maxPrecip).coerceAtMost(1f)
                drawRoundRect(
                    color = PRECIP_COLOR,
                    topLeft = Offset(xPos(i) - barW / 2, barBase - h),
                    size = androidx.compose.ui.geometry.Size(barW, h),
                    cornerRadius = androidx.compose.ui.geometry.CornerRadius(3f, 3f),
                )
            }
        }

        // ---- 双折线（最高红/最低蓝，中点贝塞尔平滑）----
        fun drawSeries(values: List<Float?>, color: Color) {
            val pts = values.mapIndexed { i, v ->
                v?.let { Offset(xPos(i), yPos(it)) }
            }
            val path = Path()
            var started = false
            for (i in 1 until pts.size) {
                val prev = pts[i - 1] ?: continue
                val cur = pts[i] ?: continue
                if (!started) {
                    path.moveTo(prev.x, prev.y)
                    started = true
                }
                val midX = (prev.x + cur.x) / 2f
                path.cubicTo(midX, prev.y, midX, cur.y, cur.x, cur.y)
            }
            drawPath(path, color, style = Stroke(width = strokePx, cap = StrokeCap.Round))
            // 数据点
            pts.filterNotNull().forEach { drawCircle(color, radius = 4f, center = it) }
        }
        drawSeries(highs, HIGH_COLOR)
        drawSeries(lows, LOW_COLOR)

        // ---- 首末温度标注 ----
        val firstHigh = highs.firstOrNull { it != null }
        val lastHigh = highs.lastOrNull { it != null }
        if (firstHigh != null) {
            val idx = highs.indexOfFirst { it != null }
            drawContext.canvas.nativeCanvas.drawText(
                "${firstHigh.toInt()}°", xPos(idx), yPos(firstHigh) - 10.dp.toPx(), textPaint,
            )
        }
        if (lastHigh != null && lastHigh != firstHigh) {
            val idx = highs.indexOfLast { it != null }
            drawContext.canvas.nativeCanvas.drawText(
                "${lastHigh.toInt()}°", xPos(idx), yPos(lastHigh) - 10.dp.toPx(), textPaint,
            )
        }

        // ---- 日期标注（等间隔最多 6 个）----
        val labelStep = max(1, ordered.size / 6)
        ordered.forEachIndexed { i, h ->
            if (i % labelStep == 0 || i == ordered.size - 1) {
                val label = h.date.takeLast(5) // MM-dd
                drawContext.canvas.nativeCanvas.drawText(label, xPos(i), size.height - 8.dp.toPx(), textPaint)
            }
        }

        // ---- 基线 ----
        drawLine(Color(0x33C0C4CC), Offset(left, bottom), Offset(right, bottom), 1.5f)
    }
}
