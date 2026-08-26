# Ollama with the model baked in, stripped to CPU-only.
# Weights come straight from HuggingFace at build time (a Q4_K_M GGUF — smaller
# AND higher fidelity than the registry's q4_0 tag, which keeps the airgap
# bundle under GitHub Releases' 2GiB asset cap). `ollama create` in this
# builder stage converts them into the on-disk model store the runtime serves;
# no model pulls happen at deploy time.
# The CPU runner is compiled into /bin/ollama; every GPU library in the
# upstream image is dead weight for our CPU-only deployments.
FROM ollama/ollama:0.5.7 AS source

ENV OLLAMA_MODELS=/models \
    OLLAMA_HOST=127.0.0.1:11434

COPY Modelfile /tmp/Modelfile

RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates curl \
    && rm -rf /var/lib/apt/lists/* \
    && mkdir -p /models \
    && curl -fL --retry 3 -o /tmp/model.gguf \
        "https://huggingface.co/bartowski/Llama-3.2-1B-Instruct-GGUF/resolve/main/Llama-3.2-1B-Instruct-Q4_K_M.gguf"

# Convert the GGUF into ollama's model store (needs a brief server in-builder).
RUN set -eux; \
    ollama serve & pid=$!; \
    for i in $(seq 1 60); do \
      curl -sf http://127.0.0.1:11434/api/tags >/dev/null && break; \
      sleep 1; \
    done; \
    ollama create llama3.2:1b -f /tmp/Modelfile; \
    ollama list; \
    kill "$pid"; \
    chmod -R g+rw /models

FROM ubuntu:24.04

RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates curl \
    && rm -rf /var/lib/apt/lists/*

COPY --from=source /bin/ollama /usr/local/bin/ollama
COPY --from=source /models /models

ENV OLLAMA_MODELS=/models \
    OLLAMA_HOST=0.0.0.0

EXPOSE 11434
ENTRYPOINT ["/usr/local/bin/ollama"]
CMD ["serve"]
