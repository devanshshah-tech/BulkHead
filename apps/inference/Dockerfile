# Ollama with the model baked in, stripped to CPU-only.
# The CPU runner is compiled into /bin/ollama; every GPU library in the
# upstream image (/usr/lib/ollama/*cuda*) is dead weight for our deployments.
# Airgap deployments never touch a model registry.
FROM ollama/ollama:0.5.7 AS source

ENV OLLAMA_MODELS=/models

RUN /bin/ollama serve & \
    SERVER_PID=$!; \
    for i in $(seq 1 30); do curl -sf http://127.0.0.1:11434/api/tags >/dev/null && break; sleep 1; done; \
    /bin/ollama pull llama3.2:3b; \
    kill $SERVER_PID; \
    wait $SERVER_PID 2>/dev/null || true; \
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
