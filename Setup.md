# Flowscribe: Manual Proof of Concept Setup Guide

## Project Name: **Flowscribe**

*Automatically documenting open-source software architecture through visual flow diagrams*

---

## Project Structure

```
flowscribe/
├── docker-compose.yml
├── Dockerfile
├── README.md
├── .gitignore
├── docs/
│   └── TODO.md
├── analysis/
│   └── tools/
│       ├── python/
│       ├── php/
│       └── javascript/
├── projects/
│   └── [cloned repos go here]
└── output/
    └── [project-name]/
        ├── architecture.md
        ├── c4-diagrams/
        ├── flow-diagrams/
        └── metadata.json
```

---

## Quick Start

### 1. Clone and Setup

```bash
# Create project directory
mkdir flowscribe
cd flowscribe

# Create directory structure
mkdir -p analysis/tools/{python,php,javascript}
mkdir -p projects
mkdir -p output
mkdir -p docs
```

### 2. Create Docker Environment

Save the following as `docker-compose.yml`:

```yaml
#version: '3.8'
services:
  flowscribe:
    build: .
    container_name: flowscribe
    volumes:
      # Mount your repo root
      - ./:/workspace
    environment:
      # Pass from .env file or host environment
      - OPENROUTER_API_KEY=${OPENROUTER_API_KEY}
      - OPENROUTER_MODEL=${OPENROUTER_MODEL:-anthropic/claude-sonnet-4-20250514}
      # Optional: Custom Model Pricing (per 1M tokens)
      # Override if using negotiated rates or custom models
      - OPENROUTER_MODEL_INPUT_COST_PER_1M=${OPENROUTER_MODEL_INPUT_COST_PER_1M:-}
      - OPENROUTER_MODEL_OUTPUT_COST_PER_1M=${OPENROUTER_MODEL_OUTPUT_COST_PER_1M:-}
      # Optional: Unified pricing (if input/output costs are same)
      #- OPENROUTER_MODEL_COST_PER_1M=${OPENROUTER_MODEL_COST_PER_1M:-}
    env_file:
      - .env
    working_dir: /workspace
    stdin_open: true
    tty: true
    command: /bin/bash```
```

Save the following as `Dockerfile`:

```dockerfile
  FROM ubuntu:22.04

  # Avoid prompts during package installation
  ENV DEBIAN_FRONTEND=noninteractive

  # Install base dependencies (without nodejs/npm - we'll add them separately)
  RUN apt-get update && apt-get install -y \
      git \
      curl \
      unzip \
      wget \
      vim \
      tree \
      graphviz \
      python3 \
      python3-pip \
      php \
      php-cli \
      php-mbstring \
      php-xml \
      composer \
      && rm -rf /var/lib/apt/lists/*

  # Install Node.js 20.x from NodeSource
  RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
      && apt-get install -y nodejs \
      && rm -rf /var/lib/apt/lists/*

  # Install Python analysis tools
  RUN pip3 install --no-cache-dir \
      pyan3 \
      pylint \
      networkx \
      matplotlib \
      pyyaml \
      requests \
      pydeps

  # Install JavaScript analysis tools
  RUN npm install -g \
      madge \
      dependency-cruiser \
      jsdoc

  # Install PHP analysis tools (including Deptrac and Structurizr)
  RUN composer global require \
      phpstan/phpstan \
      squizlabs/php_codesniffer \
      qossmic/deptrac-shim \
      structurizr-php/structurizr-php

  # Add composer global bin to PATH
  ENV PATH="/root/.config/composer/vendor/bin:${PATH}"

  # Install Mermaid CLI
  RUN npm install -g @mermaid-js/mermaid-cli

  # Set working directory
  WORKDIR /workspace

  CMD ["/bin/bash"]
```

### 3. Build and Run

```bash
# Build the container
docker-compose build

# Start the container
docker-compose up -d

# Enter the container
docker-compose exec flowscribe bash
```

---

## Manual Analysis Process

### Phase 1: Pick Your First Project

**Example: Flask**

```bash
# Inside the container
cd /workspace/projects
git clone https://github.com/pallets/flask.git
cd flask
```

### Phase 2: Explore the Project

**Step 1: Understand the structure**

```bash
# Get a tree view (limit depth)
tree -L 3 -d

# Find entry points
find . -name "*.py" | head -20

# Look for main files
ls -la src/flask/
```

### Phase 2: Static Analysis

**Python Analysis Commands:**

```bash
# Single command does it all
python3 /workspace/scripts/flowscribe-analyze.py https://github.com/pallets/flask.git
```

Generates all the reports and everything into: /workspace/output/flask. Check the README.md to get started on the complete analysis.

## Verification Checklist

For each project you document:

- [ ] Project cloned and explored
- [ ] Entry points identified
- [ ] Static analysis run successfully
- [ ] C4 Level 1 diagram created
- [ ] C4 Level 2 diagram created
- [ ] At least 1 key flow documented
- [ ] Summary document written
- [ ] Diagrams render correctly (test in GitHub/VSCode)
- [ ] Manual verification against official docs
- [ ] Metadata.json filled out

---

## Quick Reference Commands

```bash
# Start working
docker-compose up -d
docker-compose exec flowscribe bash

# Clone a project
cd /workspace/projects
git clone [repo-url]

# Create output directory
mkdir -p /workspace/output/[project-name]

# Test Mermaid rendering (install locally)
mmdc -i diagram.md -o diagram.png

# Exit container
exit

# Stop container
docker-compose down
```
