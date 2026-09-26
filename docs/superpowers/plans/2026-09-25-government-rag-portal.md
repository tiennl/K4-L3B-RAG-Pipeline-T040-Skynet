# Government RAG Portal Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Transform the existing Streamlit tax RAG chatbot into a formal, source-first government knowledge portal without changing the generation pipeline.

**Architecture:** Keep `generate_with_citation(query, top_k)` and session history unchanged. Rebuild the Streamlit composition in `app.py` around semantic portal sections and CSS tokens, while `render_sources` remains the single point that renders verifiable `GenerationResult.sources`.

**Tech Stack:** Python 3.12, Streamlit, pytest with Streamlit `AppTest`, existing RAG generation module.

## Global Constraints

- All visitor-facing copy is Vietnamese.
- Do not add React, a new UI library, or external image assets.
- Citations may only come from `GenerationResult.sources`; never render model-generated URLs.
- Preserve `generate_with_citation(query, top_k)` and the current safe-refusal behavior.
- Use navy, warm ivory/beige, muted saffron, and subdued green; preserve 4.5:1 minimum text contrast.
- Do not modify existing staged data or Track B/C files.

---

### Task 1: Cover the new portal skeleton with an AppTest

**Files:**
- Modify: `tests/test_app.py`
- Test: `tests/test_app.py`

**Interfaces:**
- Consumes: `main()` in `app.py` and the existing `AppTest.from_file` test setup.
- Produces: a regression check for the government portal heading, navigation labels, categories, prompt suggestions, feature cards, and chat input.

- [ ] **Step 1: Write the failing test**

```python
def test_app_renders_government_portal_sections():
    app = AppTest.from_file(str(APP_PATH)).run()

    assert not app.exception
    assert "Trợ lý Tra cứu Thông tin Chính thức" in app.markdown[0].value
    assert "Thủ tục hành chính" in app.markdown[0].value
    assert "Tra cứu chính xác theo tài liệu gốc" in app.markdown[0].value
    assert app.chat_input[0].placeholder == "Hãy nhập câu hỏi của bạn..."
    assert len(app.button) == 6
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `.venv/bin/pytest tests/test_app.py::test_app_renders_government_portal_sections -q`

Expected: FAIL because the current application has no official portal hero, categories, feature-card text, or six buttons.

- [ ] **Step 3: Implement the minimum UI needed for the assertion**

Add a portal hero, four suggested-question buttons, two feedback buttons, a category panel, and the four feature-card labels in `app.py`. Use the exact strings from the test.

- [ ] **Step 4: Run the focused test to verify it passes**

Run: `.venv/bin/pytest tests/test_app.py::test_app_renders_government_portal_sections -q`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add app.py tests/test_app.py
git commit -m "feat(app): add government RAG portal shell"
```

### Task 2: Build the source-first government chatbot layout

**Files:**
- Modify: `app.py:17-164`
- Test: `tests/test_app.py`

**Interfaces:**
- Consumes: `SUGGESTED_QUESTIONS`, `render_sources(sources)`, `st.session_state.messages`, and `generate_with_citation(query, top_k)`.
- Produces: `apply_theme()`, `render_portal_header()`, `render_feature_cards()`, and a two-column desktop chat experience that collapses on mobile.

- [ ] **Step 1: Write the failing test**

```python
def test_app_keeps_source_first_chat_controls():
    app = AppTest.from_file(str(APP_PATH)).run()

    assert app.slider[0].label == "Số nguồn tham khảo"
    assert app.chat_input[0].placeholder == "Hãy nhập câu hỏi của bạn..."
    assert "Nguồn chính thức" in app.markdown[0].value
    assert "Đã xác thực" in app.markdown[0].value
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `.venv/bin/pytest tests/test_app.py::test_app_keeps_source_first_chat_controls -q`

Expected: FAIL because the new source-first trust labels are not rendered yet.

- [ ] **Step 3: Implement the minimum source-first layout**

In `app.py`, use helpers to render:

```python
def render_portal_header() -> None:
    """Render the official navigation and hero without changing RAG state."""


def render_feature_cards() -> None:
    """Render static descriptions of the four supported RAG capabilities."""
```

Use CSS variables for `--navy`, `--ivory`, `--saffron`, `--green`, `--ink`, and `--line`. Render categories and retrieval controls in the left column; render message history, chat input, trust badges, feedback buttons, and source expanders in the right column. Add media queries so the layout becomes one column below 768px.

- [ ] **Step 4: Run the focused test to verify it passes**

Run: `.venv/bin/pytest tests/test_app.py::test_app_keeps_source_first_chat_controls -q`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add app.py tests/test_app.py
git commit -m "feat(app): add source-first chatbot workspace"
```

### Task 3: Render verified citations and error states consistently

**Files:**
- Modify: `app.py:17-42`
- Test: `tests/test_app.py`, `tests/test_edge_cases.py`

**Interfaces:**
- Consumes: source dictionaries from `GenerationResult.sources` with `metadata`, `retrieval_method`, `score`, and `content`.
- Produces: accessible source accordion labels and an official-source badge only when the answer has sources.

- [ ] **Step 1: Write the failing test**

```python
def test_render_sources_keeps_original_source_metadata(monkeypatch):
    source = {
        "content": "Nội dung kiểm chứng.",
        "score": 0.91,
        "retrieval_method": "hybrid",
        "metadata": {
            "title": "Văn bản hướng dẫn",
            "source": "Cổng thông tin chính thức",
            "doc_type": "Văn bản",
            "chunk_index": 2,
            "url": "https://example.gov.vn/van-ban",
        },
    }

    assert "Cổng thông tin chính thức" in source_label(source, 1)
    assert "hybrid" in source_label(source, 1)
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `.venv/bin/pytest tests/test_app.py::test_render_sources_keeps_original_source_metadata -q`

Expected: FAIL only if the source-label contract was changed while restructuring the UI.

- [ ] **Step 3: Implement the minimum citation behavior**

Keep `source_label` source-first. In `render_sources`, render the `Nguồn chính thức` and `Đã xác thực` badges before the accordion only when `sources` is nonempty. Keep `st.link_button` conditional on a real metadata URL, and leave safe refusal without citation UI.

- [ ] **Step 4: Run the focused test to verify it passes**

Run: `.venv/bin/pytest tests/test_app.py::test_render_sources_keeps_original_source_metadata -q`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add app.py tests/test_app.py tests/test_edge_cases.py
git commit -m "fix(app): preserve verified citation metadata"
```

### Task 4: Verify the portal across the RAG interaction path

**Files:**
- Modify: `app.py` only if verification discovers a direct UI defect.
- Test: `tests/test_app.py`, `tests/test_edge_cases.py`

**Interfaces:**
- Consumes: completed `app.py`, `generate_with_citation`, and existing test fixtures.
- Produces: passing regression tests and a manually verified local Streamlit portal.

- [ ] **Step 1: Run the application tests**

Run: `.venv/bin/pytest tests/test_app.py tests/test_edge_cases.py -q`

Expected: PASS with no `AppTest` exception.

- [ ] **Step 2: Compile the application**

Run: `.venv/bin/python -m py_compile app.py src/task10_generation.py`

Expected: exit code 0.

- [ ] **Step 3: Launch the local portal**

Run: `.venv/bin/python -m streamlit run app.py --server.headless true --server.port 8501 --browser.gatherUsageStats false`

Expected: Streamlit reports the local URL.

- [ ] **Step 4: Exercise visible states in the browser**

At 375px, 768px, 1024px, and desktop width, verify the navigation, hero prompt, category panel, suggested questions, source accordion, and footer. Submit one supported query and one unsupported query; confirm that the first shows actual source metadata and the second shows the safe refusal without source badges.

- [ ] **Step 5: Commit any verification-only fix**

```bash
git add app.py tests/test_app.py
git commit -m "fix(app): polish government portal responsiveness"
```
