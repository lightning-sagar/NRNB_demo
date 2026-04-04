FROM python:3.10-slim

WORKDIR /app

RUN sed -i 's|http://deb.debian.org/debian|https://deb.debian.org/debian|g' /etc/apt/sources.list.d/debian.sources \
    && sed -i 's|http://deb.debian.org/debian-security|https://deb.debian.org/debian-security|g' /etc/apt/sources.list.d/debian.sources

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    diamond-aligner \
    git \
    libglpk-dev \
    prodigal \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./requirements.txt
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY apps ./apps
COPY agent ./agent
COPY pipeline/pipeline.py ./pipeline/pipeline.py
COPY pipeline/common.py ./pipeline/common.py
COPY src ./src
COPY mcp-server ./mcp-server
COPY docker ./docker
COPY data ./data
COPY cli_chat.py ./cli_chat.py
COPY opencode_agent.py ./opencode_agent.py

RUN mkdir -p /app/outputs

CMD ["python", "-m", "apps.mcp_server"]
