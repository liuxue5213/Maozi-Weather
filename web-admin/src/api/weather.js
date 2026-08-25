import request from './request'

export function getRealtime(cityId, latitude, longitude) {
  return request({
    url: `/weather/realtime/${cityId}`,
    params: { latitude, longitude },
  })
}

export function getForecast(cityId, latitude, longitude, days = 16) {
  return request({
    url: `/weather/forecast/${cityId}`,
    params: { latitude, longitude, days },
  })
}

export function getWarning(cityId, locationId) {
  const params = {}
  if (locationId) params.location_id = locationId
  return request({
    url: `/weather/warning/${cityId}`,
    params,
  })
}

export function getHistorical(cityId, latitude, longitude, startDate, endDate) {
  return request({
    url: `/weather/historical/${cityId}`,
    params: { latitude, longitude, start_date: startDate, end_date: endDate },
  })
}
