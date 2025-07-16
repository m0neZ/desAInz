Manual Publishing Controls
==========================

The marketplace publisher exposes additional API endpoints for manual
intervention. Administrators can edit a publish task's metadata before it is
processed and re-trigger the workflow if necessary. All overrides are stored in
an audit log for traceability.

* ``GET /tasks`` – list existing publish tasks.
* ``PUT /tasks/{task_id}`` – replace task metadata and reset its status.
* ``POST /tasks/{task_id}/retry`` – enqueue the task for publishing again.
