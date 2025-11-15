# C4 Level 3 – Component Diagram Prompt (Styled)

You are generating a **C4 Level 3 (Component) diagram** in Mermaid for a single layer of a project.

## Project Context
- Project: {project_name}
- Layer: {layer_name}
- Orientation: {orientation}

## Input Data
Choose and **visually emphasize the Top {pick.count}** components by `{pick.key}` (descending).
You MUST add a single collapsed node labeled exactly **"... {other_count} other components"** when there are more than `{pick.count}` items.
(If `other_count` is 0, omit this node.)

- items: [{ name, label, violations, file, purpose }]
- dependencies: [{ from, to, internal (bool), to_layer }]
- pick: { strategy, key, count }
- other_count: {other_count}
- style: { show_external_layers: bool, limit_internal_edges: int, limit_external_edges: int }

## Task
Produce a **single Mermaid code block** for a C4 Level 3 diagram:
- Use `flowchart {orientation}`.
- Create a **subgraph** titled `"{project_name} - {layer_name} Layer"`.
- Inside the subgraph:
  - Add the **Top {pick.count}** components as primary nodes.
  - Add non-top components either as normal nodes OR group them into a single collapsed node named `"... {other_count} other components"` (only if `other_count > 0`).
- Show up to `{style.limit_internal_edges}` internal edges (between components in this layer).
- If `style.show_external_layers` is true, add minimal placeholder nodes for referenced external layers, suffixed with `" (Layer)"`, and up to `{style.limit_external_edges}` external edges using dotted lines.

## CRITICAL – Mermaid Syntax Safety Rules
**Node IDs**: alphanumeric + underscores (no spaces/hyphens/specials).  
**Node Labels**: if the label contains spaces or special characters (like `(` or `)`), **wrap it in double quotes**.  
Do **not** add backslashes for parentheses. Only escape quotes if a `"` character appears inside the label.

Examples (correct):
- `Admin["Admin (Layer)"]`
- `CacheService["Cache Service<br/>stores rendered pages"]`

## Styling (match Level 2 color palette)
Add these class definitions at the end of the diagram, and apply them to the right nodes:
```
classDef topStyle fill:#e8f5e9,stroke:#1b5e20,color:#000,stroke-width:3px
classDef otherStyle fill:#f3e5f5,stroke:#6a1b9a,color:#000
classDef collapsedStyle fill:#eeeeee,stroke:#616161,color:#000,stroke-dasharray:3 2
classDef externalStyle fill:#e1f5fe,stroke:#01579b,color:#000
```
- Apply `topStyle` to the {pick.count} emphasized components.
- Apply `otherStyle` to any additional non-top components you render individually.
- If you used the collapsed node, apply `collapsedStyle` to that node.
- For external layer placeholders (labels end with " (Layer)"), apply `externalStyle`.

## Visual Palette
Use this palette to style nodes and edges consistently with Level 2:

{palette_table}

## Output
Return **only**:

```mermaid
<your diagram here>
```

No commentary or extra blocks.
