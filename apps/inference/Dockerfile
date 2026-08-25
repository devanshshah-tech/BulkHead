# Ollama with the model baked in, stripped to CPU-only.
# Model blobs are pulled directly from registry.ollama.ai (no server needed at
# build time — this keeps multi-arch builds deterministic under QEMU).
# The CPU runner is compiled into /bin/ollama; every GPU library in the
# upstream image is dead weight for our CPU-only deployments.
FROM ollama/ollama:0.5.7 AS source

ENV OLLAMA_MODELS=/models

RUN apt-get update && apt-get install -y --no-install-recommends jq ca-certificates curl \
    && rm -rf /var/lib/apt/lists/* \
    && mkdir -p /models/manifests/registry.ollama.ai/library/llama3.2 /models/blobs \
    && curl -sfL \
        -H 'Accept: application/vnd.docker.distribution.manifest.v2+json, application/vnd.ollama.image.manifest.v1+json' \
        https://registry.ollama.ai/v2/library/llama3.2/manifests/1b \
        -o /models/manifests/registry.ollama.ai/library/llama3.2/1b \
    && jq -r '.config.digest, (.layers[] | .digest)' /models/manifests/registry.ollama.ai/library/llama3.2/1b \
       | while read -r digest; do \
           curl -sfL "https://registry.ollama.ai/v2/library/llama3.2/blobs/${digest}" \
             -o "/models/blobs/$(echo "${digest}" | tr ':' '-')"; \
         done \
    && chmod -R g+rw /models

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
