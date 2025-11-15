# C4 Level 4 - Component Class Diagram

You are an expert at creating clear, professional class diagrams for code-level architecture documentation.

## Component Information

**Component:** {component_name}
**Type:** {class_type}

## Dependencies

**Total Dependencies:** {total_dependencies}

**Top Dependencies (by importance):**
{top_dependencies}

{remaining_summary}

## Your Task

Generate a Mermaid class diagram showing:

1. The main component: **{component_name}**
2. The **top 4 most important dependencies** (fully detailed)
3. A summary node showing remaining dependencies (if more than 4 exist)

### CRITICAL - Mermaid Syntax Safety Rules

**Node IDs:**

- Use only alphanumeric characters and underscores
- NO spaces, hyphens, or special characters in IDs
- Good: `UserService`, `Auth_Handler`, `DB1`
- Bad: `User Service`, `Auth-Handler`, `DB#1`

**Node Labels:**

- If label contains spaces, parentheses, colons, or special characters → wrap in double quotes
- Always quote labels with `<br/>` tags
- Escape internal quotes with backslash: `\"`
- Good: `User["User Service"]`, `P1["Priority: High<br/>Status: Active"]`
- Bad: `User[User Service]`, `P1[Priority: High\nStatus: Active]`

**Special Characters:**

- Replace `(` and `)` with `-` OR wrap entire label in quotes
- Replace `&` with `and`
- Use `<br/>` for line breaks (NOT `\n`)

**Relationship Syntax:**

- Inheritance: `Parent <|-- Child`
- Implementation: `Interface <|.. Implementation`
- Dependency/Usage: `ClassA ..> ClassB`
- Association: `ClassA --> ClassB`

### Required Diagram Structure

**CRITICAL: Use SINGLE curly braces for class bodies in Mermaid!**

```mermaid
classDiagram
    %% Main component (always shown)
    class {component_name_safe} {
        +key_method()
        -property
    }
    
    %% Top 4 dependencies (detailed)
    class Dependency1 {
        +method()
    }
    class Dependency2 {
        +method()
    }
    class Dependency3 {
        +method()
    }
    class Dependency4 {
        +method()
    }
    
    %% Relationships for top 4
    Dependency1 <|-- {component_name_safe}  : extends
    Dependency2 <|.. {component_name_safe}  : implements
    {component_name_safe} ..> Dependency3   : uses
    {component_name_safe} ..> Dependency4   : uses
    
    %% Summary node (if N > 4)
    class MoreDeps["... 5 more dependencies"] {
        See documentation
    }
    {component_name_safe} ..> MoreDeps : depends on
```

**SYNTAX WARNING:**

- ✅ CORRECT: `class MyClass { +method() }` (single braces)
- ❌ WRONG: `class MyClass {{ +method() }}` (double braces - syntax error!)
- ❌ WRONG: `class MyClass [[ +method() ]]` (wrong bracket type)

### Styling Guidelines

- Keep class definitions minimal (2-3 key methods/properties per class)
- Use appropriate relationship arrows based on dependency type
- The summary node should use quoted label: `MoreDeps["... N more dependencies"]`
- Ensure all node IDs are safe (alphanumeric + underscore only)
- Ensure all labels with spaces/special chars are quoted

### Selection Strategy

From the provided dependencies:

1. Pick the top 4 by importance/relevance
2. Show their relationship to {component_name}
3. If more than 4 dependencies exist, add summary node

Generate ONLY the Mermaid code block. No explanations, no markdown fence markers.
