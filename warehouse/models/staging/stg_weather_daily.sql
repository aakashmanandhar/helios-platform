select
    region_code,
    city_name,
    cast(forecast_date as date) as forecast_date,
    temperature,
    temperature_unit,
    wind_speed,
    wind_direction,
    short_forecast,
    detailed_forecast,
    cast(fetched_at as timestamp) as fetched_at
from {{ source('bronze', 'weather_daily') }}
where region_code is not null
