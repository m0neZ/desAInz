# Pre-built Resources

This project caches heavy machine learning models and sample datasets under
`prebuilt/` to avoid repeated network downloads. The `scripts/download_resources.py`
helper downloads the Stable Diffusion XL weights from HuggingFace and creates the
required directories if they do not exist. Set the environment variables
`MODEL_CACHE_DIR` and `DATASET_DIR` to override the default locations.
