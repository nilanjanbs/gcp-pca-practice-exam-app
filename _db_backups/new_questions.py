#!/usr/bin/env python3
"""Append 20 challenging case-study questions (q031-q050) to database.json.
Each question is tied to one of the 4 PCA 2026 case studies:
  - EHR Healthcare
  - Helicopter Racing League (HRL)
  - Mountkirk Games
  - TerramEarth
Distractors are intentionally close to challenge architectural judgement.
"""
import json, sys, os, shutil, datetime

DB = os.path.join(os.path.dirname(__file__), '..', 'database.json')
DB = os.path.abspath(DB)

NEW_QUESTIONS = [
    # ============== EHR Healthcare (5) ==============
    {
        "id": "q031",
        "domain": "Designing & Planning",
        "diff": "challenging",
        "text": "EHR Healthcare Case Study: EHR is migrating its monolithic patient-records platform from on-prem Oracle RAC to Google Cloud. Requirements: globally consistent reads/writes for clinicians across 3 continents, ACID transactions across patient/encounter/medication tables, RPO=0, automatic regional failover with RTO < 60s, and BAA-eligible HIPAA coverage. The team also wants to keep PostgreSQL dialect to minimize ORM rewrites. Which design satisfies ALL constraints?",
        "opts": [
            "AlloyDB for PostgreSQL with cross-region read pools and a primary in us-central1, with a documented failover playbook to a secondary cluster in europe-west4",
            "Cloud SQL for PostgreSQL Enterprise Plus with HA in us-central1 and cross-region read replicas in europe-west4 and asia-east1",
            "Spanner with PostgreSQL interface configured as a multi-region instance (nam-eur-asia1) with leader placement tuned to clinician geography",
            "BigQuery in a multi-region location with FOR SYSTEM_TIME AS OF for point-in-time reads and streaming inserts from a Cloud Run write tier"
        ],
        "answer": 2,
        "explanation": "Only Spanner offers externally-consistent ACID transactions across continents with RPO=0 and automatic regional failover (multi-region configurations like nam-eur-asia1). The PostgreSQL interface preserves the dialect. AlloyDB cross-region read pools are async (RPO > 0) and require explicit cluster failover. Cloud SQL HA is regional only; cross-region replicas are asynchronous. BigQuery is OLAP, not transactional.\n\n\ud83d\udd0d Targeted Search: 'Spanner multi-region nam-eur-asia1 PostgreSQL interface', 'AlloyDB cross-region replication RPO'."
    },
    {
        "id": "q032",
        "domain": "Security & Compliance",
        "diff": "challenging",
        "text": "EHR Healthcare Case Study: A new analytics workload must read de-identified PHI from BigQuery for population-health research. Requirements: PHI must never leave a defined regulatory boundary, researchers authenticate via the corporate IdP only, the dataset must be unreadable even by Google operators, and any export attempts to non-approved projects must be blocked at the perimeter level. Which combination meets ALL requirements?",
        "opts": [
            "Cloud DLP de-identification on ingest, BigQuery dataset with column-level CMEK using Cloud KMS, Workforce Identity Federation with the corporate IdP, and a VPC Service Controls perimeter around BigQuery and Cloud Storage",
            "Cloud DLP de-identification on ingest, BigQuery dataset with default Google-managed encryption, IAM groups synced from Cloud Identity, and Organization Policy 'restrictedDomains' on resource sharing",
            "Manual de-identification in Dataflow, BigQuery External Connection to a Cloud Storage bucket with CSEK keys, SAML SSO, and BigQuery authorized views",
            "Cloud DLP de-identification on ingest, BigQuery with Cloud External Key Manager (EKM) keys, Workforce Identity Federation, and a VPC Service Controls perimeter that includes BigQuery, Cloud Storage, and Cloud KMS"
        ],
        "answer": 3,
        "explanation": "EKM holds keys outside Google's control plane, so even Google operators can't unilaterally read data — the strongest 'unreadable by Google' control. CMEK keys live in Google KMS and are accessible to Google operators in extreme circumstances. VPC SC must include the KMS service in the perimeter to prevent key-egress as a side-channel. Workforce Identity Federation lets external IdP users get Google credentials without provisioning Cloud Identity accounts. Restricted domains alone won't stop perimeter exfiltration.\n\n\ud83d\udd0d Targeted Search: 'Cloud External Key Manager BigQuery', 'VPC Service Controls KMS perimeter', 'Workforce Identity Federation BigQuery'."
    },
    {
        "id": "q033",
        "domain": "Managing Implementation",
        "diff": "challenging",
        "text": "EHR Healthcare Case Study: The team must migrate 800 TB of historical DICOM imaging from on-prem NAS to Google Cloud over a 100 Mbps internet link. The migration window is 90 days. Requirements: data integrity verification, encryption in transit, ability to resume on failure, and minimum impact on production radiology systems. Which migration approach is best?",
        "opts": [
            "Storage Transfer Service over public internet using a Transfer Agent on a Compute Engine VM, scheduled during off-hours with bandwidth throttling and checksum verification",
            "gsutil rsync from on-prem to a Cloud Storage Standard bucket, run nightly with a -m flag for parallel transfers and -c for checksum",
            "Transfer Appliance (multiple TA40 / TA300 units), shipped to Google for ingestion into Cloud Storage, with automated checksum and a final delta sync via Storage Transfer Service",
            "Cloud Storage FUSE-mount the on-prem NAS to a GKE pod and use parallel rsync jobs with HMAC keys"
        ],
        "answer": 2,
        "explanation": "At 100 Mbps, 800 TB would take ~750 days theoretically — far over the 90-day window. Transfer Appliance physically ships data and ingests it directly into Cloud Storage with built-in encryption and checksums. After bulk seed, Storage Transfer Service handles the delta of new images created during shipping. Gsutil and STS-over-internet would saturate the link and miss the deadline. Cloud Storage FUSE is for runtime access, not bulk migration.\n\n\ud83d\udd0d Targeted Search: 'Transfer Appliance DICOM migration', 'Storage Transfer Service delta sync after Transfer Appliance'."
    },
    {
        "id": "q034",
        "domain": "Reliability & Operations",
        "diff": "challenging",
        "text": "EHR Healthcare Case Study: Clinical decision-support APIs must meet a 99.95% availability SLO. The team currently runs them on regional GKE in us-central1 with PodDisruptionBudgets and multi-zonal node pools. Recent reviews flagged a single-region failure mode. Which change MOST efficiently elevates availability while preserving the existing CI/CD pipeline?",
        "opts": [
            "Convert the cluster to GKE Autopilot in the same region; rely on Google-managed control plane redundancy",
            "Deploy an identical regional cluster in us-east4, place a global external Application Load Balancer with a multi-cluster Gateway and configure traffic policies for active-active with health-check-driven failover",
            "Migrate the workload to Cloud Run multi-region with Serverless NEG behind a global LB",
            "Add a third zone to the existing regional cluster and increase replica counts; maintain a passive cold cluster in us-east4 for DR"
        ],
        "answer": 1,
        "explanation": "Multi-cluster Gateway with the global external ALB delivers active-active across regions, automatic health-check-based failover, and works with the existing GKE-based pipeline (manifests + Argo/Flux deploy to both clusters). Autopilot doesn't change failure domains. Cloud Run is a re-platform, not a minimal change. Adding zones is still single-region; cold standby misses RTO targets and underuses capacity.\n\n\ud83d\udd0d Targeted Search: 'GKE multi-cluster Gateway global ALB', 'GKE multi-region active-active'."
    },
    {
        "id": "q035",
        "domain": "Security & Compliance",
        "diff": "challenging",
        "text": "EHR Healthcare Case Study: A new ML pipeline trains a sepsis-prediction model on PHI in BigQuery. The InfoSec team requires: training data must never be cached on persistent disks outside the regulatory perimeter; model artifacts must be encrypted with customer-managed keys; the training job must run in a dedicated tenant with hardware-level memory isolation. Which Vertex AI configuration meets ALL three requirements?",
        "opts": [
            "Vertex AI custom training job on N2 machines with CMEK on the staging bucket; output models to a CMEK-encrypted Vertex AI Model Registry",
            "Vertex AI custom training job on Confidential VMs (N2D AMD SEV) with CMEK on the staging bucket and Model Registry, executed inside a VPC SC perimeter that includes Vertex AI, Cloud Storage, and KMS",
            "Vertex AI Pipelines on standard A2 GPUs with CMEK and shielded VM enabled at the node-pool level",
            "Vertex AI Workbench user-managed notebook with disk encryption via CSEK and a private endpoint"
        ],
        "answer": 1,
        "explanation": "Confidential VMs (N2D AMD SEV / C3 Intel TDX) provide hardware memory encryption — memory is encrypted with a key the host can't read. CMEK protects artifacts, and VPC SC blocks data-egress paths. Shielded VMs verify boot integrity but don't encrypt RAM. CSEK on a notebook disk doesn't address training-job tenant isolation.\n\n\ud83d\udd0d Targeted Search: 'Vertex AI Confidential VMs custom training', 'VPC Service Controls Vertex AI perimeter'."
    },

    # ============== Helicopter Racing League (5) ==============
    {
        "id": "q036",
        "domain": "Designing & Planning",
        "diff": "challenging",
        "text": "Helicopter Racing League (HRL) Case Study: HRL streams live 4K race footage to 30M global viewers with real-time AI-generated overlays (predicted finish order updated each lap). Requirements: end-to-end glass-to-glass latency under 4 seconds, regional regulatory compliance for EU viewers (data residency), and graceful degradation if the AI inference tier becomes unavailable. Which architecture is correct?",
        "opts": [
            "Live Stream API → Media CDN globally → Cloud Run inference for overlays — with the inference output spliced into the manifest at the edge; per-region origin shielding in EU and US, and a fallback profile that omits overlays if inference latency exceeds an SLO",
            "MediaLive on-prem → Cloud Storage → Cloud CDN → Vertex AI Online Prediction in a single global endpoint with multi-region failover",
            "Live Stream API with global multi-region endpoints → Cloud CDN → Vertex AI Online Prediction (regional) — overlays embedded at origin only",
            "Pub/Sub for video frames → Dataflow → Cloud Storage → Cloud CDN with a single global endpoint"
        ],
        "answer": 0,
        "explanation": "Media CDN is purpose-built for high-throughput live video with sub-second edge latency and regional shielding for residency. Splicing overlays at the edge keeps the AI tier off the critical path; the SLO-driven fallback profile preserves the stream when inference degrades. Cloud CDN is general-purpose and lacks live-streaming optimizations like LL-HLS chunked transfer. Pub/Sub→Dataflow is not a video pipeline. Embedding overlays at origin defeats latency goals.\n\n\ud83d\udd0d Targeted Search: 'Media CDN live streaming', 'Live Stream API low-latency HLS', 'Media CDN regional shielding'."
    },
    {
        "id": "q037",
        "domain": "Analyzing & Optimizing",
        "diff": "challenging",
        "text": "Helicopter Racing League (HRL) Case Study: HRL's data team runs ad-hoc queries on 5 PB of telemetry in BigQuery. Recent costs spiked. Analysis shows: 70% of queries scan partitions that are <30 days old, queries are interactive and bursty during race weekends, and 15% of cost is from cross-project data movement for analytics dashboards. Which set of changes will MOST reduce cost while preserving query performance?",
        "opts": [
            "Move all data to BigQuery Editions (Enterprise Plus) with autoscaling slots, partition all tables by ingestion time, and use BI Engine with reservations for dashboards",
            "Switch to BigQuery Editions (Enterprise) with autoscaling slot pools, enable partition pruning via partition_filter requirement, configure table clustering on race_id+lap, and use Authorized Views or BigQuery sharing (Analytics Hub) instead of cross-project copies",
            "Stay on on-demand pricing, add scheduled materialized views nightly, and move dashboards to Looker Studio with extract-mode caching",
            "Move dashboards to Cloud SQL by exporting nightly aggregates, and keep BigQuery only for raw data; partition by date"
        ],
        "answer": 1,
        "explanation": "Editions Enterprise + autoscaling matches the bursty, race-weekend pattern (you pay for slots actually used). Required partition_filter prevents accidental full-table scans. Clustering on race_id+lap matches access patterns. Analytics Hub publishes datasets in-place — eliminating 15% cross-project copy cost. BI Engine alone doesn't address cost. Cloud SQL for dashboards loses scale and freshness. Materialized views help but don't fix the slot pricing model.\n\n\ud83d\udd0d Targeted Search: 'BigQuery Editions autoscaling slots', 'Analytics Hub vs cross-project copy', 'BigQuery require_partition_filter'."
    },
    {
        "id": "q038",
        "domain": "Designing & Planning",
        "diff": "challenging",
        "text": "Helicopter Racing League (HRL) Case Study: The leaderboard service must show race standings to all viewers with at most 200ms staleness, support 500k QPS reads globally, and update from a write tier in europe-west1 (where the race control room is) at >10k writes/sec. Which design is BEST?",
        "opts": [
            "Cloud Spanner multi-region (eur6) with leader in europe-west1; read replicas in us-east1 and asia-northeast1; clients use stale reads with bounded staleness of 200ms",
            "Firestore in Native mode multi-region (eur3) with denormalized leaderboard documents; clients use real-time listeners",
            "Memorystore for Redis Cluster in europe-west1 with read replicas; clients connect via PSA in each region; cross-region writes via Cloud Tasks fan-out",
            "Bigtable in a multi-cluster routing topology with app profiles for read-only replicas; writes target the europe-west1 cluster"
        ],
        "answer": 0,
        "explanation": "Spanner multi-region with bounded-staleness reads serves replicas locally without quorum-cost — meeting 200ms staleness with global reads. Schema-on-write SQL fits leaderboard ranks. Firestore is great for denormalized docs but has lower per-region read throughput and limited cross-region read latency guarantees. Memorystore Redis isn't multi-regional natively. Bigtable lacks SQL ranking semantics and bounded-staleness reads aren't the typical pattern for ranked leaderboards.\n\n\ud83d\udd0d Targeted Search: 'Spanner bounded staleness reads multi-region', 'Spanner eur6 configuration'."
    },
    {
        "id": "q039",
        "domain": "Managing & Provisioning",
        "diff": "challenging",
        "text": "Helicopter Racing League (HRL) Case Study: The video render farm produces post-race highlight reels using FFmpeg with NVIDIA GPUs. Jobs are bursty (large bursts after each race), tolerate preemption, and need GPU availability across multiple regions to hit a 4-hour SLA. Which Google Cloud architecture is MOST cost-efficient while meeting the SLA?",
        "opts": [
            "GKE Standard clusters with GPU node pools, cluster autoscaler, Spot VMs, Pod priority classes, and PodDisruptionBudgets across us-central1, us-east1, and europe-west4",
            "Cloud Run with a custom GPU container image and concurrency=1, scaled by region",
            "Batch on Spot VMs with multi-region job templates targeting GPU machine types, configured with task retries and a placement policy that fans out across regions when capacity is constrained",
            "Compute Engine MIGs with stateful disks, a custom autoscaler triggered by Pub/Sub queue depth, and committed-use discounts on T4 GPUs"
        ],
        "answer": 2,
        "explanation": "Batch is purpose-built for bursty, preemptible-tolerant batch jobs and natively supports multi-region capacity placement and Spot VMs. Task retries handle preemption. GKE Standard works but adds cluster-management overhead and still needs orchestration tooling. Cloud Run GPU is for serving, not long batch. MIG with CUDs locks in spend that doesn't fit a bursty pattern.\n\n\ud83d\udd0d Targeted Search: 'Google Cloud Batch GPU Spot multi-region', 'Batch placement policy Spot'."
    },
    {
        "id": "q040",
        "domain": "Reliability & Operations",
        "diff": "challenging",
        "text": "Helicopter Racing League (HRL) Case Study: HRL's race-day operations team needs an SLO-driven alerting model. The current setup pages on every error spike, leading to alert fatigue. Requirements: alerts must reflect real user impact, fast burn during incidents, and slow burn during sustained low-grade degradation. Which alerting strategy aligns with Google's SRE guidance?",
        "opts": [
            "A single threshold alert at 99.5% availability over a 5-minute window with high-priority paging",
            "Burn-rate alerts using two windows: a fast window (5 min, 14.4x burn rate) for high-severity pages and a slow window (1 hour, 6x burn rate) for ticket-only alerts; both grounded in a 99.9% availability SLO over 30 days",
            "Static thresholds on CPU, memory, latency p99, and error count with paging on any threshold breach",
            "Anomaly detection on request rate via Cloud Monitoring and pages whenever traffic deviates more than 2 standard deviations"
        ],
        "answer": 1,
        "explanation": "The dual-window burn-rate model from Google SRE balances responsiveness (catch fast incidents) with noise reduction (slow burns ticket instead of page). Single thresholds and CPU-based paging produce alert fatigue and don't reflect user impact. Anomaly detection on traffic flags benign business events.\n\n\ud83d\udd0d Targeted Search: 'SRE multi-window multi-burn-rate alerts', 'Cloud Monitoring SLO burn rate alert policy'."
    },

    # ============== Mountkirk Games (5) ==============
    {
        "id": "q041",
        "domain": "Designing & Planning",
        "diff": "challenging",
        "text": "Mountkirk Games Case Study: A new battle-royale title needs a global matchmaker that places 100 players into a session with <100ms RTT for at least 80% of participants. Players authenticate via Google, Apple, or Facebook. Requirements: matchmaker must scale 0\u219220k matches/sec during launch surges, latency must be measured from real client telemetry, and no central region should bottleneck. Which architecture meets ALL constraints?",
        "opts": [
            "Single global Spanner instance for player state; matchmaking logic in Cloud Run in us-central1; client RTT estimates inferred from IP geolocation",
            "Regional Firestore in 4 regions for player state; matchmaking on GKE Autopilot in each region with Anthos Service Mesh global load balancing; client telemetry via Pub/Sub with regional subscribers; cross-region matches resolved via a global session-broker on Spanner",
            "Memorystore Redis in 1 region with cross-region clients; matchmaking on Cloud Functions; client RTT from a beacon hosted in us-central1",
            "Bigtable in a single region with replicated app profile; matchmaking on Compute Engine MIGs; static region selection by client IP"
        ],
        "answer": 1,
        "explanation": "Putting matchmaking in regions where players actually are is essential for the <100ms target. Real client telemetry beats IP-based geolocation guesses. Anthos Service Mesh handles regional service discovery and traffic policies. The global session-broker on Spanner serializes the small number of cross-region match decisions. The other choices either centralize compute (single bottleneck), use IP geolocation (inaccurate), or pick stores that aren't built for this access pattern.\n\n\ud83d\udd0d Targeted Search: 'Mountkirk Games matchmaker latency-based', 'Anthos Service Mesh global routing'."
    },
    {
        "id": "q042",
        "domain": "Analyzing & Optimizing",
        "diff": "challenging",
        "text": "Mountkirk Games Case Study: The analytics team ingests 8M events/sec of game telemetry. They need: at-least-once durability, dedupe at the warehouse, sub-minute freshness for ops dashboards, and replayability of the last 7 days for ML training. Which pipeline design is correct?",
        "opts": [
            "Pub/Sub (7-day retention) \u2192 Dataflow streaming with exactly-once delivery and idempotent BigQuery Storage Write API inserts using insert IDs; Pub/Sub Snapshots to replay for ML",
            "Pub/Sub Lite (regional, 7-day retention) \u2192 Dataflow batch every 1 minute \u2192 BigQuery legacy streaming inserts; replay by re-running batch jobs",
            "Direct streaming inserts to BigQuery from game servers; nightly dedupe with MERGE; 7-day BigQuery time-travel for replay",
            "Pub/Sub (default retention) \u2192 Cloud Functions \u2192 BigQuery streaming inserts; replay by exporting Cloud Logging"
        ],
        "answer": 0,
        "explanation": "Dataflow exactly-once + Storage Write API with insertId gives strong dedupe semantics. Pub/Sub 7-day retention with Snapshots cleanly handles replay for ML. BigQuery legacy streaming has higher cost and weaker semantics; batch every minute won't be sub-minute fresh end-to-end at 8M ev/s. Direct game-server inserts skip durability and dedupe primitives. Cloud Functions can't handle 8M ev/s sustained.\n\n\ud83d\udd0d Targeted Search: 'BigQuery Storage Write API exactly-once', 'Pub/Sub Snapshots replay'."
    },
    {
        "id": "q043",
        "domain": "Security & Compliance",
        "diff": "challenging",
        "text": "Mountkirk Games Case Study: An anti-cheat service must verify client signatures on every player action with <5ms p99 latency, store raw evidence for 90 days for appeals, and prevent insider tampering. Requirements: write-once storage of evidence, signed audit log for all admin reads, and key custody outside Google. Which combination is correct?",
        "opts": [
            "Cloud Storage Nearline with Object Lifecycle to delete at 90 days; Cloud Audit Logs (Admin Read) enabled; CMEK keys",
            "Cloud Storage with Bucket Lock and a 90-day retention policy; Object Versioning enabled; Cloud Audit Logs (Admin Read + Data Read) routed to a separate logs project; Cloud KMS keys backed by Cloud HSM",
            "Cloud Storage with Bucket Lock and a 90-day retention policy; Cloud Audit Logs (Admin Read + Data Read) routed to a separate logs project with Bucket Lock on the log sink; Cloud External Key Manager (EKM) with keys held in a third-party HSM",
            "BigQuery with row-level security; CMEK; Audit Logs to BigQuery; nightly snapshot to Coldline"
        ],
        "answer": 2,
        "explanation": "Bucket Lock + retention enforces write-once for evidence. EKM places key custody outside Google's control plane (the only choice that strictly satisfies 'outside Google'). Cloud HSM keys are still inside Google. Routing audit logs to a separate project with its own Bucket Lock prevents insider log tampering. BigQuery RLS doesn't satisfy WORM evidence requirements.\n\n\ud83d\udd0d Targeted Search: 'Cloud Storage Bucket Lock WORM', 'Cloud External Key Manager EKM custody', 'Cloud Audit Logs separate project sink'."
    },
    {
        "id": "q044",
        "domain": "Managing Implementation",
        "diff": "challenging",
        "text": "Mountkirk Games Case Study: The release pipeline ships a new game-server build every 2 hours during pre-launch. Requirements: zero downtime for active matches, ability to drain in-progress matches over up to 30 minutes, automatic rollback on a regression in error budget, and per-region staggered rollout. Which deployment strategy is best?",
        "opts": [
            "GKE rolling update with maxUnavailable=0 and a preStop hook that drains for 30s; rollback via kubectl rollout undo",
            "Cloud Deploy multi-target progression: canary at 10%/50%/100% per region with a 30-minute soak between phases; preStop hook with terminationGracePeriodSeconds=1800 to drain matches; automated rollback driven by an SLO error-budget check in a Cloud Deploy verification step",
            "Argo Rollouts blue/green per cluster with manual promotion and a 5-minute graceperiod",
            "Cloud Build trigger that runs `gcloud run deploy` per region in parallel with a traffic-shifting flag"
        ],
        "answer": 1,
        "explanation": "Cloud Deploy supports multi-region progressions with verification steps and automated rollback. terminationGracePeriodSeconds=1800 (30 min) is what actually allows long match drains. SLO-based verification catches regressions on real user impact. Rolling update with 30s drain doesn't honor the 30-minute drain. Argo Rollouts blue/green works but lacks the integrated rollback-on-SLO and per-region progression here. Cloud Run isn't the right runtime for stateful match servers.\n\n\ud83d\udd0d Targeted Search: 'Cloud Deploy verification rollback SLO', 'GKE terminationGracePeriodSeconds long drain'."
    },
    {
        "id": "q045",
        "domain": "Reliability & Operations",
        "diff": "challenging",
        "text": "Mountkirk Games Case Study: A regional game-state Redis cluster (Memorystore Redis Cluster) is hot during peak. The team observes p99 read latency spikes correlated with replication lag warnings. Requirements: keep current API surface (RESP), maintain HA, and reduce p99 spikes without re-architecting clients. Which change is BEST?",
        "opts": [
            "Switch to Memorystore for Redis Cluster (clustered) with sharded data, increased shard count, and read-from-replica enabled with consistent-hashing routing on the client",
            "Move to Memorystore for Memcached for higher throughput and use a CDN for hot keys",
            "Migrate to AlloyDB for PostgreSQL with Redis-compatible extension and use read pools",
            "Front Memorystore with Cloud CDN for read caching"
        ],
        "answer": 0,
        "explanation": "Memorystore for Redis Cluster scales horizontally via sharding, reduces per-node hot-key pressure, and supports read-from-replica with client-side routing — preserving the RESP protocol. Memcached drops Redis features (sorted sets, transactions). AlloyDB's Redis-like extension changes semantics. Cloud CDN doesn't front Memorystore.\n\n\ud83d\udd0d Targeted Search: 'Memorystore for Redis Cluster sharding read replica', 'Memorystore Redis hot key'."
    },

    # ============== TerramEarth (5) ==============
    {
        "id": "q046",
        "domain": "Designing & Planning",
        "diff": "challenging",
        "text": "TerramEarth Case Study: 2 million heavy-equipment units stream 1M telemetry events/sec to GCP. Requirements: regional ingestion to comply with data-residency in EU/US/APAC, exactly-once delivery to a downstream ML pipeline, and cost optimization for high-throughput-but-lower-priority telemetry like engine vibration spectra. Which ingestion design is BEST?",
        "opts": [
            "All devices publish to a single global Pub/Sub topic with regional subscribers; Dataflow exactly-once consumers",
            "Devices publish to regional Pub/Sub Lite topics for high-volume vibration data and regional Pub/Sub topics for control-plane events; Dataflow streaming consumers with exactly-once enabled; cross-region replication only for aggregated derived data",
            "Devices push to regional HTTPS load balancers fronting Cloud Functions which write to BigQuery streaming inserts in each region",
            "Devices use MQTT to Cloud IoT Core (deprecated) and IoT Core forwards to Pub/Sub"
        ],
        "answer": 1,
        "explanation": "Pub/Sub Lite is dramatically cheaper at high throughput when you're willing to pre-provision capacity per region — perfect for vibration spectra. Pub/Sub for control-plane events keeps the higher-tier features for low-volume but critical messages. Regional topics enforce residency. Single global topic violates residency. Cloud Functions can't sustain 1M ev/s. Cloud IoT Core was retired.\n\n\ud83d\udd0d Targeted Search: 'Pub/Sub Lite vs Pub/Sub cost throughput', 'data residency Pub/Sub regional'."
    },
    {
        "id": "q047",
        "domain": "Managing & Provisioning",
        "diff": "challenging",
        "text": "TerramEarth Case Study: The dealer-portal application runs on GKE in 4 regions. Each region has its own GKE cluster managed by separate teams. Leadership wants a single source of truth for cluster configuration (RBAC, network policies, namespaces, etc.) with audit-able rollouts. Which approach is correct?",
        "opts": [
            "Distribute YAMLs via a shared git repo and have each team `kubectl apply` on their cluster",
            "Deploy Anthos Config Management (Config Sync) with a single root-sync repo and Policy Controller for guardrails, and register all clusters into a fleet for centralized observability",
            "Use Helm charts hosted in Artifact Registry; each team installs via CI",
            "Use Cloud Deploy to deploy config-only releases to each cluster"
        ],
        "answer": 1,
        "explanation": "Anthos Config Management (Config Sync) with a fleet provides GitOps-driven, auditable configuration sync across all clusters with Policy Controller for guardrails. Helm and shared YAMLs via kubectl don't enforce drift correction. Cloud Deploy is for application releases, not cluster config sync.\n\n\ud83d\udd0d Targeted Search: 'Anthos Config Management Config Sync', 'GKE fleet Policy Controller'."
    },
    {
        "id": "q048",
        "domain": "Analyzing & Optimizing",
        "diff": "challenging",
        "text": "TerramEarth Case Study: A predictive-maintenance ML model is retrained weekly from 6 months of telemetry (~120 TB) joined with maintenance records and parts-inventory data. Training currently uses Vertex AI custom training on 8\u00d7A100 GPUs and takes 22 hours, missing the 12-hour weekend window. Which optimization yields the BIGGEST training-time reduction at minimal cost increase?",
        "opts": [
            "Move from custom training on A100s to TPU v5e Pods with the same dataset; rewrite the model in JAX",
            "Use BigQuery ML for the training and skip Vertex AI entirely",
            "Pre-process and join in BigQuery, materialize a partitioned + clustered training dataset, export to TFRecord on Cloud Storage with parallel reads enabled, use Vertex AI Reduction Server for gradient aggregation, and enable BFloat16 mixed precision",
            "Add more A100 GPUs to a single VM and increase batch size"
        ],
        "answer": 2,
        "explanation": "The dominant cost is data movement and gradient communication, not raw FLOPs. Push the join to BigQuery, write TFRecords once, read in parallel — eliminates I/O bottleneck. Reduction Server reduces all-reduce overhead in distributed training. Mixed precision (BFloat16) cuts compute roughly in half on supported hardware. TPU rewrite is high-effort. BigQuery ML doesn't fit this use case at scale. Single-VM scale-up hits PCIe and memory limits.\n\n\ud83d\udd0d Targeted Search: 'Vertex AI Reduction Server', 'TFRecord Cloud Storage parallel reads', 'BigQuery clustered dataset ML training'."
    },
    {
        "id": "q049",
        "domain": "Security & Compliance",
        "diff": "challenging",
        "text": "TerramEarth Case Study: Field technicians use a mobile app authenticated via the corporate Workspace tenant. Some technicians are contractors managed by a third-party IdP (Okta). Requirements: contractors must NOT be provisioned in Cloud Identity, must access only specific dealer-portal Cloud Run services, and access tokens must rotate every 1 hour. Which configuration is correct?",
        "opts": [
            "Federate Okta as a SAML SSO provider in Cloud Identity, create accounts for contractors, and rely on Workspace session controls",
            "Use Workforce Identity Federation with an OIDC provider mapping for Okta; create a Workforce Pool with attribute conditions; bind Cloud Run IAM roles to workforce-pool subjects; access tokens are 1-hour by default",
            "Use Workload Identity Federation with the contractors' Okta account as the workload provider; map to a service account that has Cloud Run invoker",
            "Issue long-lived service-account keys to each contractor and rotate manually"
        ],
        "answer": 1,
        "explanation": "Workforce Identity Federation is the explicit feature for human users from external IdPs without Cloud Identity provisioning. It supports SAML/OIDC, attribute mapping for fine-grained authz, and 1-hour federated tokens. Workload Identity Federation is for non-human workloads, not human users. Federating Okta into Cloud Identity does provision users (violates requirement). Long-lived SA keys violate everything.\n\n\ud83d\udd0d Targeted Search: 'Workforce Identity Federation Okta', 'Workforce Pool attribute conditions Cloud Run'."
    },
    {
        "id": "q050",
        "domain": "Reliability & Operations",
        "diff": "challenging",
        "text": "TerramEarth Case Study: The dealer portal calls 12 internal microservices. A recent incident showed a slow downstream service caused thread-pool exhaustion in upstream services, leading to a portal-wide brownout. Requirements: prevent cascading failures, retain visibility into per-call latency and errors, and enforce policy without code changes in each service. Which approach is BEST?",
        "opts": [
            "Adopt Anthos Service Mesh (Istio) on GKE with mTLS, request-level timeouts, retries with budget caps, circuit breakers via DestinationRule outlierDetection, and Cloud Service Mesh dashboards for golden-signal observability",
            "Add Hystrix-style libraries to each service and wire each team to implement timeouts independently",
            "Front each service with an external HTTP(S) Load Balancer with health checks and rely on health-check failure to circuit-break",
            "Move all services to Cloud Run and rely on Cloud Run concurrency limits"
        ],
        "answer": 0,
        "explanation": "Service Mesh (Anthos Service Mesh / Istio) implements timeouts, retries with budgets, and circuit breakers (outlierDetection) at the sidecar — no application code changes. mTLS is bonus, and golden signals come for free. Per-team libraries fragment the policy. External LBs don't do per-request circuit breaking. Cloud Run concurrency caps don't address downstream cascade.\n\n\ud83d\udd0d Targeted Search: 'Istio outlierDetection circuit breaker', 'Anthos Service Mesh retry budget', 'Cloud Service Mesh observability'."
    },
]

def main():
    if not os.path.exists(DB):
        print(f'ERROR: {DB} not found', file=sys.stderr)
        sys.exit(1)

    with open(DB, 'r', encoding='utf-8') as f:
        db = json.load(f)

    qs = db.setdefault('pca:seed-questions', [])
    existing_ids = {q.get('id') for q in qs}

    appended = 0
    for nq in NEW_QUESTIONS:
        if nq['id'] in existing_ids:
            print(f"Skipping existing id {nq['id']}")
            continue
        qs.append(nq)
        appended += 1

    # Match existing file style: ascii-escaped (emoji as \uXXXX) to avoid
    # surrogate-pair encoding issues if existing strings used those forms.
    with open(DB, 'w', encoding='utf-8') as f:
        json.dump(db, f, indent=2, ensure_ascii=True)

    print(f'Appended {appended} questions. Total now: {len(qs)}')
    # diff distribution
    from collections import Counter
    print('Diff distribution:', dict(Counter(q['diff'] for q in qs)))
    print('Domain distribution:', dict(Counter(q['domain'] for q in qs)))

if __name__ == '__main__':
    main()
