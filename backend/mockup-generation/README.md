# Mockup Generation Service

This service generates design mockups using Stable Diffusion XL. It exposes Celery tasks for asynchronous generation and provides a post-processing pipeline.

## Environment Variables

Copy `.env.example` to `.env` and adjust the values.

Set `USE_COMFYUI=true` to delegate image generation to an external ComfyUI
instance. The service will send workflow JSON to `COMFYUI_URL` (default
`http://localhost:8188`). A compatible Docker image is available at
`ghcr.io/comfyanonymous/comfyui:latest` and must be running alongside the
service when this option is enabled.
