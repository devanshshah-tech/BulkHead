# Design decisions

Tradeoffs worth being able to defend in an interview.

## pgvector over a dedicated vector DB

Milvus/Qdrant are heavier, stateful, and bring their own operational surface — exactly what you don't want inside an airgap bundle you have to ship and patch. Postgres+pgvector keeps one datastore for vectors and metadata, uses HNSW indexes, and rides on tooling every platform team already runs. At this corpus scale, recall is indistinguishable; operability wins.

## Ollama with baked Q4_K_M, not a bigger model

The constraint isn't taste, it's arithmetic: free-tier ARM VMs and developer laptops have ~8–24 GB RAM, GitHub Release assets cap at 2 GiB per file, and airgapped clusters cannot pull weights at deploy time. Baking llama3.2:1b **Q4_K_M** (~805 MB, higher fidelity than the registry's q4_0) into a CPU-only Ollama image satisfies all three simultaneously. The Modelfile carries an explicit chat template because bare-GGUF imports don't inherit one in ollama 0.5.x — a subtle failure mode we hit and documented in [swap-the-model](../how-to/swap-the-model.md).

## Zarf/UDS packaging

The airgap story needs more than an image mirror: Helm charts, manifests, and weights must move as one signed, versioned unit with a single deploy command. Zarf packages per concern (mesh/data/inference/apps), UDS composes them into one bundle with dependency ordering. This overlaps deliberately with skills practiced professionally — but here it packages a working *application*, not just infrastructure.

## Tilt locally, ArgoCD for the demo

Tilt gives sub-minute feedback while developing; ArgoCD gives controlled reconciliation once something is worth keeping. Using one tool for both would optimize neither.

## lakeFS for corpus versioning

"What document was this answer grounded in?" is the question every enterprise RAG buyer asks first. Committing each ingestion run to lakeFS makes corpus state reproducible and auditable — git semantics for data.
