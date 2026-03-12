FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    libglpk-dev \
    prodigal \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./requirements.txt
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY pipeline ./pipeline
COPY pipeline.py ./pipeline.py
COPY src ./src
COPY mcp-server ./mcp-server
COPY docker ./docker
COPY data ./data

RUN mkdir -p /app/outputs

CMD ["python", "mcp-server/server.py"]