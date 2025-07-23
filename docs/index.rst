Welcome to desAInz's documentation!
===================================

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   README
   configuration
   service_settings
   architecture
   marketplace_file_sizes
   blueprints/DesignIdeaEngineCompleteBlueprint
   implementation_plan
   admin_dashboard_trpc
   frontend/index
   staging_manual_qa
   migrations
   privacy
   backup
   quickstart
   prebuilt_resources
   recommendations
   optimization
   api_gateway_sidecar
   deployment
   cloud_deployment
   troubleshooting
   error_triage
   load_testing
   mocking
   maintenance
   operations
   orchestrator
   listing_sync
   publish_tasks
   security
   roles
   daily_summary
   feature-flags
   openapi_specs
   logs_with_loki
   monitoring
   scripts
   source/index

Kafka Utilities
---------------
.. automodule:: backend.shared.kafka.utils
    :members:

.. automodule:: backend.shared.kafka.schema_registry
    :members:


Admin Dashboard
---------------
The admin dashboard is a Next.js application found in ``frontend/admin-dashboard``.
Any shared TypeScript interfaces located in this package are included in the
documentation build. The Tailwind configuration extends the default color
palette and font families to maintain consistent styling.
