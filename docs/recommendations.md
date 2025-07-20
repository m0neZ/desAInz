# Recommendations API

The `/recommendations` endpoint exposes the top optimization actions generated
from collected metrics. The service evaluates CPU, memory and disk usage trends
and returns up to three prioritized suggestions.

```bash
curl http://localhost:8000/recommendations
```

The response is a JSON array of strings. Use this endpoint to automate cost
saving notifications or integrate results into monitoring dashboards.
