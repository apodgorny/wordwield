# Refactoring Plan: Canonical Semantic Addressing (domain|doc|chunk|idx|flags)

## Intent

Turn every sentence-vector in the system into a stable **semantic address**: one `int` that survives load/unload, FAISS rehydration, cache rebuilds, and future versioning. The system becomes a resonator: once a wave enters, every interference pattern can be reproduced from the same coordinates.

---

## Current Problems → Why They Hurt (Wave / Resonator framing)

### Problem 1: Identity drifts across load/unload
**Symptom:** After FAISS rebuild or rehydration, a vector may not carry the same identity unless a mapping table is rebuilt.  
**Why it hurts:** Your ridges and masks are “thin veins” in a heatmap; if the coordinate system shifts, the same ridge cannot be replayed. The interference pattern changes not because the wave changed, but because the axes moved.

**Solution:** Make identity a deterministic `int_id = encode(domain, doc_id, chunk_id, idx_in_doc, flags)` created at ingestion time.

---

### Problem 2: Packed ids miss `domain` and `idx_in_doc`
**Symptom:** `doc_id__chunk_id` is not fully descriptive and does not embed “time along the document” (`idx_in_doc`).  
**Why it hurts:** Exciter and Condensation are operations along the document wave. Without `idx_in_doc`, you’re forced to “look for neighbors” by logic, not by arithmetic. That turns physics into bookkeeping.

**Solution:** Append `idx_in_doc` and `flags` into the canonical `int_id`. With `idx_in_doc` as the lowest bits, windows become contiguous ranges.

---

### Problem 3: Multiple cosine implementations
**Symptom:** Semantic can compute similarity, FAISS can compute similarity, and potentially you have rotated / phase-steered variants.  
**Why it hurts:** Two cosine implementations are like two different masks: the same wave produces different interference. Tiny numeric differences become ridge boundary differences and change what you sample.

**Solution:** One canonical similarity kernel. Semantic never computes cosine directly. It requests similarity from the canonical kernel (the same physics everywhere). This kernel moves into `yo` (ё).

---

### Problem 4: The `rag_document` table duplicates identity and lifecycle
**Symptom:** `rag_document` stores `domain`, `key`, `temporary`, and `mtime` at a document level.  
**Why it hurts:** Document-level `mtime` is a coarse clock. Your system works at the sentence wave level; the clock belongs to chunks/sentences. Document-level identity is a container ontology that you’re already outgrowing.

**Solution:** Encode temporarity in `flags` (1 bit). Move `mtime` to chunk/sentence rows to enable future versioning of the wave without changing the coordinate system. Consider dropping `rag_document` or downgrading it to optional human metadata registry.

---

## Target Architecture (What Exists After Refactor)

### Canonical Key
A single `int_id` is the coordinate of a semantic atom:

- `domain`          : which resonator room
- `doc_id`          : which wave source
- `chunk_id`        : logical block boundary (coarser segmentation)
- `idx_in_doc`      : time index along the document wave (sentence order)
- `flags`           : bits for lifecycle and future switches (e.g., temporary)

**Property:** The same sentence-vector always has the same `int_id`.

---

### Roles (Clean separation)

#### `Semantic`
A pure converter: `text → sentences → vectors` plus Exciter/Condensation orchestration.  
It holds `id ↔ text` correspondence in memory and uses the canonical similarity kernel.

#### FAISS (domain index)
An accelerator: stores vectors and returns ids. It does not define truth; it reflects it.

#### SQLite
A fact store: stores `int_id`, sentence text, and time metadata (`mtime`) per sentence/chunk for future versioning.

#### `yo` (ё)
Physics: Exciter, Condensation, canonical similarity kernels.  
WordWield orchestrates; `yo` computes interference.

---

## Data Model Changes (SQLite)

### New/Updated table: sentence atoms
Store the minimum facts needed to replay the wave.

Fields (suggested):
- `id`        : INTEGER PRIMARY KEY (canonical `int_id`)
- `text`      : TEXT (sentence text)
- `mtime`     : INTEGER (chunk/sentence modification time)
- `meta`      : optional JSON/TEXT (if needed later)

Optional indexes:
- `mtime`
- If you must query ranges: store `doc_base_id` or decode on the fly; the goal is to use `id` as the perfect hash.

**Goal:** Retrieval by `id` is O(1) and stable.

---

## Encoding Layout (Bit allocation strategy)

### Constraints
- Must be stable forever (ABI of the system).
- Must allow:
  - domain separation
  - deterministic doc identity
  - contiguous ranges by `idx_in_doc` (optimization)
  - flags bit(s) (temporary)

### Layout principle
Put `idx_in_doc` in the lowest bits to make windows contiguous:
- A local excitation window around a sentence becomes `[id - r, id + r]` by arithmetic.
- Condensation can scan the wave in increasing id order.

Flags can live in the lowest bits too, but then contiguity is broken. Better:
- Reserve the lowest bits for `idx_in_doc`.
- Put `flags` above `idx_in_doc`, or keep `flags` at the top and expose them by masking.

**Result:** Neighborhood operations are pure integer arithmetic.

---

## Optimization Opportunities Opened by `idx_in_doc` (The “Guess which?” list)

### 1) Exciter becomes a range generator
Instead of “find neighbors”:
- Input: `center_id`, `radius`
- Output: `id_range = [center_id - radius, center_id + radius]`

No joins. No lookups. Just arithmetic.

### 2) Condensation becomes a scan along the document wave
Carrier update and inertia curves become a single pass over increasing `id`:
- Stable order guaranteed by `idx_in_doc` bits.
- Rewind/replay is deterministic: the same scan reproduces the same ridges.

### 3) Bulk FAISS fetch and cache locality
With contiguous ranges:
- prefetch vectors for a window in one call
- coalesced memory access patterns
- fewer random reads

This is hardware-friendly “wave propagation”, not “vector scavenging”.

### 4) Persistent ridges as address lists
Ridges can be stored as lists of `int_id`:
- saved today
- rehydrated tomorrow
- replayed without recomputing identity

---

## Refactoring Steps (Phased Plan)

### Phase 0: Freeze the physics ABI
**Problem:** If you change encode/decode later, stored ids become meaningless.  
**Solution:** Version the `encode` layout in code and in stored metadata (single constant). Once published, it is treated like a law of the system.

Deliverables:
- `encode(...)` and `decode(...)` defined and tested
- a single integer space reserved for `domain`, `doc_id`, `chunk_id`, `idx_in_doc`, `flags`

---

### Phase 1: Ingestion assigns canonical ids
**Problem:** ids currently depend on FAISS or post-hoc mapping.  
**Solution:** At document add-time in RAG service:
1. compute `doc_id` deterministically from `(domain, key)` or another stable scheme
2. sentencize
3. assign `idx_in_doc` for each sentence
4. compute `int_id` for each sentence
5. store `id ↔ text` and `mtime` in SQLite
6. add vectors to FAISS under the same `id`

Deliverables:
- A single ingest pipeline that produces stable ids
- SQLite contains all ids for replay and rehydration

---

### Phase 2: Semantic becomes purely semantic (and uses yo physics)
**Problem:** Semantic currently owns encoder and may compute things locally.  
**Solution:** Keep Semantic as a converter and orchestrator:
- it maintains `id ↔ text` in memory
- vectors are fetched by `id` (from FAISS) when needed
- similarity and excitation are computed through `yo` kernels

Deliverables:
- Semantic does not implement cosine
- Exciter/Condensation entry points exist but delegate to `yo`

---

### Phase 3: Canonical similarity everywhere
**Problem:** multiple cosine paths cause different ridges.  
**Solution:** One kernel, one place:
- `yo.cossim(...)` (and later `yo.cossim_rot(...)` / phase-steered variants) define the law
- FAISS usage is aligned with this law:
  - either normalize vectors identically
  - or route similarity requests through the same kernel when doing re-ranking / second attention

Deliverables:
- Unit tests: `yo.cossim(a,b)` matches FAISS scoring under the same normalization regime
- No duplicate cosine code paths

---

### Phase 4: Drop or downgrade `rag_document`
**Problem:** It duplicates identity and lifecycle.  
**Solution options:**
- **Option A (hard drop):** remove `rag_document` entirely; document is a range of ids
- **Option B (soft keep):** keep a tiny registry only for human-facing metadata (`domain`, `key`, created), but not required for semantic addressing

Move:
- `temporary` → `flags` bit
- `mtime` → sentence/chunk rows

Deliverables:
- Migration script (see below)
- System runs without `rag_document` dependency

---

## Migration Plan (Safe and Reproducible)

### Step 1: Add new schema alongside old
- create new table for sentence atoms keyed by `id`
- keep old tables temporarily

### Step 2: Backfill ids for existing data
For each old document:
- decode its identity (`domain`, `doc_id`, `chunk_id`)
- compute `idx_in_doc` from sentence order
- compute new `int_id`
- write rows: `(id, text, mtime)`
- reinsert vectors into FAISS with the new `id`

### Step 3: Dual-read validation
During transition:
- query both old and new paths
- compare top-k seeds and ridge boundaries for a sample set
- ensure the same ridges appear when physics is identical

### Step 4: Cutover
- make new id path the default
- delete old mapping usage
- drop `rag_document` if using Option A

---

## Testing Plan (Ridge-level correctness)

### Identity invariants
- ingest → save ids
- destroy FAISS index
- rehydrate from SQLite
- search same query
- confirm returned ids match exactly

### Exciter invariants
- given a center id, radius
- ensure excited ids are contiguous and correctly bounded within doc ranges

### Condensation invariants
- run condensation twice (fresh + rehydrated)
- compare condensation curve / ridge boundaries
- must match for the same wave

### Similarity invariants
- `yo.cossim` must match the similarity used by FAISS under the same normalization assumptions
- if normalization differs, define one canonical normalization in `yo`

---

## Risks and How to Avoid Them (All in your language)

### Risk: Shifting the coordinate system later
If encode layout changes, stored ids become a different resonator.  
**Mitigation:** Treat encode/decode layout as a law; version it and keep backward compatibility if you ever extend it.

### Risk: “Inserting” sentences breaks `idx_in_doc`
If you change sentence order inside an existing doc, the wave’s time index changes.  
**Mitigation:** If you need insertion later, add versioning using `mtime` (now per sentence/chunk). A new version is a new wave; don’t rewrite the old coordinates.

### Risk: Flags in the lowest bits break contiguity
If flags occupy low bits, `[id-r, id+r]` stops being a clean window.  
**Mitigation:** Keep `idx_in_doc` as the low bits; place flags above it.

---

## Deliverables Checklist

- [ ] Canonical `encode/decode` layout fixed and tested
- [ ] Ingestion assigns `int_id` at add-time in RAG service
- [ ] `idx_in_doc` included to enable arithmetic windows
- [ ] One canonical similarity kernel in `yo`
- [ ] Semantic delegates Exciter/Condensation and similarity to `yo`
- [ ] SQLite stores `id ↔ text` and `mtime` per atom
- [ ] FAISS rehydration reproduces the same ids
- [ ] `rag_document` dropped or downgraded
- [ ] Ridge-level regression tests pass

---

## Summary (In one breath)

You’re turning the whole system into a stable resonator: the wave enters once, its interference coordinates are written as an `int`, and from then on every ridge, mask, excitation, and condensation can be replayed exactly by address, using one law of similarity in `yo`.
