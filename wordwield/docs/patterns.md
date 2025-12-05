# Patterns

## Tendencies

1. ### Presence over absence
2. ### Repeated over unique


## Anti-patterns

### 1. *"Not"* Antipattern
Large language models were trained navigating affirmative statements much better, then negations.
"Don't do", "Avoid", "No" and "Not" and even "Leave this field blank" are aimed at generating absence, rather then presence, which is highly unnatural for LLMs trained at generating text. 

### 2. *"Unique"* Antipattern
LLMs are generating likeness to what they see, so when you ask it to generate list of unique items, you will see repetitions and derivatives of previous items which is unlikely to contain truly unique generations.

---
---

## Pro–Patterns

### 1. *"Structured output"* Pattern
To produce output that can be parsed by your program use examples of structured output, i.e. JSON or YAML.<br>
Make sure you strip anything it may produce before first `{` and after last `}`.<br>
For best practice place type of field instead of a value. and description of a filed as comment e.g:

```
Put resut into JSON, output JSON ONLY.:
[{
	field_one: str # here goes field one,
	field_two: int # and here is some int
}, ...]
```


### 2. *"Filler"* Pattern
To fill out a schema to contain generated data about an object, generation has better aim if adjusted by previous generation.<br>
So having multiple fields with descriptions – fill them one by one, while presenting previous values as well:

```
	For story:
	{
		name  : "American Pie",
		genre : "comedy"
	}
	generate text for field "plot" – "main idea, plot of the story"
```

### 3. *"Sequence"* Pattern
When you need to fill a list that contains central theme or idea, or where items follow from one another, use a list of objects,<br>
where each object contains pre-condition and post-condition for each iteration:

```
	Main story is:
	---------------
	{{ main_story }}
	---------------
	Break story down into consecutive scenes:
	[{
		backstory : str  # outcome of previous scene affects current one,
		main_act  : str  # What happens in this scene 
		outcome   : str  # Definite result of scene: action, discovery or decision
	}, ... ]
```

### 4. *"Garbage Collector"* Pattern
LLM's absession is to generate something until it "feels" it's exhausted itself. There is no way to command it "say nothing if ...". Often time when asked to only put open speech in quotes it will improvise and err on the side of maximalizm and add something besides open speech.
To go with the flow, add a "garbage collector" for it to satisfy it's need to fill something out.


```
	Put your output into valid JSON:
	{
		reply   : str  # Only what you say out loud
		comment : str  # Everything besides open speech
	}
```

Then just ignore the comment