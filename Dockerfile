FROM debian:bookworm-slim

WORKDIR /project

COPY main.py requirements.txt ./
COPY tests/ tests/

RUN apt-get update && apt-get install -q --yes \
    python3 \
    python3-pip \
    firefox-esr \ 
    && pip install -q --no-cache-dir -r requirements.txt --break-system-packages \
    && rm -rf /var/lib/apt/lists/*
      
CMD ["python3", "main.py"]

