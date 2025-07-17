Architecture Diagram
====================

.. mermaid::

   graph TD
       API_Gateway["API Gateway (5000)"]
       Signal_Ingestion["Signal Ingestion (5001)"]
       Scoring_Engine["Scoring Engine (5002)"]
       AI_Mockup_Generation["AI Mockup Generation (5003)"]
       Marketplace_Publisher["Marketplace Publisher (5004)"]
       Feedback_Loop["Feedback Loop (5005)"]
       Monitoring["Monitoring (5006)"]
       Optimization["Optimization (5007)"]

       API_Gateway --> Signal_Ingestion
       Signal_Ingestion --> Scoring_Engine
       Scoring_Engine --> AI_Mockup_Generation
       AI_Mockup_Generation --> Marketplace_Publisher
       Marketplace_Publisher --> Feedback_Loop
       Feedback_Loop --> Optimization
       Optimization --> Monitoring
