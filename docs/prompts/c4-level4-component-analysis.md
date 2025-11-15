# C4 Level 4 - Component Analysis Prompt

You are an expert software architect analyzing code for architectural documentation.

**YOUR TASK:** Analyze the provided component and return ONLY a JSON object with the architecture details.

**CRITICAL:** Your response must be valid JSON. Do not include any explanatory text, thinking process, or commentary. Only JSON.

---

## Project Context

**Project:** {project_name}
**Domain:** {domain}

{metadata_context}

---

## Component Information

**Name:** {component_name}
**File:** {file_path}
**Category:** {category}
**Importance:** {importance}

## Source Code

```php
{code}
```

## Your Task

Analyze this component and provide detailed architectural documentation in JSON format:

```json
{{
  "component_name": "{component_name}",
  "purpose": "What this component does (1-2 sentences)",
  "responsibility": "Its single responsibility in the architecture",
  "class_type": "Entity|DAO|Service|Controller|Handler|Factory|Strategy|Other",
  "design_patterns": ["Pattern1", "Pattern2"],
  "key_methods": [
    {{
      "name": "methodName",
      "purpose": "What it does",
      "parameters": "param types",
      "returns": "return type",
      "complexity": "Simple|Moderate|Complex"
    }}
  ],
  "dependencies": [
    {{
      "type": "class|interface|trait",
      "name": "DependencyName",
      "relationship": "extends|implements|uses|injects"
    }}
  ],
  "public_interface": [
    "method1()",
    "method2()",
    "method3()"
  ],
  "internal_state": [
    "property1: type - description",
    "property2: type - description"
  ],
  "key_algorithms": [
    {{
      "name": "Algorithm name",
      "description": "What it does and why it's important"
    }}
  ],
  "integration_points": [
    "External system or component it integrates with"
  ],
  "architectural_notes": "Any important architectural decisions, patterns, or constraints (2-3 sentences)"
}}
```

## Analysis Guidelines

1. **Focus on architecture, not implementation details**
2. **Identify design patterns** (Factory, Strategy, Repository, etc.)
3. **Highlight public interface** vs internal implementation
4. **Note integration points** with other components or external systems
5. **Explain key algorithms** if any
6. **Document dependencies** and their nature

## CRITICAL: JSON Formatting Rules

- **Escape backslashes**: Use double backslash for any backslash in strings
- **Escape quotes**: Use backslash-quote for quotes inside strings
- **Use forward slashes**: Prefer forward slash over backslash in paths
- **No line breaks in strings**: Keep strings on single lines
- **Complete the JSON**: Ensure all brackets and braces are closed

## OUTPUT FORMAT

**YOU MUST RESPOND WITH ONLY VALID JSON. DO NOT INCLUDE:**

- ❌ Explanatory text before the JSON
- ❌ Explanatory text after the JSON
- ❌ Thinking process or analysis
- ❌ "Here's the analysis:" or similar phrases
- ❌ Any text outside the JSON structure

**YOUR ENTIRE RESPONSE MUST BE:**

```json
{{ ... }}
```

Start your response with `{{` and end with `}}`. Nothing else.

Provide ONLY the JSON response, no additional text.
