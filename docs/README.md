# Documentation

The `blueprints` folder contains the full system blueprint.

- [Design Idea Engine Complete Blueprint](blueprints/DesignIdeaEngineCompleteBlueprint.md)

The `scripts` directory provides helper scripts for setting up storage and CDN resources:

- `setup_storage.sh` – create the S3/MinIO bucket structure
- `configure_cdn.sh` – create a CloudFront distribution
- `invalidate_cache.sh` – invalidate CDN caches when mockups change
