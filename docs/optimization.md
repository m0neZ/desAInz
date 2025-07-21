# Optimization Scheduler

The optimization service periodically computes an hourly aggregate of resource metrics.
A job managed by **APScheduler** runs `store.create_hourly_continuous_aggregate()`
every hour. The scheduler starts with the FastAPI application and shuts down when
the service stops.
