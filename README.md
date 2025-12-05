# WordWield Deep Dive (BE/FE, Agents, Streams, O-models)

WordWield is a builder’s playground for agentic systems: tiny, explicit, and wired for persistence. Schemas (`O`) double as Pydantic models and database rows; agents and operators are just function calls in a familiar Python runtime, backed by templates and structured outputs; streams give you a replayable timeline of every gulp of dialogue or event. Drop a file into `operators/` and it’s live via the registry. Heavy LLMs stay outside the code; you drive them with JSON schemas and prompt templates. This is the lean kit for people who want to see the machinery and invent new patterns, not fight a giant framework.

## The feel you get with WW
- **ML researchers**: a minimal sandbox to invent orchestration patterns without heavy abstractions. **Feel**: you see the machinery—registries, streams, schemas—so new patterns are easy to prototype, measure, and replay without hidden state.
- **Prompt engineers / UX**: schema-first prompting, stream-zipped dialogues, quick iteration on structured outputs. **Feel**: a writer’s workshop—sketch roles, run dialogue, replay gulps, tighten prompts with immediate, validated JSON outputs.
- **Applied ML / infra engineers**: local-first, explicit registries, DB-backed state for auditable runs. **Feel**: lightweight plumbing—callables, folders, and SQLite you control, plus explicit `ww.ask` model routing and zero boilerplate lifecycle.
- **Indie tool builders**: tiny surface area, easy to extend by dropping operators/schemas/models into folders. **Feel**: tinkerer-friendly—drop a file, it autoloads via registry, call it like a function, ship fast.
- **Data / ops teams**: replayable streams + persisted O-objects for traceability and post-hoc analysis. **Feel**: traceable runs by default; you can replay dialogues/events, inspect gulps, and audit structured state in the DB.
- **Tinkerers / hackers**: frictionless iteration—new agent file, new callable. **Feel**: immediate feedback, no boilerplate ceremony; everything stays in plain Python with structured prompts/templates when you need them.

## What WordWield Is
- A minimal agentic framework built around three pillars:
  - **O**: a Pydantic-based schema class that is also DB-persistent (via SQLAlchemy session injected at init).
  - **Operators / Agents**: callable classes (agents add LLM prompting).
  - **Streams**: append-only logs of `Gulp` entries (timestamped text), zipped/queried to model dialogue or event history.
- Registries (`ww.operators`, `ww.schemas`, `ww.models`, `ww.expertise`, `ww.config`) hold discovered classes and config.
- `ww` is a singleton (metaclass runs coroutines synchronously) you initialize once per process with `ww.init(PROJECT_NAME, PROJECT_PATH, reset_db=True/False)`.

## Bootstrapping Flow (Backend)
1) Call `ww.init(PROJECT_NAME, PROJECT_PATH, reset_db)` early in your entry point (e.g., `projects/narrative/main.py`).
2) `_setup_paths` stores project + framework paths, creates operators/schemas/models/logs/expertise dirs, and sets DB path (`<PROJECT_PATH>/<DB_NAME or project>.db`).
3) `_init_db` creates the SQLite engine/session; if `reset_db=True`, drops existing tables and recreates from ORM models.
4) `_register_builtins` imports built-in operators/schemas/models under `wordwield/`.
5) `_register_project` imports project-local operators/schemas/models under `<PROJECT_PATH>/operators|schemas|models` and loads text expertise files.
6) After init, use `ww.operators.*`, `ww.schemas.*`, `ww.models.*`, and `ww.ask(...)`.
- Auto-discovery: any new `.py` under those operator/schema/model folders is picked up on next init and addressable as `ww.operators.<ns>.<Class>` (or schemas/models accordingly).

## Server vs Client
- **Backend server (optional)**: `wordwield/web/server.py` is a minimal FastAPI app exposing `/` (HTML test) and `/ws` (echo). You can extend it to expose agent endpoints for a long-lived process that keeps heavy resources (LLM clients, embeddings, DB session) in memory.
- **No server needed**: you can run scripts/entry points directly (e.g., `python projects/narrative/main.py`) and use agents in-process.
- **Importing from “client” code**: frontend-ish scripts can import `from wordwield import ww` to call agents locally as long as they run Python and have access to the project files. If you need true browser FE, expose HTTP/WebSocket endpoints on the server and call them from the FE; otherwise, importing `ww` in client scripts is fine.

## Agents and Operators
- Base class: `ww.operators.Agent` (subclass of `Operator`). It:
  - Registers nested agents (`agents = {name: AgentClass}`) and streams (`streams = ['role1', ...]`).
  - Collects state, renders Jinja templates (`template`), and calls LLMs via `ask` with a ResponseSchema (`O` subclass).
  - Outputs are schema-validated JSON, so prompt iterations yield structured, immediately usable data.
- Example (Narrative project):
  - `projects/narrative/operators/life.py` defines `Life(Agent)` with nested `character` agent, streams per actor, and an `invoke` loop that alternates authors and writes to streams.
  - `projects/narrative/operators/narrative.py` defines a `Narrative(Project)` orchestrating many agents (`story_planner`, `character_extractor`, `scene_splitter`, etc.).
- Example (Jarvis project):
  - `projects/jarvis/operators/Orchestrator.py` (open in your IDE) is another agent orchestrator showing how to chain agents.
- Agent call pattern:
  ```python
  from wordwield import ww
  ww.init(PROJECT_NAME, PROJECT_PATH)
  result = ww.operators.Life(PROJECT_NAME)(human='Саша', actors=['Вася', 'Саша'])
  ```

## O: Dual Role (Pydantic + DB)
- `O` subclasses are Pydantic models with persistence hooks.
- Persistence is enabled by `O.enable_persistence(session)` during `ww._init_db`; models gain `.db` (ODB wrapper) to `save/delete`.
- Class helpers:
  - `put(name, **kwargs)`: upsert by name, then `set` + `save`.
  - `get(name)`, `load(ref)`, `exists`, `all(as_dict=False)`.
  - `to_jsonschema`, `to_schema_prompt`, `describe`, `schema(...)` (dynamic class factory).
  - `to_operator()`: instantiate operator named in `class_name` via registry (requires `enable_instantiation`).
- Instance helpers:
  - `set(**kwargs)`: assign (except id) and `save()`.
  - `save()`, `delete()`, `clone()`, `unpack()`, `to_dict/json/yaml/tree/prompt`.
- Under the hood, `ODB` bridges `O` to SQLAlchemy tables (created from Pydantic models).

## Streams, Gulp, Pipes
- **StreamSchema** is an `O` subclass describing a stream (`name`, `role`, `author`).
- Streams store `Gulp` entries (timestamped text/value). Usage:
  - `stream = ww.schemas.StreamSchema.put(name='chat', role='assistant', author='Bot')`
  - `stream.write("hello")` appends.
  - `stream.read(limit=None, since=None)` reads gulps.
  - `StreamSchema.zip(stream1, stream2, ...)` merges streams by time to reconstruct dialogues.
- Agents in Narrative use streams to manage dialogue turns (`Life.get_next_author` reads last gulp author).
- Pipes: conceptually, a stream feeding another operator; implemented by zipping/reading streams and handing gulps to agents.

## Models / LLM Backends
- `ww.ask(prompt, schema, model_id='provider::name', temperature=...)` routes to `Model.generate`.
- Built-ins:
  - `wordwield/models/ollama.py` (`OllamaModel`) streaming JSON via Ollama.
  - `wordwield/models/openai.py` (`OpenaiModel`) using OpenAI chat with JSON schema.
- Default `model_id` in `ww.ask` is Ollama `gemma3n:e4b`; override per call or change default.
- Explicit routing: per-call `model_id` lets you switch providers without changing agent code; keep multiple backends side-by-side.

## Vector DB (optional)
- `wordwield/lib/vdb.py` wraps Chroma + SentenceTransformer (`paraphrase-multilingual-MiniLM-L12-v2`).
- `set(text, meta=None, doc_id=None)` stores embedding + metadata; `get(query, n_results=5, where=None)` returns matches.
- Imported in Narrative operators (`life.py`, `characters.py`) but not used heavily yet.

## Orchestrating Projects
- A `Project` is just an `Agent` subclass with semantic grouping (e.g., Narrative, GuessingGame).
- You can skip `Project` and run agents directly; `Project` is a semantic hook to bundle agents/streams.
- Narrative flow (high level):
  1) `StorySchema.put(...)`
  2) `Narrative` agent plans story, splits scenes, drafts scenes, extracts/develops characters, runs life simulation with dialogue streams.
- Jarvis flow: orchestrator coordinates sub-agents (see `projects/jarvis/operators`).

## Running
- Without server: `python projects/narrative/main.py` (resets DB, seeds streams, enters Life loop).
- With server (optional, minimal echo): `PYTHONPATH=$(pwd) uvicorn wordwield.web.server:app --reload`.
- `make run` now points to `wordwield.web.server:app` and requires `PROJECT_PATH` in `.env`.

## Importing in Client Code
- Any Python client (script/CLI/UI layer) can `from wordwield import ww`, call `ww.init(...)`, and invoke agents locally.
- If you need browser FE, expose HTTP/WebSocket endpoints that wrap agent calls; otherwise, importing `ww` directly suffices for Python-based “client” code.

## Key Takeaways
- Initialize once per process with `ww.init`.
- Define data as `O` subclasses; they are both Pydantic models and DB rows.
- Define behavior as `Agent`/`Operator` subclasses; register via project `operators/`.
- Use Streams + Gulps to sequence dialogue/events.
- Use `ww.ask` with ResponseSchemas to keep LLM outputs structured.
- Run in-process for simplicity; add a server only when you need a boundary or long-lived heavy resources.

## Little Pieces of Brilliance
- **Registry-first boot**: `ww.init` wires all registries (config/operators/schemas/models/expertise) up front, then auto-discovers classes by base type. Drop a new agent file into `operators/` and it’s instantly addressable as `ww.operators.<ns>.<Class>`.
- **O as double agent**: every schema is both a Pydantic model and a DB row. You get validation, JSON schema, prompts, and persistence with one class definition (`put/get/all/set/save/delete`).
- **Streams as dialog DNA**: `StreamSchema.zip` merges timelines across authors; Narrative’s `Life` agent uses that to rotate turns and feed LLMs consistent context.
- **Nested agents & state**: an Agent can own sub-agents (`agents = {...}`) and streams; state is a registry that auto-collects properties and template vars before prompting.
- **Template + schema prompting**: Jinja prompts plus `ResponseSchema` drive LLMs to structured JSON; `Model.generate` validates and fills defaults to keep outputs sane.
- **Easy operator instantiation**: any `O` with `class_name`/`name` can `to_operator()` via registry lookups—data objects can spawn their behavior.
- **Pluggable models**: `model_id='provider::name'` decouples agents from providers (Ollama, OpenAI, etc.) without code changes.
- **Expertise registry**: drop `.md/.txt` into `expertise/` and it’s instantly available as text snippets under `ww.expertise` for prompts.

(See more documentation in doc folder)
