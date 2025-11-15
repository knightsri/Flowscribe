# C4 Level 2: Container Diagram Generation Prompt

You are creating a **C4 Level 2 (Container/Layer) diagram** showing the architectural layers within **{project_name}**.

## What is C4 Level 2?

Level 2 zooms into the system and shows its major containers/layers:

- **Containers** = Deployable units, services, layers, or major subsystems
- Shows how they depend on each other
- Still high-level (not showing individual classes/components yet)

## Input Data

You have been provided with:

- **Project name**: {project_name}
- **Layers**: List of architectural layers with descriptions
- **Dependencies**: How layers depend on each other (with reference counts)
- **Total violations**: {total_violations} architectural rule violations detected

**Layers data**:

```json
{layers}
```

**Dependencies data**:

```json
{dependencies}
```

## Your Task

Generate a **Mermaid diagram** showing the container/layer architecture.

### CRITICAL - Mermaid Syntax Safety Rules

Follow these rules EXACTLY:

1. **Node IDs**: Use only alphanumeric characters and underscores
   - ✓ Good: `User`, `Presentation`, `Domain_Layer`, `API`
   - ✗ Bad: `Domain Layer`, `API-Gateway`, `Layer(Admin)`

2. **Node Labels**:
   - If label contains spaces, colons, `<br/>`, or special chars → wrap in double quotes
   - Always quote labels with `<br/>` tags
   - Example: `Presentation["Presentation Layer<br/>Handles HTTP requests"]`

3. **Edge Labels**: Quote if they contain special characters
   - Example: `Presentation -->|"15 refs"| Domain`

4. **Line breaks**: Use `<br/>` (NOT `\n`)

### Required Diagram Structure

Create a `graph TB` (top-to-bottom) diagram with:

1. **External actor** (User) outside the system
2. **System boundary** using a subgraph
3. **Layers** inside the system boundary
4. **Dependencies** between layers with reference counts
5. **Styling** to show layer types

### Template Structure

**IMPORTANT**: Use standard markdown code fence with `mermaid` language identifier.

```
graph TB
    %% External Actors
    User["👤 User<br/>End users of the system"]
    
    %% System Boundary
    subgraph System["{{project_name}}"]
        direction TB
        
        %% Layers (one node per layer)
        [LayerID]["[Layer Name]<br/>[Description]"]
        
        %% Example:
        %% Presentation["Presentation<br/>Handles HTTP requests and UI"]
        %% Domain["Domain<br/>Business rules and entities"]
    end
    
    %% User to System
    User -->|"Uses"| [TopMostLayer]
    
    %% Internal Dependencies (from dependencies data)
    [FromLayer] -->|"X refs"| [ToLayer]
    
    %% Example:
    %% Presentation -->|"42 refs"| Domain
    %% Domain -->|"18 refs"| Persistence
    
    %% Styling
    classDef userStyle fill:#e1f5ff,stroke:#01579b,color:#000
    classDef layerStyle fill:#fff3e0,stroke:#e65100,color:#000
    classDef violationStyle fill:#ffebee,stroke:#c62828,color:#000
    
    class User userStyle
    class [layers with violations] violationStyle
    class [other layers] layerStyle
```

### Diagram Guidelines

1. **Show all provided layers** - one node per layer

2. **Layer node format**:

   ```
   LayerName["LayerName<br/>Description"]
   ```

3. **Dependencies** - show all provided dependencies with counts:

   ```
   FromLayer -->|"count refs"| ToLayer
   ```

4. **Highlight violations** - if `total_violations > 0`:
   - Apply `violationStyle` to layers that have violations
   - Use warning colors (red/orange tint)

5. **User interaction** - show User connecting to the top-most layer (usually Presentation or API)

6. **System boundary** - wrap all layers in a subgraph titled "{project_name}"

### Example Output

For a project with Presentation, Domain, and Persistence layers:

```
graph TB
    User["👤 User<br/>System users"]
    
    subgraph System["MyProject"]
        direction TB
        Presentation["Presentation<br/>HTTP handlers and UI"]
        Domain["Domain<br/>Business logic"]
        Persistence["Persistence<br/>Database access"]
    end
    
    User -->|"Uses"| Presentation
    Presentation -->|"42 refs"| Domain
    Domain -->|"18 refs"| Persistence
    
    classDef userStyle fill:#e1f5ff,stroke:#01579b,color:#000
    classDef layerStyle fill:#fff3e0,stroke:#e65100,color:#000
    classDef violationStyle fill:#ffebee,stroke:#c62828,color:#000
    
    class User userStyle
    class Presentation,Domain violationStyle
    class Persistence layerStyle
```

### Quality Checklist

Before outputting, verify:

- ✓ All layer IDs use only alphanumeric and underscores
- ✓ All node labels with `<br/>` are quoted
- ✓ All edge labels with special chars are quoted
- ✓ System boundary is a subgraph with title
- ✓ User actor is outside the system boundary
- ✓ Dependencies match the data provided
- ✓ Layers with violations are styled differently (if any)
- ✓ Using standard markdown code fence (NOT `<div class="mermaid">`)

---

## Output Format

Generate ONLY the Mermaid diagram code.

**CRITICAL - Fence Format**:

- Use standard markdown code fence: (three backticks)`mermaid` ... (three backticks)
- **DO NOT** use HTML `<div class="mermaid">` tags

Do NOT include:

- Explanations or commentary
- Multiple alternative versions
- Code fences around the mermaid fence

DO include:

- Clean, well-formatted Mermaid syntax
- All layers from the data
- All dependencies with counts
- Proper styling classes

---

Generate the container diagram now.
