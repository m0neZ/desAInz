Welcome to desAInz's documentation!
===================================

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   README
   configuration
   architecture
   marketplace_file_sizes
   blueprints/DesignIdeaEngineCompleteBlueprint
   admin_dashboard_trpc
   staging_manual_qa
   migrations
   privacy
   backup
   api/modules
   quickstart
   deployment
   cloud_deployment
   troubleshooting
   error_triage
   blueprints/DesignIdeaEngineCompleteBlueprint
   admin_dashboard_trpc
   load_testing
   mocking
   maintenance
   listing_sync
   publish_tasks
   i18n
   security
   roles
   daily_summary
   feature-flags
   openapi_specs
   logs_with_loki

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
