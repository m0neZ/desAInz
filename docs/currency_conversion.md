# Currency Conversion

The marketplace publisher converts listing prices from USD to the desired currency at runtime. Exchange rates are fetched from `open.er-api.com` and cached in Redis. Rates are refreshed hourly using an `apscheduler` background scheduler.

Use `backend.shared.currency.convert_price` to convert amounts:

```python
from redis import Redis
from backend.shared.currency import convert_price

redis_client = Redis.from_url("redis://localhost:6379/0")
price_eur = convert_price(10.0, "EUR", redis_client)
```

Rounding follows typical financial rules (two decimal places, half-up).
