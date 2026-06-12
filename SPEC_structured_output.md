# SPEC: LangChain Structured Output Refactor

## Goal

Replace the fragile JSON-forcing pattern (`JsonOutputParser` + manual try/except) with LangChain's `with_structured_output()` API so the LLM returns typed Pydantic objects directly — no parsing, no silent failures.

---

## Changes to `chains.py`

### Before (current)
```python
llm = ChatOpenAI(...)
chain = SOME_PROMPT | llm | JsonOutputParser()
result = chain.invoke({...})  # returns dict, must cast manually
```

### After (target)
```python
llm = ChatOpenAI(...)
structured_llm = llm.with_structured_output(MyModel)
chain = SOME_PROMPT | structured_llm
result = chain.invoke({...})  # returns MyModel instance directly
```

---

## per-function changes

### `generate_ideas(count: int) -> List[str]`
- **Before**: `IDEAS_PROMPT | llm | JsonOutputParser()` → returns `dict` → manually cast
- **After**: `llm.with_structured_output(List[str])` via `invoke_tools()` or `bind_tools()` — OR keep `JsonOutputParser` only here since it returns a simple list of strings (low risk)
- **Decision**: Keep `JsonOutputParser` for `generate_ideas` — it's a simple list, not worth the overhead of schema registration. Same for `SUGGEST_FIXES_PROMPT` which returns a list of Suggestions.

### `build_story(suggestion: str) -> Story`

#### Sub-steps that return typed objects:

| Sub-step | Current return | New return type |
|---|---|---|
| `FIGURE_TIME_PERIOD_PROMPT` | `List[str]` | `List[str]` (simple, keep JsonOutputParser) |
| `FIGURE_MORALES_PROMPT` | `List[str]` | `List[str]` (simple, keep JsonOutputParser) |
| `FIGURE_PROTAGONISTS_PROMPT` | `List[dict]` → `[Protagonist(**p) for p in raw]` | `List[Protagonist]` via `with_structured_output(List[Protagonist])` |
| `FIGURE_VILLAIN_PROMPT` | `dict` → `Villain(**raw)` | `Villain` via `with_structured_output(Villain)` |
| `FIGURE_CHAPTER_TITLES_PROMPT` | `List[str]` | `List[str]` (keep JsonOutputParser) |
| `CHAPTER_PROMPT` | plain string | plain string (no schema needed) |
| `FIGURE_TITLE_PROMPT` | plain string | plain string (no schema needed) |
| `FIGURE_LOCATION_PROMPT` | plain string | plain string |
| `FIGURE_PLAN_PROMPT` | plain string | plain string |
| `FIGURE_SUMMARY_PROMPT` | plain string | plain string |

### `refine_story(story: Story) -> Story`

| Chain | Current | New |
|---|---|---|
| `FIGURE_LOGICAL_PROBLEMS_PROMPT` | `JsonOutputParser()` → `List[Problem]` via cast | `with_structured_output(List[Problem])` |
| `SUGGEST_FIXES_PROMPT` | `JsonOutputParser()` → `List[Suggestion]` via cast | Keep `JsonOutputParser` (returns simple list, low risk) |
| `ADJUST_CHAPTER_PROMPT` | plain string | plain string |

### `compare_stories(story_a: Story, story_b: Story) -> Story`
- Plain string → int parse → return story. Keep as-is (not worth refactoring).

---

## Model adjustments (`models.py`)

The `with_structured_output()` API in LangChain uses `createModelWithValidate()` internally for Pydantic v2. All models in `models.py` must:

1. Use Pydantic v2 style (already the case — `BaseModel` from pydantic)
2. Have all fields typed with concrete types (no `Any`)
3. Have `model_config` with `extra="ignore"` (already set)
4. **Check**: models used as output schemas (`Protagonist`, `Villain`, `Problem`, `Suggestion`) should NOT have complex validators that would fail during `model_validate()`

**Required changes to models.py**:
- Add `model_rebuild()` calls if any model has forward refs (none currently visible, but verify after implementation)
- For `List[Protagonist]` output, ensure `Protagonist` doesn't have private fields

---

## Error handling strategy

### Before
```python
try:
    raw = chain.invoke(...)
    result = [Model(**r) for r in raw]
except Exception:
    break  # silent fail, story continues with stale data
```

### After — two layers:

**Layer 1: LLM refusal / parse failure**
```python
try:
    result = chain.invoke(...)
except Exception as e:
    vprint(f"[red]Structured output failed:[/red] {e}")
    # Fall back based on context:
    # - For non-critical chains (ideas, morales): return empty list / default
    # - For critical chains (build_story, refine_story): raise, let caller decide
    raise
```

**Layer 2: Validation failure (model_validate fails)**
- `with_structured_output()` already calls `model_validate` internally
- If it fails, it raises — catch at call site

**Refinement loop**: When `refine_story` grooming fails, do NOT silently continue. Either:
- `vprint` a warning and break the loop cleanly
- Or allow a configurable `strict=False` mode that falls back to text-based editing

---

## Testing considerations

1. **Test `generate_ideas`** — verify it returns a list of strings
2. **Test `build_story`** — verify all sub-objects are correctly typed (Protagonist, Villain, Chapter)
3. **Test `refine_story`** — verify Problem/Suggestion objects parse correctly
4. **Test error path** — mock LLM to return invalid JSON and verify graceful error
5. **Update `test_llm.py`** — rename from "json_mode" test since we're not forcing JSON anymore

---

## Files to modify

1. **`storygen/chains.py`** — replace `JsonOutputParser` with `with_structured_output()`, update all chain functions
2. **`storygen/models.py`** — verify/fix any forward ref or validation issues, add `model_rebuild()` if needed
3. **`test_llm.py`** — update test name and assertions to reflect structured output approach

---

## Backward compatibility

- `settings.llm_base_url`, `settings.llm_api_key`, `settings.model_name` remain unchanged
- All chain functions keep the same signatures and return types (just cleaner internally)
- No changes to CLI, config loading, or TTS