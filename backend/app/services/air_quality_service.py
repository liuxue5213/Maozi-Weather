"""
空气质量 & 生活指数 服务

包含：
- AQI 计算与等级判定
- 生活指数计算（穿衣、洗车、运动、紫外线等）
- 日出日落时间计算
"""
import math
from datetime import datetime


# ===== AQI 计算 =====

# AQI 分级标准（GB 3095-2012）
AQI_LEVELS = [
    (0, 50, "优", "绿色"),
    (51, 100, "良", "黄色"),
    (101, 150, "轻度污染", "橙色"),
    (151, 200, "中度污染", "红色"),
    (201, 300, "重度污染", "紫色"),
    (301, 500, "严重污染", "褐红色"),
]

# 污染物浓度限值（μg/m³，CO为mg/m³）
POLLUTANT_BREAKPOINTS = {
    "pm25": [(0, 35, 0, 50), (35, 75, 50, 100), (75, 115, 100, 150),
             (115, 150, 150, 200), (150, 250, 200, 300), (250, 500, 300, 500)],
    "pm10": [(0, 50, 0, 50), (50, 150, 50, 100), (150, 250, 100, 150),
             (250, 350, 150, 200), (350, 420, 200, 300), (420, 600, 300, 500)],
    "so2": [(0, 50, 0, 50), (50, 150, 50, 100), (150, 475, 100, 150),
            (475, 800, 150, 200), (800, 1600, 200, 300), (1600, 2620, 300, 500)],
    "no2": [(0, 40, 0, 50), (40, 80, 50, 100), (80, 180, 100, 150),
            (180, 280, 150, 200), (280, 565, 200, 300), (565, 940, 300, 500)],
    "co": [(0, 2, 0, 50), (2, 4, 50, 100), (4, 14, 100, 150),
           (14, 24, 150, 200), (24, 36, 200, 300), (36, 60, 300, 500)],
    "o3": [(0, 100, 0, 50), (100, 160, 50, 100), (160, 215, 100, 150),
           (215, 265, 150, 200), (265, 800, 200, 300), (800, 1200, 300, 500)],
}


def calculate_iaqi(pollutant: str, concentration: float) -> int:
    """计算单项污染物的 IAQI"""
    if concentration is None or pollutant not in POLLUTANT_BREAKPOINTS:
        return 0

    for bp_lo, bp_hi, iaqi_lo, iaqi_hi in POLLUTANT_BREAKPOINTS[pollutant]:
        if bp_lo <= concentration <= bp_hi:
            iaqi = ((iaqi_hi - iaqi_lo) / (bp_hi - bp_lo)) * (concentration - bp_lo) + iaqi_lo
            return round(iaqi)

    return 500


def calculate_aqi(pm25=None, pm10=None, so2=None, no2=None, co=None, o3=None) -> dict:
    """
    计算 AQI（取各 IAQI 最大值）

    Returns:
        dict: {aqi, level, primary}
    """
    iaqi_values = {
        "pm25": calculate_iaqi("pm25", pm25),
        "pm10": calculate_iaqi("pm10", pm10),
        "so2": calculate_iaqi("so2", so2),
        "no2": calculate_iaqi("no2", no2),
        "co": calculate_iaqi("co", co),
        "o3": calculate_iaqi("o3", o3),
    }

    valid_iaqi = {k: v for k, v in iaqi_values.items() if v > 0}

    if not valid_iaqi:
        return {"aqi": None, "level": None, "primary": None}

    primary = max(valid_iaqi, key=valid_iaqi.get)
    aqi = valid_iaqi[primary]

    level = "未知"
    for lo, hi, name, _ in AQI_LEVELS:
        if lo <= aqi <= hi:
            level = name
            break

    primary_names = {
        "pm25": "PM2.5",
        "pm10": "PM10",
        "so2": "SO₂",
        "no2": "NO₂",
        "co": "CO",
        "o3": "O₃",
    }

    return {
        "aqi": aqi,
        "level": level,
        "primary": primary_names.get(primary, primary),
    }


# ===== 生活指数计算 =====

def calc_clothing_index(temperature: float) -> dict:
    """穿衣指数"""
    if temperature >= 30:
        return {"level": "炎热", "desc": "建议穿短袖、裙子、短裤等夏季服装"}
    elif temperature >= 25:
        return {"level": "舒适", "desc": "建议穿单层棉麻面料的短套装、T恤衫等"}
    elif temperature >= 20:
        return {"level": "温暖", "desc": "建议穿单层棉麻面料的衬衫、薄长裙等"}
    elif temperature >= 15:
        return {"level": "较舒适", "desc": "建议穿套装、夹衣、风衣、休闲装等"}
    elif temperature >= 10:
        return {"level": "较冷", "desc": "建议穿风衣、大衣、夹毛衣等"}
    elif temperature >= 5:
        return {"level": "冷", "desc": "建议穿棉衣、冬大衣、厚毛衣等"}
    elif temperature >= 0:
        return {"level": "很冷", "desc": "建议穿厚棉衣、羽绒服、手套等"}
    else:
        return {"level": "寒冷", "desc": "建议穿厚羽绒服、毛皮大衣、厚手套等"}


def calc_car_wash_index(temperature: float, precipitation: float = 0, wind_speed: float = 0) -> dict:
    """洗车指数"""
    if precipitation and precipitation > 0:
        return {"level": "不宜", "desc": "有降水，车辆容易弄脏，不建议洗车"}
    elif temperature < 0:
        return {"level": "不宜", "desc": "温度低于0℃，洗车水易结冰，不建议洗车"}
    elif wind_speed and wind_speed > 5:
        return {"level": "较不宜", "desc": "风大容易扬尘，洗车后易脏"}
    elif temperature < 5:
        return {"level": "较不宜", "desc": "温度较低，洗车后易结冰"}
    else:
        return {"level": "适宜", "desc": "天气晴好，适宜洗车"}


def calc_sport_index(temperature: float, humidity: float = 50, aqi: int = 50) -> dict:
    """运动指数"""
    if aqi and aqi > 200:
        return {"level": "不宜", "desc": "空气质量差，不建议户外运动"}
    elif aqi and aqi > 150:
        return {"level": "较不宜", "desc": "轻度以上污染，减少户外运动"}
    elif temperature > 35:
        return {"level": "不宜", "desc": "气温过高，容易中暑，避免户外运动"}
    elif temperature < -10:
        return {"level": "不宜", "desc": "气温过低，容易冻伤，避免户外运动"}
    elif temperature > 30:
        return {"level": "较适宜", "desc": "气温较高，注意防暑，选择早晚运动"}
    elif temperature < 5:
        return {"level": "较适宜", "desc": "气温较低，注意保暖，充分热身"}
    elif humidity and humidity > 80:
        return {"level": "较适宜", "desc": "湿度大，体感闷热，注意补水"}
    else:
        return {"level": "适宜", "desc": "天气舒适，适宜户外运动"}


def calc_uv_index(uv: float) -> dict:
    """紫外线指数"""
    if uv >= 11:
        return {"level": "极强", "desc": "紫外线极强，尽量避免外出，必须外出需全面防护"}
    elif uv >= 8:
        return {"level": "很强", "desc": "紫外线很强，避免10-16点外出，做好全面防护"}
    elif uv >= 6:
        return {"level": "强", "desc": "紫外线强，外出需戴帽子、太阳镜，涂SPF30+防晒霜"}
    elif uv >= 3:
        return {"level": "中等", "desc": "紫外线中等，外出适当防护，涂SPF15+防晒霜"}
    else:
        return {"level": "弱", "desc": "紫外线弱，基本无需防护"}


def calc_travel_index(temperature: float, precipitation: float = 0, wind_speed: float = 0, aqi: int = 50) -> dict:
    """旅游指数"""
    if precipitation and precipitation > 10:
        return {"level": "不宜", "desc": "有强降水，不建议外出旅游"}
    elif aqi and aqi > 200:
        return {"level": "不宜", "desc": "空气质量差，不建议外出旅游"}
    elif temperature > 38 or temperature < -15:
        return {"level": "不宜", "desc": "极端温度，不建议外出旅游"}
    elif precipitation and precipitation > 0:
        return {"level": "较适宜", "desc": "有降水，出行请带雨具"}
    elif aqi and aqi > 100:
        return {"level": "较适宜", "desc": "空气质量一般，敏感人群注意防护"}
    elif 15 <= temperature <= 25:
        return {"level": "适宜", "desc": "温度适宜，天气晴好，非常适合旅游"}
    else:
        return {"level": "适宜", "desc": "天气条件较好，适宜旅游"}


def calc_all_life_indices(temperature: float, humidity: float = 50,
                          precipitation: float = 0, wind_speed: float = 0,
                          uv: float = 5, aqi: int = 50) -> list[dict]:
    """
    计算所有生活指数

    Returns:
        list[dict]: 各项生活指数，字段名与 LifeIndexOut  schema 对齐
    """
    indices = []

    clothing = calc_clothing_index(temperature)
    indices.append({"index_type": "clothing", "index_name": "穿衣指数", **clothing})

    car_wash = calc_car_wash_index(temperature, precipitation, wind_speed)
    indices.append({"index_type": "car_wash", "index_name": "洗车指数", **car_wash})

    sport = calc_sport_index(temperature, humidity, aqi)
    indices.append({"index_type": "sport", "index_name": "运动指数", **sport})

    uv_index = calc_uv_index(uv)
    indices.append({"index_type": "uv", "index_name": "紫外线指数", **uv_index})

    travel = calc_travel_index(temperature, precipitation, wind_speed, aqi)
    indices.append({"index_type": "travel", "index_name": "旅游指数", **travel})

    return indices


# ===== 日出日落计算 =====

def calc_sunrise_sunset(latitude: float, longitude: float, date: datetime = None) -> dict:
    """
    计算日出日落时间

    使用简化算法（基于太阳赤纬和时角）

    Args:
        latitude: 纬度
        longitude: 经度
        date: 日期（默认今天）

    Returns:
        dict: {sunrise, sunset, daylight_hours}
    """
    if date is None:
        date = datetime.now()

    # 计算一年中的第几天
    day_of_year = date.timetuple().tm_yday

    # 太阳赤纬（简化公式）
    declination = 23.45 * math.sin(math.radians((360 / 365) * (day_of_year - 81)))

    # 时角
    lat_rad = math.radians(latitude)
    dec_rad = math.radians(declination)

    # 日出时角
    cos_omega = -math.tan(lat_rad) * math.tan(dec_rad)

    # 处理极昼极夜
    if cos_omega > 1:
        return {"sunrise": None, "sunset": None, "daylight_hours": 0}  # 极夜
    elif cos_omega < -1:
        return {"sunrise": None, "sunset": None, "daylight_hours": 24}  # 极昼

    omega = math.degrees(math.acos(cos_omega))

    # 日出日落时间（UTC小时）
    sunrise_utc = 12 - (omega / 15)
    sunset_utc = 12 + (omega / 15)

    # 转换为本地时间（经度修正）
    sunrise_local = sunrise_utc + longitude / 15
    sunset_local = sunset_utc + longitude / 15

    # 规范化到 0-24 范围
    sunrise_local = sunrise_local % 24
    sunset_local = sunset_local % 24

    # 转换为时分
    sunrise_hour = int(sunrise_local)
    sunrise_min = int((sunrise_local - sunrise_hour) * 60)
    sunset_hour = int(sunset_local)
    sunset_min = int((sunset_local - sunset_hour) * 60)

    daylight_hours = sunset_utc - sunrise_utc

    return {
        "sunrise": f"{sunrise_hour:02d}:{sunrise_min:02d}",
        "sunset": f"{sunset_hour:02d}:{sunset_min:02d}",
        "daylight_hours": round(daylight_hours, 1),
    }
