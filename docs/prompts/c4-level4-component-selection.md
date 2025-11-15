# C4 Level 4 - Component Selection Prompt

You are a software architect analyzing the **{project_name}** project in the **{domain}** domain.

## Your Task

Identify the **10-12 most architecturally significant components** that deserve detailed C4 Level 4 (code-level) documentation.

## Selection Criteria

Choose components that are:
1. **Core Domain Logic** - Central business entities and workflows
2. **Critical Infrastructure** - Key technical components that enable the system
3. **Complex Algorithms** - Non-trivial logic that benefits from detailed explanation
4. **Integration Points** - Components that connect to external systems
5. **High Impact** - Changes here affect many other parts of the system
6. **Pedagogical Value** - Good examples for understanding the architecture

## Project Context

**Domain:** {domain}
**Total PHP Files:** {total_files}

**Architectural Layers from Deptrac:**
{layers_summary}

**Largest Components (by file size):**
{largest_files}

## Response Format

Provide your response as JSON:

```json
{{
  "selected_components": [
    {{
      "name": "ComponentName",
      "file_path": "relative/path/to/Component.php",
      "category": "Core Domain Logic|Infrastructure|Algorithm|Integration|Other",
      "importance": "Why this component is architecturally significant (1-2 sentences)",
      "key_concepts": ["concept1", "concept2", "concept3"]
    }}
  ],
  "honorable_mentions": [
    {{
      "name": "ComponentName",
      "file_path": "relative/path/to/Component.php",
      "reason": "Why it's worth mentioning but not in top 12"
    }}
  ],
  "selection_rationale": "Brief explanation of your overall selection strategy (2-3 sentences)"
}}
```

## Important Notes

- Select exactly 10-12 components for `selected_components`
- Include 5-10 components in `honorable_mentions`
- Focus on components that reveal architectural patterns and design decisions
- For {domain} domain, prioritize components related to the core business workflows
- Consider both technical complexity and business importance

Provide ONLY the JSON response, no additional text.