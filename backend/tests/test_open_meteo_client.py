"""Open-Meteo 客户端归一化函数单元测试。

重点回归：实况 wind_direction 必须输出中文风向文本（曾因输出数字角度
导致 App 端 kotlinx.serialization 反序列化失败 → 详情页「获取天气失败」）。
"""
from app.utils.open_meteo_client import OpenMeteoClient, wind_dir_to_text


def test_wind_dir_to_text_basic():
    assert wind_dir_to_text(0) == "北"
    assert wind_dir_to_text(45) == "东北"
    assert wind_dir_to_text(90) == "东"
    assert wind_dir_to_text(303) == "西北"
    assert wind_dir_to_text(360) == "北"


def test_wind_dir_to_text_none_and_garbage():
    assert wind_dir_to_text(None) is None
    assert wind_dir_to_text("abc") is None


def _current_payload():
    return {
        "current": {
            "time": "2026-09-13T23:00",
            "temperature_2m": 21.6,
            "apparent_temperature": 20.8,
            "relative_humidity_2m": 46,
            "surface_pressure": 1020.8,
            "wind_speed_10m": 4.3,
            "wind_direction_10m": 303,
            "precipitation": 0.0,
            "weather_code": 0,
        }
    }


def test_normalize_current_weather_wind_direction_is_text():
    r = OpenMeteoClient.normalize_current_weather(_current_payload(), city_id=89)
    assert r is not None
    assert r["wind_direction"] == "西北"  # 回归：绝不能是 303 这类数字
    assert r["temperature"] == 21.6
    assert r["weather_desc"] == "晴"
    assert r["data_source"] == "Open-Meteo"


def test_normalize_current_weather_empty_payload():
    assert OpenMeteoClient.normalize_current_weather({}, city_id=1) is None
    # current 为空 dict：返回结构但字段全空（行为契约：不抛异常即可）
    r = OpenMeteoClient.normalize_current_weather({"current": {}}, city_id=1)
    assert r is not None and r["temperature"] is None


def _hourly_payload():
    return {
        "hourly": {
            "time": ["2026-09-13T23:00", "2026-09-14T00:00"],
            "temperature_2m": [21.6, 20.1],
            "relative_humidity_2m": [46, 50],
            "weather_code": [0, 61],
            "precipitation": [0.0, 0.6],
            "precipitation_probability": [0, 80],
            "wind_speed_10m": [4.3, 3.1],
        }
    }


def test_normalize_hourly_forecast_emits_pop():
    items = OpenMeteoClient.normalize_hourly_forecast(_hourly_payload(), city_id=89)
    assert len(items) == 2
    assert items[0]["pop"] == 0
    assert items[1]["pop"] == 80  # 回归：pop 曾恒为 None
    assert items[1]["weather_desc"] == "小雨"


def test_normalize_hourly_forecast_empty():
    assert OpenMeteoClient.normalize_hourly_forecast({}, city_id=1) == []


def test_normalize_minutely_15():
    payload = {
        "minutely_15": {
            "time": ["2026-09-13T23:15", "2026-09-13T23:30"],
            "precipitation": [0.2, 0.0],
            "precipitation_probability": [60, 10],
        }
    }
    items = OpenMeteoClient.normalize_minutely_15(payload, city_id=89)
    assert len(items) == 2
    assert items[0]["precipitation"] == 0.2
    assert items[1]["precipitation_probability"] == 10


def test_normalize_minutely_15_empty():
    assert OpenMeteoClient.normalize_minutely_15({}, city_id=1) == []


def _daily_payload():
    return {
        "daily": {
            "time": ["2026-09-13"],
            "weather_code": [2],
            "temperature_2m_max": [26.0],
            "temperature_2m_min": [15.0],
            "precipitation_sum": [1.2],
            "wind_speed_10m_max": [5.5],
            "sunrise": ["2026-09-13T05:42"],
            "sunset": ["2026-09-13T18:20"],
        }
    }


def test_normalize_daily_forecast():
    items = OpenMeteoClient.normalize_daily_forecast(_daily_payload(), city_id=89)
    assert len(items) == 1
    d = items[0]
    assert d["temp_max"] == 26.0
    assert d["temp_min"] == 15.0
    assert d["precipitation_sum"] == 1.2
