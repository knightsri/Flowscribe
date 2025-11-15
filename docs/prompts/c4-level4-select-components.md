# Level 4 – Component Selection Prompt

You are a software architect analyzing **{project_name}** in the **{domain}** domain.

## Your Task
Identify the **1–{max_components} most architecturally significant components** that deserve detailed C4 Level 4 documentation.

## Project Context
**Total PHP Files:** {total_files}

**Architectural Layers (from Deptrac):**
{layers_block}

**Largest Components (by file size):**
{largest_block}

## Selection Criteria
1. Core Domain Logic (central business entities/workflows)
2. Critical Infrastructure (enabling subsystems)
3. Complex Algorithms (non‑trivial logic)
4. Integration Points (external systems)
5. High Impact (touches many parts of the codebase)
6. Pedagogical Value (useful exemplars)

## Output — Return ONLY JSON (no commentary)
You **must** return valid JSON with at least **1** and at most **{max_components}** items in `selected_components`.

```json
{
  "selected_components": [
    {
      "name": "ComponentName",
      "file_path": "relative/path/to/Component.php",
      "category": "Core Domain Logic|Infrastructure|Algorithm|Integration|Other",
      "importance": "Why this component is architecturally significant (1-2 sentences)",
      "key_concepts": ["concept1", "concept2", "concept3"]
    }
  ],
  "honorable_mentions": [
    {
      "name": "ComponentName",
      "file_path": "relative/path/to/Component.php",
      "reason": "Why it's worth mentioning but not in top {max_components}"
    }
  ],
  "selection_rationale": "Brief explanation of your overall selection strategy (2-3 sentences)"
}
```

### Do NOT return
- Markdown, Mermaid, or any text outside the JSON block.
- An empty `selected_components` list.
