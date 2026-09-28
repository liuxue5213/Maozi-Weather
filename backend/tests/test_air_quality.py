"""国标 AQI 计算（GB 3095-2012）单元测试。"""
from app.services.air_quality_service import calculate_aqi


def test_clean_air_returns_level_1():
    r = calculate_aqi(pm25=5, pm10=10, so2=2, no2=5, co=0.3, o3=20)
    assert r["aqi"] <= 50
    assert r["level"] == "优"


def test_high_pm25_polluted():
    r = calculate_aqi(pm25=150)
    assert r["aqi"] >= 200
    assert "污染" in r["level"]


def test_none_inputs_returns_none_aqi():
    r = calculate_aqi()
    assert r["aqi"] is None or r["aqi"] == 0 or r["level"] is None


def test_result_has_required_keys():
    r = calculate_aqi(pm25=35, pm10=70)
    assert {"aqi", "level", "primary"} <= set(r.keys())


def test_pm25_boundary_values():
    # AQI 随 PM2.5 浓度单调上升
    good = calculate_aqi(pm25=15)
    mid = calculate_aqi(pm25=40)
    bad = calculate_aqi(pm25=100)
    assert good["aqi"] <= 50
    assert good["aqi"] < mid["aqi"] < bad["aqi"]
