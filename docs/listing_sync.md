# Listing State Synchronization

`scripts/listing_sync.py` verifies that the local database reflects the actual state of listings on the marketplace.
It periodically queries the marketplace API for each stored listing and updates the `state` column when differences are found.
Listings flagged as removed or otherwise problematic trigger a PagerDuty alert via `notify_listing_issue`.

Run the script directly or schedule it using the provided `setup_scheduler` helper:

```bash
python scripts/listing_sync.py
```
