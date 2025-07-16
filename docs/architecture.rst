Architecture
============

.. mermaid::

   graph TB
       users[Users] --> dashboard[Admin Dashboard]
       dashboard --> api[API Gateway]
       api --> template[Service Template]
       api --> mockup[Mockup Generation]
       api --> scoring[Scoring Engine]
       template --> storage[S3 Storage]
       mockup --> storage
       scoring --> storage

This diagram shows the high-level interaction between the dashboard and the
backend services.
