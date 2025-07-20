Next.js Setup
=============

This page explains how the admin dashboard's Next.js project is structured and how to run it locally.

Project Structure
-----------------
The dashboard lives in ``frontend/admin-dashboard``. It uses **TypeScript** with **tRPC** for API calls and **Tailwind CSS** for styling.

Local Development
-----------------
Install dependencies with ``npm install --legacy-peer-deps`` and start the dev server:

.. code-block:: bash

   cd frontend/admin-dashboard
   npm run dev

Environment variables are loaded from ``.env.local``. See ``frontend/admin-dashboard/README.md`` for details.
