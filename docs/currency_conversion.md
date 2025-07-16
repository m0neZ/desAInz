# Currency Conversion

Prices for marketplace listings may be displayed in different currencies. The
`CurrencyConverter` class provides utilities for converting amounts using
exchange rates stored in Redis.

Exchange rates are refreshed periodically from a remote API and cached under the
`exchange_rates` key. Conversions round to two decimal places using the
``ROUND_HALF_UP`` strategy to ensure totals match marketplace expectations.
