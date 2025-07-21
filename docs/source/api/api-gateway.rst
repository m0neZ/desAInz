API Gateway HTTP API
====================

``GET /trending``
    Return the most popular keywords observed by the ingestion service.

Example request using ``requests``:

.. code-block:: python

   import requests

   base_url = "https://api.example.com"
   response = requests.get(f"{base_url}/trending", timeout=10)
   response.raise_for_status()
   print(response.json())
