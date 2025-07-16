# API Gateway CSV Exports

Two endpoints allow downloading statistics as CSV files when authenticated with an admin role.

`/export/ab_tests` returns all A/B test results with columns `id`, `listing_id`, `variant`, and `conversion_rate`.

`/export/marketplace_stats` aggregates listings and the number of associated tests using columns `listing_id`, `price`, and `num_tests`.
