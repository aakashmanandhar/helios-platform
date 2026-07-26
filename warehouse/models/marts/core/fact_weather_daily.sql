select
    region_code as warehouse_code,
    forecast_date,
    temperature,
    temperature_unit,
    short_forecast,
    wind_speed
from {{ ref('stg_weather_daily') }}
