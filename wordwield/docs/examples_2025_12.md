# WordWield Examples (2025_12)

## Init and auto-discovery
```python
from wordwield import ww
PROJECT_PATH = "/Users/you/your_project"
ww.init(PROJECT_NAME="demo", PROJECT_PATH=PROJECT_PATH, reset_db=True)
# Any .py under operators/schemas/models is auto-registered:
# call as ww.operators.your_ns.YourAgent(...)
```

## O: schema + DB + prompt schema
```python
from wordwield import ww
from wordwield.core     import O

class Note(O):
    title: str
    body: str

ww.init("demo", PROJECT_PATH)
note = Note.put("first", title="Hello", body="World")
print(note.to_json())     # JSON with data
print(note.to_schema_prompt())  # Prompt-friendly schema text
```

## Agent with schema-validated output
```python
from wordwield import ww
from wordwield.core     import O

class ReplySchema(O):
    answer: str = O.Field(description="Concise reply")

class Greeter(ww.operators.Agent):
    ResponseSchema = ReplySchema
    template = "Say hi to {{ name }} in one sentence."

ww.init("demo", PROJECT_PATH)
resp = Greeter() (name="Alex")  # Structured JSON, validated
print(resp)  # {'answer': '...'}
```

## Streams and gulps (dialogue replay)
```python
from wordwield import ww
ww.init("demo", PROJECT_PATH)

user_stream = ww.schemas.StreamSchema.put(name="user", role="user", author="You")
bot_stream  = ww.schemas.StreamSchema.put(name="bot",  role="assistant", author="Bot")

user_stream.write("Hello!")
bot_stream.write("Hi there, how can I help?")

dialogue = ww.schemas.StreamSchema.zip(user_stream, bot_stream)
print(dialogue.to_prompt())  # Merged timeline
```

## Nested agents and state
```python
from wordwield import ww

class SubAgent(ww.operators.Agent):
    template = "Summarize: {{ text }}"

class Parent(ww.operators.Agent):
    agents = {"summarizer": SubAgent}
    async def invoke(self, text):
        return await self.agents.summarizer(text=text)

ww.init("demo", PROJECT_PATH)
print(Parent()(text="WordWield auto-wires agents."))
```

## Model routing (switch providers per call)
```python
from wordwield import ww
from wordwield.core     import O

class EchoSchema(O):
    message: str

ww.init("demo", PROJECT_PATH)
prompt = "Return JSON: {\"message\": \"hi\"}"

# Ollama (default)
res1 = ww.ask(prompt=prompt, schema=EchoSchema, model_id="ollama::gemma3n:e4b")
# OpenAI
res2 = ww.ask(prompt=prompt, schema=EchoSchema, model_id="openai::gpt-4o")
```

## Expertise registry (prompt snippets)
```python
from wordwield import ww
ww.init("demo", PROJECT_PATH)
print(ww.expertise)              # Tree of available snippets
print(ww.expertise.domain.topic) # Access text from expertise/domain/topic.md
```

## Vector DB wrapper (Chroma + embeddings)
```python
from wordwield.core.vdb import VDB

vdb = VDB(collection_name="memory")
vdb.set("SaaS marketing trends", meta={"tag": "marketing"})
hits = vdb.get("marketing", n_results=3)
for doc, score, meta, doc_id in hits:
    print(doc, score, meta, doc_id)
```
