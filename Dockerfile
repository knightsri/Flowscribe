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