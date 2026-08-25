# Airgap-Deployable RAG Platform — Execution Plan

**Goal:** Build a portfolio project that proves you can package and operate a full AI/RAG stack inside disconnected, GitOps-managed Kubernetes clusters — and make it freely, publicly viewable by recruiters without contradicting the "airgap" premise.

**Target roles:** AI Engineer / AI Solutions Engineer / Forward Deployed Engineer

**Core narrative for interviews:** "I built the thing FDEs actually ship — an AI capability packaged so a customer's disconnected, security-locked cluster can stand it up with one command, with full GitOps lifecycle management on top."

---

## 0. Naming & Framing (do this first)

**Chosen name: `bulkhead`** (repo: `bulkhead-rag`). Originally named `airlock`, renamed after WorkOS announced their own product called Airlock (an intent-based access control layer for AI agents) in August 2026 — different problem space entirely, but not worth the search-result collision with a funded, press-covered company's product. Bulkhead keeps the same "sealed compartment / isolation boundary" metaphor without the name clash.

Write a one-paragraph pitch now and put it at the top of the eventual README:

> "A production-style Retrieval-Augmented Generation platform designed to run fully disconnected. Ships as a single Zarf airgap bundle, deployed via ArgoCD GitOps, with mTLS-secured service mesh (Istio), reproducible dev tooling (mise), and versioned document corpora (lakeFS). Includes a live connected-mode demo and a downloadable airgap bundle you can run yourself."

This framing — **connected demo + downloadable airgap bundle** — is the key trick that resolves "airgap projects are hard to show recruiters." More in Phase 6.

### 0.1 Differentiate this from your AXE.AI internship work
Your resume already claims an 8-task mise CI/CD layer, a Zarf/UDS airgap bundle, and a pepr-mesh crash fix at AXE.AI. If this project's headline claims are "I built a mise CI/CD layer" and "I packaged an airgap bundle," it reads as *repeating* your internship, not *exceeding* it — a sharp interviewer will notice the overlap and ask why you rebuilt the same thing solo.

The project still uses mise, Zarf, and UDS (they're core to the story), but the **new, resume-worthy claims have to sit a level above what AXE.AI already covers**:
- AXE.AI: packaged infra components into a deployable bundle → **this project**: packages a full working *application* (RAG stack, not just infra) into that bundle, and adds the GitOps layer (ArgoCD) and IaC layer (Terraform) that weren't part of the internship scope
- AXE.AI: fixed a mesh crash reactively → **this project**: designs mTLS and traffic policy from scratch, proactively, as part of the initial architecture
- Net new versus AXE.AI entirely: RAG/retrieval architecture, gRPC/Protobuf service contracts, corpus versioning (lakeFS), GitOps reconciliation (ArgoCD), IaC (Terraform), and the free-tier public deployment story
- When writing the README, resume bullets, or talking about this in interviews, foreground the GitOps + IaC + RAG-architecture pieces first — the Zarf/UDS packaging is supporting detail, not the headline, since that's the part that overlaps with AXE.AI

### 0.2 A couple of existing "airgapped RAG" projects exist — know what they don't cover
A search turns up at least two prior examples worth knowing about before you write the README: a popular single-app Streamlit tool (PDF upload → local-model Q&A, Docker only, no orchestration) and a two-year-old blog walkthrough deploying Milvus on Kubernetes via a proprietary managed ML platform. Neither touches Zarf/UDS packaging, Istio, ArgoCD, Terraform, or a real multi-service architecture — they're single-app demos, not platform infrastructure. This means "airgapped RAG" alone isn't a novel enough headline (a recruiter searching that phrase will find prior art), so the README's first line should lead with the platform-engineering layer — packaging, GitOps, mesh security, IaC — not just "RAG that works offline."

---

## Phase 1 — Architecture & Repo Scaffolding (Days 1–3)

### 1.1 Define the system architecture
Components:
- **Ingestion service** (Python, FastAPI) — chunk & embed documents, write to vector store, version corpus in lakeFS
- **Vector store** — PostgreSQL + `pgvector` extension (simplest, most credible for enterprise contexts; avoid overusing OpenSearch dual-purpose here)
- **Object storage** — MinIO (stand-in for S3, holds raw docs + model artifacts)
- **RAG query API** — FastAPI (public REST) + internal gRPC to a retrieval service (shows you understand REST-at-edge / gRPC-internal patterns)
- **LLM inference** — a small local model server (e.g., Ollama or vLLM running a small quantized model) so the whole thing works **with zero external API calls** — this IS the airgap story
- **Metadata/audit DB** — PostgreSQL (separate schema/instance from vector store, or same instance different DB — decide based on how much "distinct systems" signal you want)
- **Docs site** — Docusaurus, deployed to GitHub Pages, containing architecture, runbooks, and "how to deploy this yourself" guides

### 1.2 Draw the architecture diagram
Do this before writing code. Use draw.io / Excalidraw. Save as SVG in `/docs/architecture/`. You will reuse this diagram in: README, Docusaurus site, and every interview.

### 1.3 Repo structure
```
bulkhead-rag/
├── apps/
│   ├── ingestion-service/       # FastAPI, Python
│   ├── query-api/                # FastAPI, Python
│   ├── retrieval-service/        # gRPC, Python or Go
│   └── inference/                # model server config (Ollama/vLLM)
├── proto/                         # .proto definitions for gRPC
├── infra/
│   ├── terraform/                 # cloud infra for the "connected demo"
│   ├── helm/                      # Helm charts per service
│   ├── zarf/                      # Zarf packages + airgap bundle definition
│   ├── uds/                       # UDS bundle config
│   └── istio/                     # mesh policies, mTLS, gateways
├── gitops/
│   └── argocd/                    # Application manifests, App-of-Apps
├── ci/
│   └── .github/workflows/         # CI/CD pipelines
├── .mise.toml                     # tool versions + task runner
├── docs/                          # Docusaurus site source
└── README.md
```

### 1.4 Tool version pinning with mise
Create `.mise.toml` pinning: python, go (if used), terraform, helm, kubectl, k3d/kind, zarf, uds-cli, argocd-cli, docker, tilt. Define `mise` tasks around what this project actually needs end to end — e.g. `mise run lint`, `mise run test`, `mise run build`, `mise run package`, `mise run dev` (runs `tilt up`), `mise run deploy:local`, `mise run deploy:demo` (Terraform + ArgoCD sync), `mise run deploy:airgap`. The task count and shape should follow the project's real needs, not match any prior task list — the point here is the GitOps/IaC tasks (deploy:demo) that go beyond pure packaging.

---

## Phase 2 — Core Application Services (Days 4–10)

### 2.1 Ingestion service (FastAPI, Python)
- Endpoint to upload docs → chunk → embed (use a small local embedding model, e.g. `sentence-transformers`, no external API) → write vectors to Postgres/pgvector
- Write raw source docs to MinIO
- Tag each ingestion run with a lakeFS commit so you can say "this answer traces back to corpus version X" — this is a strong, unusual, interview-worthy detail
- Unit tests with `pytest`

### 2.2 Retrieval service (gRPC)
- Define `.proto` contract: `Retrieve(query) -> List[Chunk]`
- Implement in Python or Go — pick Go here if you want a second language on the resume; otherwise Python is fine
- This is the piece that talks to Postgres/pgvector internally, not exposed publicly

### 2.3 Query API (FastAPI, public-facing)
- REST endpoint: `POST /query` — calls retrieval service (gRPC) then calls local inference server, returns grounded answer + citations (which doc chunks were used)
- Add a `/healthz` and `/readyz` — signals you think about production readiness, not just demos
- Optional: add a GraphQL endpoint alongside REST if you want to show both (`strawberry-graphql` is a clean choice) — don't over-engineer, one clean GraphQL query is enough to prove the skill

### 2.4 Inference
- Run Ollama or vLLM serving a small open model (e.g. Llama 3.2 3B / Phi-3-mini) — small enough to run on a free-tier VM or even a laptop, which matters for the free-deployment phase later

### 2.5 Containerize everything
- One `Dockerfile` per service, multi-stage builds, non-root user, minimal base images (distroless or `python:slim`)
- Push images to **GitHub Container Registry (ghcr.io)** — free, unlimited public image storage

---

## Phase 3 — Local Kubernetes Environment (Days 11–14)

### 3.1 Local cluster
Use **k3d** or **kind** for local dev (lightweight, matches k3s used in the free cloud deployment later — keeps parity).

### 3.2 Helm charts
- One chart per service, values files per environment (`values-local.yaml`, `values-demo.yaml`, `values-airgap.yaml`)
- Use an umbrella chart or Helmfile to compose all services together

### 3.3 Inner dev loop with Tilt
- Add a `Tiltfile` wiring up all services (ingestion, query-api, retrieval, inference) against the local k3d/kind cluster — watches source, rebuilds images, redeploys automatically, with a live status UI
- Add `mise run dev` as a thin wrapper around `tilt up`, keeping the mise-task-runner story consistent with the rest of the project
- This is distinct from ArgoCD on purpose: Tilt is for fast iteration while building locally; ArgoCD (Phase 5) is for controlled reconciliation of the deployed demo. Worth stating that distinction explicitly in interviews — it shows you understand different points in the delivery lifecycle, not just "I know two deployment tools"

### 3.4 Istio service mesh
- Install Istio in the local cluster
- Enable strict mTLS between all internal services (`PeerAuthentication`)
- Define `VirtualService`/`Gateway` for the public query API
- Add a simple traffic policy demo (e.g., retries, timeouts) — small but shows real mesh usage, not just "I installed Istio"

### 3.5 Verify locally
Run the full flow: ingest a doc → query it → get a grounded answer with citations, all inside the local cluster, zero external calls.

---

## Phase 4 — Packaging for Airgap (Days 15–19)

This is the part that overlaps most with your AXE.AI work, so keep it as supporting infrastructure, not the headline claim — the differentiators are Phase 1 (RAG architecture), Phase 5 (GitOps/IaC), and Phase 6 (public deployment).

### 4.1 Zarf packages
- Create a Zarf package per component (ingestion, query-api, retrieval, inference, postgres, minio)
- Include the model weights and any pip/OS dependencies inside the package so nothing needs internet at deploy time

### 4.2 UDS bundle
- Compose the Zarf packages into a single UDS bundle — one command deploys the entire platform to a fresh, disconnected cluster
- Document the exact command in the README: `uds deploy bulkhead-rag-bundle.tar.zst`

### 4.3 Prove the airgap claim
- Spin up a cluster with **no outbound internet** (network policy blocking egress, or literally an offline VM) and deploy only from the bundle
- Record this — screen capture — this becomes your strongest interview demo clip, more convincing than a live link

---

## Phase 5 — CI/CD and GitOps (Days 20–24)

### 5.1 CI (GitHub Actions — free for public repos)
Pipeline stages: lint → unit test → build images → push to ghcr.io → build Zarf packages → build UDS bundle → publish bundle as a GitHub Release artifact → build Docusaurus site → deploy to GitHub Pages

### 5.2 ArgoCD (GitOps for the connected demo)
- Install ArgoCD on the target cluster (the free cloud VM from Phase 6)
- App-of-Apps pattern: one root Argo `Application` that manages all service `Applications`
- Point ArgoCD at your Helm charts/values in Git — merging to `main` reconciles the live demo automatically (nice, concrete "I built a real deployment pipeline" story)

### 5.3 Terraform
- Provision whatever cloud pieces the **connected demo** needs (see Phase 6) — VM, network, DNS record
- Keep state in a free backend (Terraform Cloud free tier, or just local state committed nowhere and documented as "run locally" — free-tier Terraform Cloud is cleaner for showing remote state competency)
- Skip Terragrunt unless you want to show multi-environment DRY patterns — optional stretch goal, not core to the story; add only if time remains (see Stretch Goals)

---

## Phase 6 — Free, Public Deployment Strategy

The tension: this project's selling point is "disconnected deployment," but recruiters need a public, zero-friction way to see it. Solve this with **three access tiers**, all free:

### Tier 1 — Live connected demo (primary, for recruiters who just click a link)
- **Host:** Oracle Cloud Infrastructure **Always Free tier** — 4 Arm-based OCPUs + 24GB RAM VM, free forever (no expiring trial credits). This is the best free option that can actually run k3s + Istio + your services without resource starvation.
  - Alternative free options if OCI signup friction is an issue: Fly.io free allowances (smaller, may need to trim services), or a single Civo/Vultr/DigitalOcean referral credit VM (time-limited, not truly free forever — use only as backup)
- **Kubernetes:** install **k3s** on the free VM (lightweight, production-grade, low resource footprint — fits the free tier's constraints)
- **Ingress/TLS:** use a **Cloudflare Tunnel** (free) from the VM — gives you a public HTTPS URL without opening firewall ports or paying for a load balancer or TLS cert. This is the standard free way to expose a home/small VM safely.
- **DNS:** free subdomain via Cloudflare, or a free `.xyz`/`.tech` domain from providers with free-domain promos, or simply use the `trycloudflare.com` / a custom domain you already may own
- **What's running here:** the full stack via the ArgoCD-managed Helm deployment (Phase 5.2) — this is the "connected mode," using the same Helm charts as the airgap bundle, just without the Zarf/UDS packaging step. Same codebase, two delivery mechanisms — a good talking point ("the packaging is the only thing that changes between connected and disconnected delivery").

### Tier 2 — Downloadable airgap bundle (for technical reviewers who want proof)
- Publish the `.tar.zst` UDS bundle as a **GitHub Release** asset (free, no size issues for reasonable model sizes if you pick a small quantized model)
- README includes exact steps: spin up any local kind/k3d cluster, run one `uds deploy` command, no internet required after download
- This is what you demo live in an interview if asked "prove it's really airgapped" — pull up a terminal, kill network access, deploy from the bundle

### Tier 3 — Recorded proof (zero infra dependency, always works)
- A 3–5 minute screen recording (Loom or asciinema — both free) showing: airgapped cluster, no egress, single-command deploy, working query with citations
- Embed this in the Docusaurus site and README — this is your fallback if the live demo VM is ever down (free tiers do occasionally get reclaimed/rate-limited, so never depend on Tier 1 alone)

### Docs site
- **Docusaurus**, deployed via **GitHub Pages** (completely free, custom domain optional)
- Content: architecture diagram, "why this exists" framing, runbooks for both connected and airgap deploys, and the embedded demo recording

### Cost recap (should be $0)
| Component | Service | Cost |
|---|---|---|
| Compute | OCI Always Free VM | $0 |
| Container registry | GHCR | $0 (public repos) |
| CI/CD | GitHub Actions | $0 (public repos) |
| GitOps | ArgoCD (self-hosted on free VM) | $0 |
| DNS/TLS | Cloudflare Tunnel + free DNS | $0 |
| Docs hosting | GitHub Pages | $0 |
| Terraform state | Terraform Cloud free tier | $0 |
| Bundle distribution | GitHub Releases | $0 |

---

## Phase 7 — Polish for Recruiters (Days 25–28)

- **README** structure: one-paragraph pitch → architecture diagram → live demo link → "prove it's airgapped" recording → local run instructions → tech stack table mapped explicitly to job-relevant skills
- **Tech stack table** — spell out the mapping recruiters skim for, e.g.:
  | Skill area | What's used | Where |
  |---|---|---|
  | Platform packaging | Zarf, UDS | `infra/zarf`, `infra/uds` |
  | Local dev experience | Tilt, k3d/kind | `Tiltfile` |
  | Service mesh | Istio (mTLS, traffic policy) | `infra/istio` |
  | GitOps | ArgoCD | `gitops/argocd` |
  | IaC | Terraform | `infra/terraform` |
  | CI/CD | GitHub Actions, mise | `.github/workflows`, `.mise.toml` |
  | Backend | FastAPI, gRPC, Protobuf | `apps/*` |
  | Data | PostgreSQL/pgvector, MinIO, lakeFS | `apps/ingestion-service` |
  | Docs | Docusaurus | `docs/` |
- Pin the repo on GitHub profile, add topics/tags for discoverability
- Write a short **"Design Decisions" doc** explaining tradeoffs (why pgvector over a dedicated vector DB, why k3s not full K8s for the demo, etc.) — this is what separates "portfolio project" from "resume-driven development" in an interviewer's eyes

---

## Stretch Goals (only after core is solid)

- Terragrunt: restructure Terraform into multi-env (dev/demo/airgap-sim) DRY modules
- Add OpenSearch or Elasticsearch as an alternative retrieval backend behind a feature flag, to show polyglot persistence awareness
- Add a canary rollout demo using Istio traffic splitting between two model versions (ties into the "Agent Deployment/Canary Platform" idea from earlier — natural v2 of this project)
- Add Apache Iceberg + MinIO as a "cold storage / analytics" layer for ingested-document metadata, queryable via Spark — shows Big Data breadth without diluting the core RAG story

---

## Phase 8 — Stretch Goal: Sandboxed Agentic Layer (NemoClaw)

**Only attempt after Phases 1–7 are solid and demoable.** This is explicitly a stretch goal, not core scope — treat it as an "if time and stability allow" addition, not a dependency for the main story.

### 8.1 What it is and why it fits
NVIDIA's **NemoClaw** is an open-source runtime layer (built on **OpenShell**) that sandboxes autonomous AI agents: default-deny network policy, filesystem access scoped to specific directories, and inference routed through a policy-gated "Privacy Router" (local model vs. cloud model, by rule). It's very new — announced at GTC 2026, still alpha — so treat it as an exploratory addition, not a load-bearing one.

The fit isn't cosmetic: your whole project's thesis is "constrain what's allowed to leave the boundary." NemoClaw applies that same philosophy one layer up — from network-level airgap constraints (Zarf/UDS/Istio) to agent-behavior constraints (default-deny sandboxing). Same story, one level higher in the stack.

**A sharper way to frame this in interviews:** WorkOS shipped a product called Airlock in August 2026 (unrelated to this project, prompted the rename to `bulkhead`) that governs what a *cloud-connected* agent is allowed to do to third-party SaaS tools — Gmail, Linear, Notion — via intent evaluation and credential brokering. It's a genuinely good idea, and it's explicitly built for agents that can reach WorkOS's cloud service. This stretch goal is the analogous problem in the one environment WorkOS's approach can't reach: a fully disconnected cluster with no path to any cloud authorization service at all. Saying that out loud in an interview — "here's a real product solving this for connected agents, and here's what the same idea looks like when you can't call out to the cloud in the first place" — is a strong, current signal that you're tracking the field, not just listing tools.

### 8.2 Where it plugs in
Not into the core RAG query path — a plain retrieve-then-generate flow has no real "agent" behavior worth sandboxing. It fits if you add a **tool-calling agent layer** on top of the existing platform, e.g. an agent that can:
- Query the vector store / retrieval service on the user's behalf
- Trigger a re-ingestion job against a new document
- Call a small number of scoped internal tools

Run that agent inside an OpenShell sandbox via NemoClaw, with network policy scoped to *only* your internal services (query-api, retrieval-service) — nothing else reachable, no exceptions. Pair it with local model routing through the Privacy Router so the whole tool-calling loop stays inside the airgap boundary, consistent with the rest of the platform.

### 8.3 Before committing time to this
- Confirm NemoClaw/OpenShell actually runs on a plain Linux **ARM** host (your free-tier OCI VM) — its docs lean toward DGX/WSL in places, and you don't want to discover a hard GPU dependency after you've built a demo around it
- Because it's alpha, budget real debugging time and don't block the core project's timeline on it
- If it doesn't pan out cleanly, it's still fine as a **"Future Work" talking point** in the README/design-decisions doc — "the next layer I'd add is agent-level sandboxing via something like NemoClaw/OpenShell" is a legitimate, forward-looking answer in an interview even if unbuilt

### 8.4 If it works, the resume-bullet-shaped outcome looks like
> "Extended the platform with a tool-calling agent sandboxed via NVIDIA NemoClaw/OpenShell, enforcing default-deny network policy so agent tool-calls could only reach internal services, with inference routed entirely through a local model to preserve the airgap boundary."

---

## Suggested Timeline Summary

| Phase | Days | Output |
|---|---|---|
| 0–1: Framing & scaffolding | 1–3 | Repo, architecture diagram, mise tasks |
| 2: Core services | 4–10 | Working ingestion/retrieval/query APIs locally |
| 3: Local K8s + Istio | 11–14 | Full stack running in local cluster with mTLS |
| 4: Airgap packaging | 15–19 | Zarf/UDS bundle, proven offline deploy |
| 5: CI/CD + GitOps | 20–24 | GitHub Actions pipeline, ArgoCD-managed demo |
| 6: Free public deployment | (overlaps with 5) | Live demo URL, release bundle, recording |
| 7: Polish | 25–28 | README, docs site, design-decisions doc |

~4 weeks part-time is realistic. Ship Phases 1–4 even if 5–7 slip — a locally-provable airgap bundle with a good recording is already a strong interview artifact on its own.
