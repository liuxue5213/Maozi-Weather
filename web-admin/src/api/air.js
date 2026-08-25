import request from './request'

export function getAirQuality(cityId, latitude, longitude) {
  return request({
    url: `/weather/air_quality/${cityId}`,
    params: { latitude, longitude },
  })
}

export function getLifeIndex(cityId, params) {
  return request({
    url: `/weather/life_index/${cityId}`,
    params,
  })
}

export function getSunriseSunset(cityId, params) {
  return request({
    url: `/weather/sun/${cityId}`,
    params,
  })
}

export function calculateAqi(params) {
  return request({
    url: `/weather/aqi/calculate`,
    params,
  })
}
