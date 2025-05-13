# Loki Ingestion Debug Matrix & Steps Tried

This document tracks the systematic debug steps and test matrix used to diagnose Loki log ingestion issues in this project.

---

## Steps Tried (Chronological)

1. **Confirmed Loki container health** via `/ready` endpoint and Docker logs.
2. **Updated Loki config** for local development (removed invalid fields, ensured WAL/chunks dirs).
3. **Validated ingestion test** using:
   - HTTPX async push to `/loki/api/v1/push`
   - Query via `/loki/api/v1/query_range`
4. **Switched log timestamp** to nanosecond Unix time (`int(time.time() * 1_000_000_000)`).
5. **Increased query retries and window** (from 10×1s to 20×2s, then ±5s to ±60s).
6. **Added debug prints** for push/query payloads, headers, and responses.
7. **Checked for WAL/storage errors** in Loki container logs.
8. **Tested label format** as both string (`'{app="synthetic"}'`) and dict (`{"app": "synthetic"}`).
9. **Tested X-Scope-OrgID** as `"fake"`, `"default"`, and omitted.
10. **Pushed logs with unique lines** for each matrix combination.

---

## Current Test Matrix Functionality

The test `test_log_ingestion` in `_tests/test_log_ingest.py` now runs a matrix of cases:

- **OrgID Header:**
  - `"fake"`
  - `"default"`
  - omitted
- **Label Format:**
  - Loki label as string: `'{app="synthetic"}'`
  - Loki label as dict: `{ "app": "synthetic" }`
- **Query Window:**
  - ±5 seconds
  - ±60 seconds

For each combination, the test:
- Prints the full push/query payloads and responses
- Fails with a clear message if ingestion fails, indicating the combination

---

## How to Use This Debug Matrix

1. Run the test:
   ```bash
   poetry run pytest app/core/loki/_tests/test_log_ingest.py
   ```
2. Review output for which (if any) combinations succeed.
3. If all fail, check Loki container logs for WAL/storage errors or permission issues.
4. Use this matrix to inform future configuration or bugfixes.

---

## Next Steps / Recommendations
- If a single combination works, use that OrgID/label/query pattern for all log pushes.
- If none work, escalate to Loki server logs and config.
- Keep this file updated as new debug steps are attempted.
