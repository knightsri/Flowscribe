# C4 Level 1: System Context Generation Prompt

You are a software architect creating **C4 Level 1 (System Context) documentation** for the **{project_name}** project in the **{project_domain}** domain.

## Project Information

**Repository:** {repo_url}  
**Domain:** {project_domain}
**Framework:** This appears to be a {project_framework} project based on the analyzed files.

This context helps you understand the project scope and target audience for your analysis. Pay special attention to framework-specific patterns and integrations.

## What is C4 Level 1?

A System Context diagram shows the **big picture** - how your system fits into the world:

- **The System** - The software being documented (center of the diagram)
- **Users/Actors** - People who interact with the system
- **External Systems** - Other systems it integrates with
- **Relationships** - How they all connect

Think of it as a **10,000-foot view** - you're showing the forest, not the trees.

---

## Project Files Provided

The following files have been analyzed using framework-aware discovery, prioritizing configuration files, framework-specific files, and documentation that reveal external system integrations and user types:

{files_content}

---

## Framework-Specific Analysis Guidelines

Since this is a **{project_framework}** project, pay special attention to:

### WordPress Projects

- Plugin integrations (look for plugin files and configurations)
- Theme customizations and third-party theme dependencies
- Database configuration and caching systems
- WordPress.org ecosystem integrations (plugin/theme repositories)
- Email services, CDN configurations, file upload handling
- Multisite network capabilities
- REST API and external service integrations

### Drupal Projects

- Module ecosystem and contrib modules
- Configuration management and deployment workflows
- Services container and dependency injection
- Database abstraction layer and multiple DB support
- Caching layers (Redis, Memcached, Varnish)
- Search integrations (Solr, Elasticsearch)

### Laravel Projects

- Service providers and dependency injection
- Queue systems and job processing
- Database connections and migrations
- API integrations and HTTP clients
- Caching and session storage
- File storage and cloud services

### Symfony Projects

- Bundle architecture and third-party bundles
- Service container and configuration
- Console commands and scheduled tasks
- HTTP foundation and external API calls
- Database abstraction and ORM integrations

### Django Projects

- App architecture and third-party packages
- Database backends and connection pooling
- Celery for task queues
- Static file and media handling
- REST framework and API integrations

### Rails Projects

- Gem dependencies and Rails engines
- Active Record and database adapters
- Background job processing (Sidekiq, etc.)
- Asset pipeline and CDN integration
- Action Mailer and email services

---

## Your Task

Analyze the project files above and generate a **complete C4 Level 1 markdown document** that includes:

1. System overview and description
2. Key features
3. Users and actors (framework-specific roles)
4. External systems and integrations (discovered from config files)
5. **A Mermaid system context diagram**

### Document Structure Required

**IMPORTANT**: The document structure below contains placeholders that have already been filled in with actual values. Use these EXACT values in your output:

- Project name: **{project_name}**
- Generation date: **{generation_date}**
- Domain: **{project_domain}**

Do NOT make up your own values for these fields. Use them exactly as shown above.

Use this exact structure:

```
# {project_name} - C4 Level 1: System Context

**Generated:** {generation_date}  
**Domain:** {project_domain}  
**Repository:** {repo_url}  
**Framework:** {project_framework}  
**Diagram Level:** C4 Level 1 (System Context)

---

## System Overview

### Description

[2-3 paragraphs describing what this system does and its role in the ecosystem. Include framework-specific context.]

### Purpose

[1 clear sentence: "The purpose of {project_name} is to..."]

### Key Features

- [Feature 1 - focus on capabilities revealed in config files]
- [Feature 2 - emphasize integrations found in the files]
- [Feature 3 - highlight framework-specific strengths]
- [Feature 4 - mention extensibility patterns discovered]
- [Feature 5 - note deployment and scaling capabilities]

---

## System Context Diagram

[Generate the Mermaid diagram here following the instructions below]

---

## Users and Actors

[Focus on framework-specific user types and roles discovered in files]

### [User Type Name]

**Role:** [What this user does with the system]

**Primary Actions:**
- [Action 1]
- [Action 2]
- [Action 3]

[Identify 3-5 user types, including framework-specific roles like Plugin Developers, Theme Designers, etc.]

---

## External Systems and Integrations

[Focus on actual integrations discovered in the analyzed files]

### [External System Name]

**Purpose:** [Why does {project_name} integrate with this?]  
**Integration Type:** [API / Database / File System / Message Queue / etc.]  
**Data Flow:** [What data is exchanged and in which direction?]  
**Evidence:** [Which config file or code revealed this integration?]

[Identify 4-8 external systems based on actual evidence from files]

---

## Mermaid Diagram Requirements

**IMPORTANT**: The System Context Diagram should appear **immediately after the System Overview section** and **before the Users and Actors section**. This ensures stakeholders see the visual overview before diving into details.

### CRITICAL - Mermaid Syntax Safety Rules

Follow these rules EXACTLY to ensure the diagram renders correctly:

1. **Node IDs**: Use only alphanumeric characters and underscores
   - ✓ Good: `System`, `User1`, `ExtDB`, `Payment_API`
   - ✗ Bad: `Payment-API`, `Ext DB`, `User(Admin)`

2. **Node Labels**:
   - If label contains spaces, colons, parentheses, or line breaks → wrap in double quotes
   - Always quote labels with `<br/>` tags
   - Escape internal quotes with `\"`
   - Example: `System["🛍️ {project_name}<br/>Main application server"]`

3. **Line breaks**: Use `<br/>` (NOT `\n`)

4. **Edge labels**: Can be simple text or quoted if they contain special chars
   - Example: `User -->|"Uses via web browser"| System`

5. **Icons**: Use emojis to make the diagram more engaging:
   - Users: 👤 or 👥
   - System (main): 🛍️ or 🎯 or 🖥️
   - Exte# C4 Level 1: System Context Generation Prompt

You are a software architect creating **C4 Level 1 (System Context) documentation** for the **{project_name}** project in the **{project_domain}** domain.

## Project Information

**Repository:** {repo_url}  
**Domain:** {project_domain}

This context helps you understand the project scope and target audience for your analysis.

## What is C4 Level 1?

A System Context diagram shows the **big picture** - how your system fits into the world:

- **The System** - The software being documented (center of the diagram)
- **Users/Actors** - People who interact with the system
- **External Systems** - Other systems it integrates with
- **Relationships** - How they all connect

Think of it as a **10,000-foot view** - you're showing the forest, not the trees.

---

## Project Files Provided

{files_content}

---

## Your Task

Analyze the project files above and generate a **complete C4 Level 1 markdown document** that includes:

1. System overview and description
2. Key features
3. Users and actors
4. External systems and integrations
5. **A Mermaid system context diagram**

### Document Structure Required

**IMPORTANT**: The document structure below contains placeholders that have already been filled in with actual values. Use these EXACT values in your output:

- Project name: **{project_name}**
- Generation date: **{generation_date}**
- Domain: **{project_domain}**

Do NOT make up your own values for these fields. Use them exactly as shown above.

Use this exact structure:

```

# {project_name} - C4 Level 1: System Context

**Generated:** {generation_date}  
**Domain:** {project_domain}  
**Repository:** {repo_url}  
**Diagram Level:** C4 Level 1 (System Context)

---

## System Overview

### Description

[2-3 paragraphs describing what this system does and its role in the ecosystem]

### Purpose

[1 clear sentence: "The purpose of {project_name} is to..."]

### Key Features

- [Feature 1 - brief description]
- [Feature 2 - brief description]
- [Feature 3 - brief description]
- [Feature 4 - brief description]
- [Feature 5 - brief description]

---

## System Context Diagram

[Generate the Mermaid diagram here following the instructions below]

---

## Users and Actors

[For each type of user/actor, create a subsection]

### [User Type Name]

**Role:** [What this user does with the system]

**Primary Actions:**

- [Action 1]
- [Action 2]
- [Action 3]

[Repeat for each user type - identify 2-4 user types]

---

## External Systems and Integrations

[For each external system, create a subsection]

### [External System Name]

**Purpose:** [Why does {project_name} integrate with this?]  
**Integration Type:** [API / Database / File System / Message Queue / etc.]  
**Data Flow:** [What data is exchanged and in which direction?]

[Repeat for each external system - identify 3-6 external systems]

---

## Mermaid Diagram Requirements

**IMPORTANT**: The System Context Diagram should appear **immediately after the System Overview section** and **before the Users and Actors section**. This ensures stakeholders see the visual overview before diving into details.

### CRITICAL - Mermaid Syntax Safety Rules

Follow these rules EXACTLY to ensure the diagram renders correctly:

1. **Node IDs**: Use only alphanumeric characters and underscores
   - ✓ Good: `System`, `User1`, `ExtDB`, `Payment_API`
   - ✗ Bad: `Payment-API`, `Ext DB`, `User(Admin)`

2. **Node Labels**:
   - If label contains spaces, colons, parentheses, or line breaks → wrap in double quotes
   - Always quote labels with `<br/>` tags
   - Escape internal quotes with `\"`
   - Example: `System["🛍️ {project_name}<br/>Main application server"]`

3. **Line breaks**: Use `<br/>` (NOT `\n`)

4. **Edge labels**: Can be simple text or quoted if they contain special chars
   - Example: `User -->|"Uses via web browser"| System`

5. **Icons**: Use emojis to make the diagram more engaging:
   - Users: 👤 or 👥
   - System (main): 🛍️ or 🎯 or 🖥️
   - External Systems: 🔗 or 🌐 or 📊 or 💾
   - APIs: 🔌
   - Databases: 💾 or 🗄️

### Required Diagram Structure

Create a `graph TB` (top-to-bottom) or `graph LR` (left-to-right) diagram with:

- User nodes on the left/top
- Main system in the center
- External systems on the right/bottom
- Clear directional arrows showing interactions

### Template Structure

**IMPORTANT**: Use standard markdown code fence with `mermaid` language identifier.
**DO NOT** use `<div class="mermaid">` HTML syntax.

**Correct fence format**:

- Open with: three backticks followed by `mermaid`
- Close with: three backticks

Example of correct syntax:

```

(Three backticks)mermaid
graph TB
    ...
(Three backticks)

```

Here's the structure to follow:

```

graph TB
    %% Define nodes
    User1["👤 [User Type]<br/>[Brief role description]"]
    User2["👤 [User Type]<br/>[Brief role description]"]

    System["🛍️ {project_name}<br/>[System purpose in 5-7 words]"]
    
    Ext1["🔗 [External System]<br/>[What it provides]"]
    Ext2["💾 [External System]<br/>[What it provides]"]
    Ext3["🌐 [External System]<br/>[What it provides]"]
    
    %% Define relationships
    User1 -->|"[Action]"| System
    User2 -->|"[Action]"| System
    
    System -->|"[Integration type]"| Ext1
    System -->|"[Integration type]"| Ext2
    System -->|"[Integration type]"| Ext3
    
    %% Optional: styling
    classDef userStyle fill:#e1f5ff,stroke:#01579b,color:#000
    classDef systemStyle fill:#fff3e0,stroke:#e65100,color:#000
    classDef externalStyle fill:#f3e5f5,stroke:#4a148c,color:#000
    
    class User1,User2 userStyle
    class System systemStyle
    class Ext1,Ext2,Ext3 externalStyle

```

**CRITICAL**: The Mermaid diagram MUST use standard markdown code fence (three backticks + `mermaid`), NOT `<div class="mermaid">` HTML tags.

### Diagram Guidelines

1. **Keep it focused**: Show 2-4 user types, 3-6 external systems maximum
2. **Use descriptive labels**: Each node should explain its role
3. **Show data flow direction**: Arrows indicate who initiates the interaction
4. **Be specific about integration types**: API, Database, File, Message Queue, etc.
5. **Make it visually appealing**: Use colors, emojis, and clear layout

### Example Node Formats

**Correct:**

```

User["👤 Content Editors<br/>Create and manage articles"]
System["🛍️ WordPress<br/>Content management platform"]
ExtDB["💾 MySQL Database<br/>Stores all content and configuration"]
ExtAPI["🔗 REST API<br/>Third-party integrations"]

```

**Incorrect:**

```

User[Content Editors (Admin)]  // Parens not quoted
System[WordPress: CMS]  // Colon not quoted
Ext-DB[MySQL]  // Hyphen in ID

```

---

## Analysis Guidelines

When analyzing the project files:

1. **Identify the core purpose**: What problem does this software solve?

2. **Find user types**: Look for:
   - User roles in documentation
   - Authentication/authorization hints
   - Different interfaces (admin vs user)
   - Typical personas for this domain

3. **Spot external systems**: Look for:
   - Database connections (MySQL, PostgreSQL, MongoDB, etc.)
   - API integrations (mentioned in config files)
   - File storage (S3, local filesystem)
   - Email services (SMTP, SendGrid, etc.)
   - Authentication providers (OAuth, LDAP, etc.)
   - Caching layers (Redis, Memcached)
   - Message queues (RabbitMQ, Kafka, etc.)
   - Payment gateways
   - Third-party services

4. **Understand integration patterns**:
   - Is it pulling data? Pushing data? Both?
   - Synchronous or asynchronous?
   - What's the primary communication protocol?

5. **Keep it high-level**: Level 1 is NOT about internal components - save that for Level 2/3

---

## Quality Checklist

Before outputting, verify:

- ✓ All Mermaid node IDs use only alphanumeric and underscores
- ✓ All node labels with spaces/special chars are quoted
- ✓ All `<br/>` tags are inside quoted labels
- ✓ System description is clear and specific
- ✓ User types are realistic for this domain
- ✓ External systems are actually mentioned in the files (not assumed)
- ✓ Diagram has visual appeal (colors, emojis, clear layout)
- ✓ Document follows the exact structure specified

---

## Output Format

Generate the **complete markdown document** following the structure above.

**CRITICAL - Mermaid Syntax**:

- Use standard markdown code fence: (three backticks)`mermaid` ... (three backticks)
- **DO NOT** use HTML `<div class="mermaid">` tags
- This is for standard markdown rendering

Do NOT include:

- Code fences around the entire document
- Commentary or explanations outside the document
- Multiple alternative versions

DO include:

- Proper markdown headers and formatting
- The complete Mermaid diagram with proper fences
- Specific details from the actual project files
- Professional, clear language suitable for stakeholders

---

Generate the C4 Level 1 documentation now.
