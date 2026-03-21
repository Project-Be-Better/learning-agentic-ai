#### Terminal 1

```
D:\learning-projects\learning-agentic-ai\phase2-celery> celery -A tasks worker --pool=threads --loglevel=info

 -------------- celery@thommans-asus v5.6.2 (recovery)
--- ***** -----
-- ******* ---- Windows-11-10.0.26200-SP0 2026-03-21 09:54:03
- *** --- * ---
- ** ---------- [config]
- ** ---------- .> app:         tasks:0x25e78f58170
- ** ---------- .> transport:   redis://localhost:6379/0
- ** ---------- .> results:     redis://localhost:6379/0
- *** --- * --- .> concurrency: 16 (thread)
-- ******* ---- .> task events: OFF (enable -E to monitor tasks in this worker)
--- ***** -----
 -------------- [queues]
                .> celery           exchange=celery(direct) key=celery


[tasks]
  . tasks.analyse_trip

[2026-03-21 09:54:03,517: INFO/MainProcess] Connected to redis://localhost:6379/0
[2026-03-21 09:54:03,527: INFO/MainProcess] mingle: searching for neighbors
[2026-03-21 09:54:04,567: INFO/MainProcess] mingle: all alone
[2026-03-21 09:54:04,619: INFO/MainProcess] celery@thommans-asus ready.
[2026-03-21 09:54:25,698: INFO/MainProcess] Task tasks.analyse_trip[7a6f3007-814d-407e-b153-c62ff6294d73] received
[2026-03-21 09:54:25,700: WARNING/MainProcess] [safety] picking up trip trip_001...
[2026-03-21 09:54:27,701: WARNING/MainProcess] [safety] finished trip trip_001
[2026-03-21 09:54:27,730: INFO/MainProcess] Task tasks.analyse_trip[7a6f3007-814d-407e-b153-c62ff6294d73] succeeded in 2.0310000000026776s: {'trip_id': 'trip_001', 'agent': 'safety', 'status': 'done', 'score': 0.82}
```

#### Terminal 2

```
(agentic-ai) PS D:\learning-projects\learning-agentic-ai\phase2-celery> uv run python dispatch.py
Dispatching task...
Task dispatched — id: 7a6f3007-814d-407e-b153-c62ff6294d73
Waiting for result...
Result → {'trip_id': 'trip_001', 'agent': 'safety', 'status': 'done', 'score': 0.82}
(agentic-ai) PS D:\learning-projects\learning-agentic-ai\phase2-celery>
```
