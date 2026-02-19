# Codebase Optimization Plan

> Generated 2026-02-19. `agent/processor.py` pass already completed and merged to main.

## Priority Legend
- **P0** — Crash / runtime error
- **P1** — Incorrect behavior / security vulnerability
- **P2** — Performance / significant design flaw
- **P3** — Code smell / maintainability

---

## Phase 1: `tools/functions.py` (2,173 lines)

The largest file and a core dependency of the pipeline. Has a guaranteed crash bug.

| # | Pri | Line(s) | Issue |
|---|-----|---------|-------|
| 1 | P0 | 314 | `random.poisson()` does not exist — crashes at runtime. Use `numpy.random.poisson` or manual Poisson draw |
| 2 | P1 | 934 | Bare `except:` in `_calculate_timing_risk` swallows `KeyboardInterrupt`/`SystemExit` |
| 3 | P1 | 809, 1549, 1935, 1956 | Wrong dict key `merchant_id` — transactions use `merchant`. All merchant risk checks are dead code |
| 4 | P1 | 910-912 | Unreachable geographic logic — `NIGERIA`/`ROMANIA` already classified as `international_risky` before this branch |
| 5 | P1 | 1572-1578 | Double-counting sanctioned countries — creates both a CRITICAL violation and a HIGH warning for the same country |
| 6 | P2 | 449 | `from collections import Counter` imported inside hot-path method — move to module level |
| 7 | P2 | 431-567 | `_analyze_transaction_patterns` iterates transactions list 8+ times — collapse to single pass |
| 8 | P3 | 12 | Unused import: `Tuple` |
| 9 | P3 | 619-625 | Risk weights must sum to 1.0 but are not validated |
| 10 | P3 | 759+ | Magic numbers (`10000`, `5000`, `0.3`, `0.8`) scattered across risk calculation — extract constants |
| 11 | P3 | 862-878, 2073-2090, 1532-1538, 1633-1635 | Location-parsing logic duplicated 4 times — extract `_parse_location` helper |
| 12 | P3 | 1423-1428, 1511-1516, 1580-1586, 1645-1651 | Compliance status determination duplicated 4 times — extract helper |
| 13 | P3 | 243, 287 | `hashlib.md5` without `usedforsecurity=False` — fails on FIPS systems |
| 14 | P3 | 242-243, 287-288 | `random.seed()` on global state is not thread-safe — use `random.Random(seed)` instance |
| 15 | P3 | 1337 | Hardcoded `"regulation_version": "2024.1"` — extract constant |

---

## Phase 2: `dashboard/app.py` (1,041 lines)

User-facing Streamlit app with a critical XSS vulnerability.

| # | Pri | Line(s) | Issue |
|---|-----|---------|-------|
| 1 | P1 | 822-832, 889-897 | **XSS**: User-supplied Kafka data interpolated into `unsafe_allow_html=True` HTML blocks |
| 2 | P1 | 761-763 | `time.sleep(2)` blocks the entire Streamlit thread on every auto-refresh render |
| 3 | P1 | 175 | Bare `except: pass` swallows all exceptions during timestamp parsing |
| 4 | P1 | 430-451 | `random` module used but never imported — `NameError` on "Load Mock Data" |
| 5 | P1 | 320, 354 | Race condition: `self.consumers` dict written from multiple threads without locking |
| 6 | P2 | 765, 770 | Double-slicing: fetches 20 items then slices to 10 — unclear intent |
| 7 | P2 | 193-194 | `sum()` over full deque inside lock on every decision — use running total |
| 8 | P2 | 315, 352 | Inconsistent `group.id` strategy between transaction and decision consumers |
| 9 | P2 | 793-799 | `reasoning_steps` drained from queue but never displayed — dead code that discards data |
| 10 | P2 | 909 | Alert chart colors mapped by index, not by priority name — wrong colors possible |
| 11 | P3 | 312 | `import uuid` inside method — move to module level |
| 12 | P3 | 949-955 | "Global Auto-refresh" UI is disabled/dead — remove or implement |
| 13 | P3 | 281, 311+ | Mixed `print()` and `logger` usage — standardize |
| 14 | P3 | 604 | `fill='tonexty'` with single trace does nothing — use `fill='tozeroy'` |
| 15 | P3 | 487-488 | `mock_data_loaded` flag set but never read — dead code |

---

## Phase 3: `agent/rag.py` (1,065 lines)

RAG-based fraud pattern search with silent failure modes and wrong ChromaDB API usage.

| # | Pri | Line(s) | Issue |
|---|-----|---------|-------|
| 1 | P1 | 78-79, 88-90 | Silent fallback to zero-vector embeddings on API failure — corrupts collection |
| 2 | P1 | 87, 129, 289, 983, 1017 | Bare `except Exception` blocks swallow errors and return degraded results silently |
| 3 | P1 | 238 | `$contains` filter not supported by ChromaDB — silently ignored or errors |
| 4 | P1 | 258 | Wrong similarity score formula — `1 - distance` only valid for cosine, but collection uses default L2 |
| 5 | P2 | 92-99 | `__call_sync__` uses reserved dunder naming and is dead code |
| 6 | P2 | 169-188 | `asyncio.new_event_loop()` in `__init__` conflicts if called from async context |
| 7 | P2 | 79, 90, 243 | Magic number `768` for embedding dimension — will silently corrupt if model changes |
| 8 | P2 | 280 | `search_time: "async"` is a meaningless string, not actual timing |
| 9 | P3 | 11, 14 | Unused imports: `hashlib`, `uuid` |
| 10 | P3 | 343, 387, 431+ | Same hardcoded `created_at` timestamp repeated 15 times |
| 11 | P3 | 105 | Relative path default `"./chroma_db"` — unpredictable in production |
| 12 | P3 | 997 | `collection.get(limit=0)` when count is 0 — undefined behavior |

---

## Phase 4: `producer/generator.py` (627 lines)

Transaction generator with a mutation bug and rate-limiting issues.

| # | Pri | Line(s) | Issue |
|---|-----|---------|-------|
| 1 | P1 | 377 | `config.pop('topic')` mutates the caller's dict — use `config.get()` |
| 2 | P1 | 535 | Config parsing: `key, value = line.split('=', 1)` raises `ValueError` on lines without `=` |
| 3 | P1 | 408-413 | `AdminClient` constructed from mutated config (after `pop`) — may contain invalid keys |
| 4 | P1 | 517-524 | `None` env vars passed to `Producer()` before validation runs |
| 5 | P2 | 489 | `time.sleep(interval)` doesn't account for elapsed time — rate drift |
| 6 | P2 | 447, 489 | `producer.poll(0)` per-message is inefficient at high rates |
| 7 | P2 | 464-494 | Duplicate `KeyboardInterrupt` handling races with `SIGINT` handler |
| 8 | P2 | 286-287 | Off-by-one in `UNUSUAL_HOUR` vs `LATE_NIGHT` boundary |
| 9 | P2 | 308 | Transaction ID truncated to 12 hex chars — collision risk at high volume |
| 10 | P3 | 510 | `import os` / `import dotenv` inside function body |
| 11 | P3 | 304-305 | Undocumented magic numbers for risk weight distribution |
| 12 | P3 | 274-298 | Hardcoded country codes duplicated from other modules |
| 13 | P3 | 175-177 | Pre-generates 10,000 customer strings in memory at init |

---

## Phase 5: Smaller Files

### `tools/risk_analysis.py` (304 lines)

| # | Pri | Line(s) | Issue |
|---|-----|---------|-------|
| 1 | P1 | 147 | Bare `except:` in `_calculate_time_risk` |
| 2 | P1 | 239 | Bare `except:` with `continue` in `_calculate_velocity_risk` |
| 3 | P1 | 37, 216 | Naive/aware datetime mismatch — `TypeError` at runtime |
| 4 | P2 | 131-138 | Dead `else` branch — all hours already covered by preceding conditions |
| 5 | P3 | 77-259 | Magic numbers throughout — extract constants |

### `tools/notification.py` (231 lines)

| # | Pri | Line(s) | Issue |
|---|-----|---------|-------|
| 1 | P0 | 203 | `timedelta` used but not imported — `NameError` at runtime |
| 2 | P1 | 90 | Alert IDs use timestamp — duplicates under load. Use `uuid.uuid4()` |
| 3 | P2 | 180 | `flush(timeout=1.0)` per-alert blocks for up to 1s each |
| 4 | P2 | 28 | `self.alerts` list grows unboundedly — eventual OOM |
| 5 | P2 | 154-168 | `_send_kafka_alert` manually reconstructs dict that already exists |
| 6 | P2 | 212 | Bare `except:` in `get_recent_alerts` |

### `tools/fraud_detection.py` (198 lines)

| # | Pri | Line(s) | Issue |
|---|-----|---------|-------|
| 1 | P1 | 131-144 | `_check_velocity_fraud` always returns `False` — velocity detection disabled |
| 2 | P1 | 193 | Blacklist uses `user_id.endswith('999')` — demo logic never replaced |
| 3 | P2 | 58 | Bare `except:` in `check_fraud_patterns` |
| 4 | P2 | 178 | Bare `except:` in `_check_geographic_impossibility` |
| 5 | P2 | 45 | `amount == round(amount)` fragile with floats — use `amount % 1 == 0` |
| 6 | P3 | 9-16 | Duplicated merchant/country lists — share with risk_analysis.py |

### `agent/together_client.py` (218 lines)

| # | Pri | Line(s) | Issue |
|---|-----|---------|-------|
| 1 | P1 | 164 | Tool results never sent back to model (same bug we fixed in processor.py) |
| 2 | P2 | 104-106 | Unknown tool returns string instead of raising — failures invisible |
| 3 | P2 | 167 | No error handling for malformed JSON in tool arguments |
| 4 | P3 | 139 | `max_tokens=2000` hardcoded |

### `agent/consumer.py` (105 lines)

| # | Pri | Line(s) | Issue |
|---|-----|---------|-------|
| 1 | P1 | 3 | Uses `kafka-python` library while rest of codebase uses `confluent-kafka` |
| 2 | P1 | 35 | No per-message error handling — one bad message crashes the loop |
| 3 | P2 | 48 | Only `KeyboardInterrupt` caught — other exceptions kill the process |
| 4 | P2 | 80-91 | `_handle_risk_response` is a stub — detects fraud but takes no action |
| 5 | P3 | 4 | Relative import `from together_client import ...` — only works from `agent/` directory |

### `agent/rag_integration.py` (237 lines)

| # | Pri | Line(s) | Issue |
|---|-----|---------|-------|
| 1 | P0 | 176 | `List` used in type annotation but not imported — `NameError` in Python < 3.10 |
| 2 | P1 | 17-55 | `integrate_rag_with_processor()` returns `"function": None` — unusable |
| 3 | P1 | 100 | `await` on possibly-synchronous `search_fraud_patterns` — `TypeError` |
| 4 | P2 | 26-53, 72-97 | Tool definition dict copy-pasted verbatim twice |
| 5 | P3 | 196-234 | `setup_rag_integration()` is documentation disguised as code |

### `producer/transaction_generator.py` (117 lines)

| # | Pri | Line(s) | Issue |
|---|-----|---------|-------|
| 1 | P2 | 100 | `time.sleep(interval)` with 2s default — limits throughput |
| 2 | P2 | 82 | `future.get(timeout=10)` blocks per-send — defeats Kafka batching |
| 3 | P2 | 72 | Pre-baked `risk_score` in transaction — misleads downstream consumers |
| 4 | P2 | 92-93 | `count=0` treated as infinite — should be `count is not None` |
| 5 | P3 | 53, 56, 59, 64 | Magic numbers for probabilities and amount ranges |

---

## Recommended Execution Order

1. **Phase 1: `tools/functions.py`** — Largest file, P0 crash bug, core pipeline dependency
2. **Phase 2: `dashboard/app.py`** — XSS vulnerability, user-facing
3. **Phase 5a: Small tools** (`notification.py`, `risk_analysis.py`, `fraud_detection.py`) — Quick wins, several P0/P1 bugs
4. **Phase 4: `producer/generator.py`** — Mutation bug, config issues
5. **Phase 5b: Agent files** (`together_client.py`, `consumer.py`, `rag_integration.py`) — Tool-call loop bug (duplicate of processor.py fix), library mismatch
6. **Phase 3: `agent/rag.py`** — Silent failures, ChromaDB API issues (requires chromadb dependency to test)
