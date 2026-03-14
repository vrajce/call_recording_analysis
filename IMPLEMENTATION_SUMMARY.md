# KenexAI — Implementation Summary

## Scope
- Transform the app to operate RAG-only for audits and insights.
- Add Hugging Face–based batch summarization that writes into DuckDB.
- Create and populate a new ai_summary table.
- Implement Admin Settings (QSDD) CRUD to manage rules in qsdd_framework.
- Fix planner and prompt wiring to ensure call IDs are cited and answers stay concise.
- Add utility scripts to inspect and validate the database.

## Major Changes
- RAG-only backend
  - Disabled all SQL tool paths and helpers; answers use transcript evidence only.
  - Updated prompts to emphasize citation and “I don’t know” uncertainty.
  - References:
    - System prompt: [chat_backend.py](file:///c:/Users/Vraj/Projects/Kenexai/chat_backend.py#L131-L151)
    - RAG tool: [chat_backend.py](file:///c:/Users/Vraj/Projects/Kenexai/chat_backend.py#L309-L343)

- QSDD dynamic rules sourcing
  - Builds the QSDD context from qsdd_framework with enabled=TRUE and orders by weight.
  - References:
    - [get_qsdd_rules_prompt](file:///c:/Users/Vraj/Projects/Kenexai/chat_backend.py#L27-L69)
    - Print helper: [tools/print_qsdd_context.py](file:///c:/Users/Vraj/Projects/Kenexai/tools/print_qsdd_context.py)

- QSDD Admin CRUD
  - Backend CRUD module to add, update, delete rules in qsdd_framework.
  - Streamlit Admin Settings (QSDD) page now has forms to manage rules.
  - References:
    - Backend: [tools/qsdd_admin.py](file:///c:/Users/Vraj/Projects/Kenexai/tools/qsdd_admin.py)
    - UI: [app.py](file:///c:/Users/Vraj/Projects/Kenexai/app.py#L161-L250)

- AI Summaries (Hugging Face)
  - Create table and batch scripts to generate and insert summaries, strengths, improvements, failed_criteria.
  - Overwrite mode script ensures the table contains refreshed, consistent data.
  - References:
    - Table init: [tools/create_ai_summary_table.py](file:///c:/Users/Vraj/Projects/Kenexai/tools/create_ai_summary_table.py)
    - Batch (overwrite): [generate_ai_summary_overwrite_hf.py](file:///c:/Users/Vraj/Projects/Kenexai/generate_ai_summary_overwrite_hf.py)
    - Batch (fallback-friendly): [generate_ai_summary_hf.py](file:///c:/Users/Vraj/Projects/Kenexai/generate_ai_summary_hf.py)

## Database
- Verified DuckDB tables:
  - agents, ai_summary, call_summary, calls, data_quality_log, qsdd_framework, quality_scores, transcripts
  - Inspect utility: [tools/db_overview.py](file:///c:/Users/Vraj/Projects/Kenexai/tools/db_overview.py)
- ai_summary schema:
  - contact_id, agent_id, summary, strengths, improvements, failed_criteria, model_name, version, created_at

## Prompts & Behavior
- RAG answers include up to 10 Call ID citations inline to limit clutter.
- “If you don’t know, say ‘I don’t know’” added to the system prompt guidelines.
- Manager Copilot and UI behaviors updated accordingly.

## How to Run

### Start the UI
```bash
streamlit run app.py
```

### Initialize ai_summary table
```bash
python tools/create_ai_summary_table.py
python tools/db_overview.py
```

### Generate AI summaries (overwrite all rows)
```bash
# Optional: set model and version
# PowerShell:
$env:HF_MODEL="google/flan-t5-base"
$env:AI_SUMMARY_VERSION="2"

python generate_ai_summary_overwrite_hf.py
```

### Quick validation
```bash
python tools/quick_test.py
```

## Admin Settings (QSDD)
- Navigate to “Admin Settings (QSDD)” in the UI.
- Manage rules:
  - Add: section, criteria, weights, enabled, what/when to check, examples, scoring method
  - Update: select a rule by framework_id, modify specific fields
  - Delete: remove a rule by framework_id

## Notes
- Summaries include “Note: Machine-generated, not human-intervened” inside summary to clearly mark automation.
- If Hugging Face models cannot load, scripts store a fallback summary and mark model_name=fallback to keep the pipeline robust.

## Next Steps
- Add guardrails for QSDD weight calculations (e.g., effective_weight = section_weight * criteria_weight).
- Add viewer pages for ai_summary with filters for agent_id and time ranges.
- Optional: add authentication for Admin Settings changes.
