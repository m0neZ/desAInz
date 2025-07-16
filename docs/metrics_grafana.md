# Metrics and Grafana

The application records scoring results and publishing latency in ClickHouse when
`CLICKHOUSE_URL` is configured. Metrics are aggregated using `toStartOfInterval`
so they can be visualised efficiently in Grafana.

Import the JSON dashboards from `infrastructure/grafana` into Grafana to analyse
trends over time. Downsampling occurs at query time by grouping on a chosen
interval to keep storage usage minimal.
