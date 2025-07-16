---

## **1\. Objectives & Success Metrics**

| Goal | KPI | Target |
| ----- | ----- | ----- |
| Generate high-potential design ideas | Ideas scored ≥ X in top-quartile freshness & engagement | ≥ 200/day |
| Automate mock-up creation | % ideas with at least one AI mock-up | 95 % |
| Validate via feedback loop | Ideas with statistically significant positive signal (CTR, Saves, Add-to-Cart) | 25 % |
| Time-to-publish | Ingest → live mock-up on marketplace | ≤ 2 h |

---

## **2\. High-Level Architecture**

┌──────────────────┐       ┌────────────────────┐       ┌──────────────────────┐  
│  Signal Ingestors│──────▶│  Normalization &   │──────▶│   Idea Store (DB)    │  
│  (Social, Events)│       │  Deduplication     │       │  & Vector Index      │  
└────────┬─────────┘       └─────────┬──────────┘       └─────────┬────────────┘  
         │                            │                          ▲  
         ▼                            ▼                          │  
┌──────────────────┐       ┌────────────────────┐       ┌────────┴───────────┐  
│  Scoring Engine  │◀──────│  AI Mock-up Gen.   │──────▶│   Feedback Loop    │  
│  (Batch \+ Real- )│       │  (Image & Listing) │       │  (A/B & Market)    │  
└────────┬─────────┘       └────────────────────┘       └────────┬───────────┘  
         │                            ▲                          │  
         ▼                            │                          ▼  
┌──────────────────┐       ┌────────────────────┐       ┌──────────────────────┐  
│  Orchestrator &  │──────▶│  Human Review \- UI │──────▶│  Marketplace Pushers │  
│  Job Scheduler   │       └────────────────────┘       └──────────────────────┘  
└──────────────────┘

* **Micro-services** communicate via an event bus (Kafka/Pub-Sub) for loose coupling and scalability.

* **Cold-start** (hourly) vs. **Hot** (real-time spikes via webhooks).

---

## **3\. Component Details**

### **3.1 Signal Ingestion Layer**

| Source | Method | Meta Extracted | Notes |
| ----- | ----- | ----- | ----- |
| TikTok Discover / IG Explore | Unofficial API \+ headless fallback | Hashtag, view velocity, like ratio | Headless cluster on Fargate; rotate proxies |
| Reddit r/all & niche subs | Reddit API \+ Pushshift backup | Title, subreddit, upvote/hour | Historical pulls; filter NSFW |
| YouTube Trending | Data v3 API | Thumbnail palette, title tokens | Skip comments on first pass |
| Event & Holiday Calendars | Static CSV \+ lightweight scrape | Event name, locale, date | Cache with long TTL |
| Nostalgia Archives (Wiki, TV Tropes) | Daily scrape | Topic, anniversary year | Low-frequency job |

**Normalization** into a common `Signal` schema; dedupe with a Redis Bloom filter.

### **3.2 Data Store**

* **PostgreSQL** \+ **pgvector** for metadata & embeddings.

* **S3** for mock-up binaries.

* **Redis** for hot-topic caching (TTL ≤ 48 h).

### **3.3 Scoring Engine**

**Score** `S = w₁·Freshness + w₂·Engagement + w₃·Novelty + w₄·CommunityFit + w₅·Seasonality`

| Feature | Calc | Notes |
| ----- | ----- | ----- |
| Freshness | `sigmoid(decay(hours_since_peak))` | Real-time priority |
| Engagement | `zscore(likes+comments+views per min, 7-day median)` | Normalized across sources |
| Novelty | `1 – cosine(embed, recent_centroid)` | Penalizes redundancy |
| CommunityFit | Avg(subreddit\_affinity, hashtag\_cohesion) | Pre-trained niche embeddings |
| Seasonality | `1 if within ±7 days of event else exp(-distance)` | Boosts event-aligned ideas |

*   
  Stateless containers scale based on queue length.

### **3.4 AI Mock-up Generation**

1. **Prompt Builder**

   * Grammars combine top keywords, format templates, nostalgia hooks.

2. **Generative Model**

   * **Stable Diffusion XL** fine-tuned for vector-style; AWS Batch GPU autoscaling.

   * Fallback to external APIs if necessary.

3. **Post-processing**

   * Background removal, CMYK conversion, DPI validation (300 DPI via Pillow).

4. **Listing Draft**

   * LLM generates title, bullets, tags (token cap 256).

### **3.5 Feedback Loop**

* **A/B micro-tests** via email list or low-budget ads (measure CTR).

* Hourly ingest of **marketplace metrics** (views, favorites, add-to-cart, sales).

* **Thompson Sampling** allocates promotion budget.

* Nightly online-learning update of scoring weights.

### **3.6 Orchestrator & CI/CD**

* **Temporal.io** / **Dagster** workflows with retry & approval gates.

* **GitHub Actions** → Docker → EKS with blue-green deploys.

* **Observability**: OpenTelemetry \+ Prometheus \+ Grafana \+ PagerDuty alerts.

### **3.7 UI/UX Surfaces**

* **Admin Dashboard** (Next.js \+ tRPC): signal stream, heatmap, mock-up gallery, A/B results.

* **One-click Publish**: push to Redbubble/Amazon Merch via APIs or RPA.

---

### **Core Data Model (simplified)**

erDiagram  
    SIGNAL {  
      uuid id PK  
      text content  
      source ENUM  
      captured\_at TIMESTAMP  
      metadata JSONB  
      hash CHAR(32) UNIQUE  
    }  
    IDEA ||--|| SIGNAL : derived\_from  
    IDEA {  
      uuid id PK  
      title TEXT  
      embedding VECTOR(768)  
      score FLOAT  
      status ENUM(queued, mocked, live, archived)  
      created\_at TIMESTAMP  
      updated\_at TIMESTAMP  
    }  
    MOCKUP ||--|| IDEA : for  
    MOCKUP {  
      uuid id PK  
      s3\_uri TEXT  
      variant ENUM(front, back, colorway)  
      ctr FLOAT  
    }

---

### **Performance & Cost Optimizations**

| Area | Strategy |
| ----- | ----- |
| API quotas | Stagger pulls; ETag caching; delta-only updates |
| Scoring throughput | Batch 1 000 embeddings/vector ops per GPU to maximize VRAM |
| GPU mock-ups | Spot instances \+ on-demand fallback; reuse seeds |
| Storage lifecycle | Archive mock-ups \> 12 months in Glacier/Coldline |

---

## **7\. Quality, Governance & Compliance**

* **Brand & IP Safety**:

  * Trademark check via USPTO & EUIPO APIs before publish.

  * NSFW filter (open‑source CLIP‑based) on generated images.

* **Data Privacy**:

  * Store only public social content; purge PII fields.

* **Testing**:

  * Pytest \+ FactoryBoy fixtures.

  * Contract tests for each external API; use VCR.py cassettes to keep CI fast.

* **Monitoring & Alerts**:

  * 95th‑percentile time from signal capture → mock‑up should remain under SLA; alerts via PagerDuty.

### **Key Takeaways**

* **Event‑driven micro‑services** plus a robust vector store give speed and flexibility.

* **Layered scoring** keeps the engine lean—start simple and iterate with feedback.

* **GPU‑intensive steps** are isolated behind queues so other services remain cheap and fast.

* The roadmap focuses on shipping value early (one source, one marketplace) while laying solid foundations for scale.

