#!/usr/bin/env python3
"""Append q071-q100: 30 brand-new HARD + CHALLENGING PCA scenarios.
15 hard + 15 challenging, distinct from q001-q070.
"""
import json, os, sys
from collections import Counter

DB = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'database.json'))

NEW = [
    # ── 1
    {
        "id": "q071",
        "domain": "Designing & Planning",
        "diff": "challenging",
        "text": "A Cloud Run service must reach a private Cloud SQL instance on a Shared VPC, has 3000 concurrent instances during spikes, and is throughput-sensitive (500 MB/s aggregate egress). The team is currently using a Serverless VPC Connector but seeing throughput caps and long cold-start tail latency. Which migration is BEST?",
        "opts": [
            "Add a second Serverless VPC Connector and load-balance across both",
            "Switch the service to Cloud Run **Direct VPC egress** with the network/subnetwork attached to the service; remove the Serverless VPC Connector",
            "Move the workload to Cloud Functions Gen 2 with an HTTPS connector",
            "Place the Cloud SQL instance behind a public IP and use Cloud Armor"
        ],
        "answer": 1,
        "explanation": "Cloud Run Direct VPC egress attaches the service directly to a VPC subnet — no connector hop, much higher throughput, and eliminates the connector cold-start tax. Adding more connectors hits the same per-connector throughput caps and increases cost. Cloud Functions Gen 2 isn't faster than Direct VPC egress on Cloud Run (they share the runtime). Public IPs are the wrong direction for compliance.\n\n\ud83d\udd0d Targeted Search: 'Cloud Run Direct VPC egress', 'Serverless VPC Access connector throughput'."
    },
    # ── 2
    {
        "id": "q072",
        "domain": "Managing & Provisioning",
        "diff": "hard",
        "text": "A GKE workload pulls a 6 GB container image and is scaled rapidly during traffic spikes. Cold-start latency on new nodes is dominated by image pull time. Requirements: cut cold-start time without changing the image, and keep using Artifact Registry. Which feature is correct?",
        "opts": [
            "Switch to a regional persistent disk and pre-pull the image to the disk",
            "Enable **GKE Image Streaming** with a streaming-eligible Artifact Registry image; pods start as soon as the data they need is streamed in",
            "Use Container-Optimized OS preloaded with the image baked in",
            "Increase node-pool size and pin pods with affinity rules"
        ],
        "answer": 1,
        "explanation": "GKE Image Streaming lets containers start running while their image data is streamed lazily from Artifact Registry — measurable cold-start reductions on multi-GB images, no image rebuild required. Regional PD pre-pull doesn't integrate with the kubelet image cache. Baking images into the node image is brittle and expensive. Larger node pools mask the symptom and waste capacity.\n\n\ud83d\udd0d Targeted Search: 'GKE Image Streaming Artifact Registry', 'GKE container streaming cold start'."
    },
    # ── 3
    {
        "id": "q073",
        "domain": "Security & Compliance",
        "diff": "challenging",
        "text": "A regulated genomics workload runs on GKE and processes raw human-genome data. InfoSec requires hardware-level memory encryption for the workload nodes (so even root-on-host operators cannot snoop RAM), without rewriting the application or moving to a different runtime. Which configuration is correct?",
        "opts": [
            "Confidential VMs at the project level for all VMs",
            "GKE node pool created with **Confidential GKE Nodes** (N2D AMD SEV / C3 Intel TDX) and the workload constrained to those node pools via taints/tolerations and node selectors",
            "Shielded VMs with Secure Boot enabled on the GKE node pool",
            "GKE Sandbox (gVisor) on a default node pool"
        ],
        "answer": 1,
        "explanation": "Confidential GKE Nodes give per-node hardware memory encryption for K8s pods running on those nodes. Selector/taint pinning ensures only the genomics workload runs there. Project-wide Confidential VMs is a blunt instrument and doesn't apply to GKE node pools without configuration. Shielded VMs verify boot integrity but don't encrypt RAM. gVisor is a syscall-level sandbox, not memory encryption.\n\n\ud83d\udd0d Targeted Search: 'Confidential GKE Nodes', 'GKE Confidential Nodes node pool taint'."
    },
    # ── 4
    {
        "id": "q074",
        "domain": "Designing & Planning",
        "diff": "challenging",
        "text": "A company stores customer profiles in Cloud Spanner. They need to push every row mutation downstream to Pub/Sub for fan-out to fraud detection, search indexing, and email triggers, with at-least-once delivery and ordering preserved per primary key. Which design is correct?",
        "opts": [
            "Application-level dual-write to Spanner and Pub/Sub inside the same RPC handler",
            "**Spanner Change Streams** consumed by a Dataflow job (using the SpannerIO change-streams connector) that writes to Pub/Sub with ordering keys = primary key; downstream subscribers fan out by attribute filter",
            "Hourly batch SELECT * WHERE updated_at > ... and publish results to Pub/Sub",
            "Use Database Migration Service to replicate Spanner changes into a Pub/Sub topic"
        ],
        "answer": 1,
        "explanation": "Spanner Change Streams emit row-level mutations with strong ordering and durability. The supported pattern is to consume them with Dataflow's SpannerIO change-streams connector and republish to Pub/Sub with ordering keys for per-key ordering. Dual-write loses transactional consistency. Hourly batch can't preserve per-row ordering and misses deletes. DMS does not stream Spanner changes to Pub/Sub.\n\n\ud83d\udd0d Targeted Search: 'Spanner change streams Dataflow', 'Pub/Sub ordering keys'."
    },
    # ── 5
    {
        "id": "q075",
        "domain": "Designing & Planning",
        "diff": "hard",
        "text": "An e-commerce app stores 200M product records in Cloud Spanner and now needs semantic similarity search ('show items similar to this product') based on text + image embeddings. Requirements: keep the same Spanner OLTP datastore, low query-add latency, and avoid maintaining a separate vector database. Which approach is correct?",
        "opts": [
            "Stream rows to Vertex AI Vector Search and query that index from the application",
            "Use **Spanner vector search** — store embeddings as ARRAY<FLOAT32> columns and use the built-in approximate vector index (e.g., ScaNN-style) with `APPROX_COSINE_DISTANCE` queries",
            "Store embeddings in BigQuery and join with Spanner via federated queries",
            "Index embeddings in Memorystore for Redis with the RediSearch module"
        ],
        "answer": 1,
        "explanation": "Spanner now supports native vector indexing with approximate-nearest-neighbor distance functions, letting you keep transactional product data and similarity search co-located on the same store. Vertex AI Vector Search is a great choice when you need a separate index, but here the requirement is to *avoid* a separate vector DB. BigQuery is OLAP. Memorystore RediSearch isn't on managed Memorystore.\n\n\ud83d\udd0d Targeted Search: 'Cloud Spanner vector search', 'Spanner APPROX_COSINE_DISTANCE'."
    },
    # ── 6
    {
        "id": "q076",
        "domain": "Analyzing & Optimizing",
        "diff": "hard",
        "text": "A data team has a 4 PB lake stored as Apache **Iceberg** tables on Cloud Storage. They want unified governance, fine-grained access control, and the ability to query the same tables from BigQuery, Spark on Dataproc, and Trino — without copying data or maintaining duplicate metadata. Which solution is correct?",
        "opts": [
            "Create BigQuery external tables for each file and rebuild metadata nightly",
            "Use **BigLake** Iceberg tables with the BigLake metastore — a single managed metadata layer that BigQuery, Dataproc/Spark, and other open-source engines all read; fine-grained IAM via BigLake row/column policies",
            "Migrate the data to Hive on a Compute Engine cluster",
            "Manually maintain a Hive metastore on Cloud SQL and point each engine at it"
        ],
        "answer": 1,
        "explanation": "BigLake (with the BigLake metastore) is purpose-built for this: open-format tables (Iceberg/Hudi/Delta) on Cloud Storage with one metadata layer accessible from BigQuery and OSS engines, plus IAM-driven row/column-level controls. Custom external tables and self-hosted Hive metastores reproduce features you'd inherit for free. Migrating off the lake violates the no-copy requirement.\n\n\ud83d\udd0d Targeted Search: 'BigLake Iceberg metastore', 'BigLake fine-grained access control'."
    },
    # ── 7
    {
        "id": "q077",
        "domain": "Analyzing & Optimizing",
        "diff": "challenging",
        "text": "A platform team manages 12 GCS buckets and 8 BigQuery datasets across many domain teams. Requirements: discover assets automatically, classify zones (raw / curated / consumed), enforce data quality rules at ingest, and surface lineage across BigQuery and GCS in one place. Which managed service is correct?",
        "opts": [
            "Cloud Data Catalog with manual tag templates and a custom lineage tracker",
            "**Dataplex** — define a lake with raw/curated/consumed zones; Dataplex auto-discovers entities in GCS and BigQuery, runs data quality tasks, and emits lineage to a unified UI",
            "Cloud Composer DAGs that crawl GCS+BQ nightly and write metadata to BigQuery",
            "Cloud Asset Inventory with custom Looker Studio dashboards"
        ],
        "answer": 1,
        "explanation": "Dataplex unifies asset discovery, zone-based governance, data-quality tasks, and cross-engine lineage out of the box. Data Catalog (now part of Dataplex) only stores metadata. Custom DAGs and Asset Inventory dashboards reinvent these features without the integrated UX.\n\n\ud83d\udd0d Targeted Search: 'Dataplex zones discovery', 'Dataplex data quality tasks lineage'."
    },
    # ── 8
    {
        "id": "q078",
        "domain": "Managing Implementation",
        "diff": "hard",
        "text": "A SQL-only analytics team wants version-controlled, dependency-aware transformations on top of BigQuery, with unit tests, scheduled runs, and a managed development experience — without standing up dbt or Airflow. Which Google-managed service is BEST?",
        "opts": [
            "Cloud Composer DAG with BigQueryOperator chains",
            "**Dataform** — managed SQLX repositories (Git-backed), declarative dependencies via `ref()`, assertions for tests, scheduled releases, and integrated UI in BigQuery",
            "Cloud Build pipelines that run hand-written `bq query` calls",
            "Cloud Workflows with embedded SQL strings"
        ],
        "answer": 1,
        "explanation": "Dataform is Google's first-party managed SQL transformation framework: Git-backed SQLX, automatic dependency graph via `ref()`, assertions for tests, and scheduled releases — exactly what the team asked for, no extra infra. Composer/Workflows/Cloud Build can mimic pieces but lack the integrated SQLX dev loop.\n\n\ud83d\udd0d Targeted Search: 'Dataform SQLX BigQuery', 'Dataform assertions schedules'."
    },
    # ── 9
    {
        "id": "q079",
        "domain": "Analyzing & Optimizing",
        "diff": "challenging",
        "text": "A data engineering team runs hundreds of one-off Spark jobs per day for ad-hoc analytics. They want zero cluster management, autoscaling per job, integration with Dataplex for asset access, and the ability to keep the existing PySpark code unchanged. Which service is correct?",
        "opts": [
            "Dataproc on GKE with auto-scaling node pools",
            "**Dataproc Serverless for Spark** — submit batch jobs to a managed runtime that autoscales per workload, with no cluster lifecycle, and supports integration with Dataplex secure-data-exchange",
            "Compute Engine MIG with Spark installed and a custom autoscaler",
            "BigQuery for all analytics with the python-bigquery client"
        ],
        "answer": 1,
        "explanation": "Dataproc Serverless for Spark is the managed-no-cluster runtime that fits ad-hoc PySpark with per-job autoscaling. Dataproc on GKE still requires a cluster lifecycle and Kubernetes ops. Compute Engine self-managed Spark is the most ops. BigQuery is SQL-only and would require code rewrites.\n\n\ud83d\udd0d Targeted Search: 'Dataproc Serverless Spark batch', 'Dataproc Serverless Dataplex'."
    },
    # ── 10
    {
        "id": "q080",
        "domain": "Reliability & Operations",
        "diff": "hard",
        "text": "A team needs an asynchronous task system with: per-task target HTTP endpoint, configurable retry with exponential backoff per task, deadline up to 30 minutes per task, and the ability to schedule a specific delivery time per task (not a fixed cron). Which Google Cloud service is BEST?",
        "opts": [
            "Pub/Sub with push subscriptions and DLQs",
            "**Cloud Tasks** — queues that target HTTP/AppEngine handlers with per-task retry config, scheduling timestamps, deduplication, and 30-minute deadlines",
            "Cloud Workflows with sleep steps",
            "Cloud Scheduler with one job per task"
        ],
        "answer": 1,
        "explanation": "Cloud Tasks is for per-task scheduled delivery to HTTP endpoints with per-task retry policies — exactly the requirements. Pub/Sub is fan-out messaging without per-message scheduling. Workflows is orchestration. Cloud Scheduler is for fixed cron-like jobs, not millions of one-off tasks with per-task schedules.\n\n\ud83d\udd0d Targeted Search: 'Cloud Tasks per-task scheduling retry', 'Cloud Tasks vs Pub/Sub'."
    },
    # ── 11
    {
        "id": "q081",
        "domain": "Designing & Planning",
        "diff": "challenging",
        "text": "A trading platform publishes per-account event updates to Pub/Sub and consumes them with multiple Dataflow jobs. Requirements: per-account ordering must be preserved end-to-end, but events from different accounts can be processed in parallel. The team also needs to keep throughput high (millions of events/sec). Which approach is correct?",
        "opts": [
            "Use a single Pub/Sub topic without ordering keys and rely on consumer-side timestamp sorting",
            "Use Pub/Sub topic with **ordering keys = account_id**; subscribers enable message ordering; Dataflow uses the ordered Pub/Sub IO connector",
            "Use one Pub/Sub topic per account",
            "Use Pub/Sub Lite with single-partition topics"
        ],
        "answer": 1,
        "explanation": "Pub/Sub message ordering keys provide per-key ordering while preserving fan-out parallelism across keys — the textbook way to keep per-account ordering at high throughput. Consumer-side sort is brittle and adds latency. One topic per account explodes resource counts at scale. Single-partition Pub/Sub Lite serializes all events, killing throughput.\n\n\ud83d\udd0d Targeted Search: 'Pub/Sub ordering keys', 'Pub/Sub message ordering Dataflow'."
    },
    # ── 12
    {
        "id": "q082",
        "domain": "Security & Compliance",
        "diff": "hard",
        "text": "A central security team wants every Cloud Storage bucket and BigQuery dataset created across 200 projects to use CMEK from a specific key ring, automatically and without each project team having to provision keys. Which feature is correct?",
        "opts": [
            "Mandate by Org Policy and have each team provision keys themselves",
            "**Cloud KMS Autokey** at the folder/org level — Google automatically provisions and assigns CMEK keys for newly created supported resources from the configured Autokey configuration",
            "Cloud Functions trigger that runs on resource creation and rotates keys",
            "Use default Google-managed encryption and document compensating controls"
        ],
        "answer": 1,
        "explanation": "Cloud KMS Autokey automates CMEK provisioning across an organization or folder — new supported resources get a generated CMEK key without per-team work. Org Policy can require CMEK but doesn't create the keys for teams. Custom triggers reinvent Autokey. Default encryption fails the CMEK requirement.\n\n\ud83d\udd0d Targeted Search: 'Cloud KMS Autokey', 'KMS Autokey CMEK organization'."
    },
    # ── 13
    {
        "id": "q083",
        "domain": "Security & Compliance",
        "diff": "challenging",
        "text": "Two banks want to jointly compute fraud-detection ML on combined customer data, but each bank's raw data must remain encrypted from the OTHER bank's view AND from Google operators. Requirements: hardware-attested confidential compute, joint workload runs only after both parties sign attestation policies, and outputs are returned only when policies pass. Which feature is correct?",
        "opts": [
            "Confidential VMs in a shared project with dual-control IAM",
            "**Confidential Space** — runs workloads in a Confidential VM TEE, attests the workload image to each data owner, and only releases keys to decrypt each party's data inside the TEE if the attestation policies match",
            "GKE Confidential Nodes with mTLS between pods",
            "Vertex AI custom training with CMEK and VPC SC"
        ],
        "answer": 1,
        "explanation": "Confidential Space is built for multi-party data clean rooms: each party encrypts their inputs and grants release of decryption keys only after the workload's attested image and policy match. The TEE prevents the other party and Google operators from seeing raw inputs. The other options provide pieces (hardware encryption, networking) but not the multi-party trust ceremony with workload attestation.\n\n\ud83d\udd0d Targeted Search: 'Confidential Space attestation', 'Confidential Space data clean room'."
    },
    # ── 14
    {
        "id": "q084",
        "domain": "Security & Compliance",
        "diff": "challenging",
        "text": "A research team de-identifies a 50M-row patient dataset for analytics. Compliance requires evidence that re-identification risk is below a threshold (k=10 for any combination of quasi-identifiers like ZIP, age band, gender). Which capability quantifies this risk and lets you tune until the threshold is met?",
        "opts": [
            "Cloud DLP de-identification templates with redact transforms",
            "**Sensitive Data Protection (SDP) risk analysis** — k-anonymity, l-diversity, k-map, or delta-presence analyses run over the de-identified dataset to quantify residual re-identification risk",
            "BigQuery row-level security policies",
            "VPC Service Controls perimeter scoped to the dataset"
        ],
        "answer": 1,
        "explanation": "SDP (the renamed Cloud DLP) provides risk-analysis jobs that compute k-anonymity, l-diversity, k-map, and delta-presence on tabular data — the only Google-native way to quantify residual re-identification risk and tune transforms accordingly. The other options control access but don't measure re-identification risk.\n\n\ud83d\udd0d Targeted Search: 'Sensitive Data Protection risk analysis k-anonymity', 'Cloud DLP l-diversity'."
    },
    # ── 15
    {
        "id": "q085",
        "domain": "Security & Compliance",
        "diff": "hard",
        "text": "Security wants to enforce 'no SSH from the internet' and 'deny RDP everywhere' across every existing and future VPC in the organization, including projects that may be created tomorrow, with minimal team-by-team intervention. Which mechanism is correct?",
        "opts": [
            "Manually create firewall rules in every VPC and audit nightly",
            "**Hierarchical Firewall Policies** at the org/folder level with explicit deny rules; each new VPC inherits them automatically",
            "Cloud Armor edge security policy attached to a global LB",
            "VPC Service Controls perimeter blocking SSH/RDP"
        ],
        "answer": 1,
        "explanation": "Hierarchical Firewall Policies attach at the org or folder level and apply to all VPCs underneath, including future projects — exactly the 'enforce centrally, no per-team work' requirement. Per-VPC rules don't scale and drift. Cloud Armor is for HTTP(S) edge, not SSH/RDP at VPC edge. VPC SC governs API egress, not L4 traffic to compute.\n\n\ud83d\udd0d Targeted Search: 'Hierarchical Firewall Policy organization', 'GCP firewall policy folder'."
    },
    # ── 16
    {
        "id": "q086",
        "domain": "Designing & Planning",
        "diff": "challenging",
        "text": "An enterprise needs to consume Cloud SQL, BigQuery, and a partner's published service privately — without exposing any of these services through public IPs or VPC peering, and the consumer projects must continue to use private RFC1918 addresses scoped to their own VPC. Which feature is BEST?",
        "opts": [
            "VPC Network Peering with the producer projects",
            "**Private Service Connect (PSC) endpoints** — create a PSC endpoint in the consumer VPC pointing at the published service; consumers reach the service via a private IP in their own subnet",
            "Cloud Interconnect attachments to each producer project",
            "Cloud NAT with allowlisted destinations"
        ],
        "answer": 1,
        "explanation": "Private Service Connect endpoints expose published services (Google APIs, partner services, internal services) as a private IP inside the consumer's VPC — no peering, no public IPs, RFC1918 only. VPC Peering exposes the entire producer VPC. Interconnect is for hybrid connectivity. NAT only addresses outbound public traffic.\n\n\ud83d\udd0d Targeted Search: 'Private Service Connect endpoint published service', 'PSC vs VPC peering'."
    },
    # ── 17
    {
        "id": "q087",
        "domain": "Reliability & Operations",
        "diff": "hard",
        "text": "A workload behind Cloud NAT generates 8 million outbound HTTPS calls/hour to a small set of external destinations. Engineers see intermittent connection failures. Logs show NAT 'Allocation failed' for source ports. Which fix is correct?",
        "opts": [
            "Add more Cloud NAT gateways in the same region",
            "Configure **manual port allocation** on Cloud NAT with a higher minimum-ports-per-VM, or add more NAT IPs (or enable dynamic port allocation) to expand the available 5-tuple space",
            "Switch the workload to use a Serverless VPC Connector",
            "Disable Cloud NAT and assign external IPs to each VM"
        ],
        "answer": 1,
        "explanation": "Cloud NAT 'Allocation failed' is port exhaustion — too few source ports per VM for the destination tuple. Increasing minimum-ports-per-VM, adding NAT IPs, or enabling dynamic port allocation expands the 5-tuple space. Adding NAT gateways in the same region doesn't help; one NAT gateway per region. Connectors and external IPs are unrelated.\n\n\ud83d\udd0d Targeted Search: 'Cloud NAT port allocation failed', 'Cloud NAT dynamic port allocation'."
    },
    # ── 18
    {
        "id": "q088",
        "domain": "Reliability & Operations",
        "diff": "challenging",
        "text": "A consumer-facing web app behind a global external Application Load Balancer is being targeted by a sophisticated, slowly-ramping L7 DDoS that mimics legitimate traffic. Static rate-limit rules in Cloud Armor are insufficient. Which capability is BEST?",
        "opts": [
            "Increase backend autoscaling minimum capacity",
            "Enable **Cloud Armor Adaptive Protection** with Managed Protection Plus — ML-driven anomaly detection that proposes WAF rules tailored to the attack signature in near real time",
            "Move to a regional internal LB and require VPN for clients",
            "Switch to a TCP load balancer to drop HTTP-layer attacks"
        ],
        "answer": 1,
        "explanation": "Adaptive Protection uses ML to learn baseline traffic and propose targeted Cloud Armor rules during anomalous events — the right tool for slow, mimicking L7 attacks. Autoscaling pays for the attacker. Restricting to VPN breaks the consumer model. TCP LB removes the very inspection capability you need.\n\n\ud83d\udd0d Targeted Search: 'Cloud Armor Adaptive Protection', 'Managed Protection Plus L7 DDoS'."
    },
    # ── 19
    {
        "id": "q089",
        "domain": "Reliability & Operations",
        "diff": "hard",
        "text": "Operators want to run ad-hoc SQL across application logs spanning 30 days for incident investigation, without exporting to BigQuery, and need to share saved queries with the team. Which feature is correct?",
        "opts": [
            "Cloud Logging classic with Logs Explorer queries only",
            "Route logs to a **Log Bucket with Log Analytics enabled** and run SQL via the Log Analytics page (or the linked BigQuery dataset for cross-joins); 30-day retention configured on the bucket",
            "Daily export to BigQuery via sink and query manually",
            "Stream logs to Pub/Sub and into a Dataflow pipeline that writes Parquet"
        ],
        "answer": 1,
        "explanation": "Log Analytics on Log Buckets gives in-place SQL over logs, BigQuery-style query semantics, and links to a BigQuery dataset for cross-joining with other tables — no export needed. The other options either lack SQL or require continuous custom export pipelines.\n\n\ud83d\udd0d Targeted Search: 'Cloud Logging Log Analytics SQL', 'Log Bucket Log Analytics'."
    },
    # ── 20
    {
        "id": "q090",
        "domain": "Reliability & Operations",
        "diff": "challenging",
        "text": "A microservices platform produces 100k requests/sec. The SRE team wants distributed traces with low overhead, the ability to keep 100% of error/slow traces and a small percentage of normal traffic, and OpenTelemetry-compatible instrumentation. Which approach is correct?",
        "opts": [
            "Sample 100% of traces in Cloud Trace and accept the cost",
            "Use OpenTelemetry SDK with the OpenTelemetry Collector and **tail-based sampling** (keep all error/slow traces; sample normal traces at, e.g., 1%); export to Cloud Trace",
            "Sample at the application code with random 1% head sampling",
            "Disable tracing in production"
        ],
        "answer": 1,
        "explanation": "Tail-based sampling decides at end-of-trace based on the full span tree — letting you keep ALL error/slow traces while subsampling normal traffic. Head sampling decides up front and loses error visibility. 100% sampling is cost-prohibitive at this scale. Disabling tracing kills observability.\n\n\ud83d\udd0d Targeted Search: 'OpenTelemetry tail sampling', 'Cloud Trace OpenTelemetry Collector'."
    },
    # ── 21
    {
        "id": "q091",
        "domain": "Reliability & Operations",
        "diff": "hard",
        "text": "A regulated workload uses Cloud Spanner. Requirements: ability to recover the database to any point within the last 7 days (RPO ~minutes), exportable backups for retention beyond 7 days, and recovery from accidental DML without restoring the full instance. Which set of features is correct?",
        "opts": [
            "Daily exports to Cloud Storage and re-import on demand",
            "**Spanner Point-in-Time Recovery (PITR)** with version_retention_period up to 7 days for fast recovery; **Spanner backups** for >7-day retention; **stale reads** at a prior timestamp for granular row-level recovery without a full restore",
            "Cross-region read replicas with manual failover for backup",
            "Streaming logical replication into BigQuery"
        ],
        "answer": 1,
        "explanation": "Spanner PITR (up to 7 days), Spanner backups (long retention), and stale reads (`AS OF SYSTEM TIME`) collectively cover all three requirements. Daily GCS export misses minute-level RPO. Cross-region replicas don't address accidental DML. BQ replication isn't a recovery path.\n\n\ud83d\udd0d Targeted Search: 'Spanner PITR version_retention_period', 'Spanner stale reads AS OF SYSTEM TIME'."
    },
    # ── 22
    {
        "id": "q092",
        "domain": "Designing & Planning",
        "diff": "hard",
        "text": "A self-managed PostgreSQL on Compute Engine needs sustained 350k IOPS at <1ms p99 latency for a 4 TB database, with the option to detach and re-attach the disk to another VM during failover. Which storage option is correct?",
        "opts": [
            "SSD persistent disk (pd-ssd) at maximum size",
            "**Hyperdisk Extreme** — provisioned IOPS up to 350k+, low single-digit-ms latency, decoupled IOPS/throughput from capacity, attachable across VMs",
            "Local SSD with replication scripts",
            "Filestore Enterprise mounted via NFS"
        ],
        "answer": 1,
        "explanation": "Hyperdisk Extreme is designed for high-IOPS, latency-sensitive databases — provision IOPS independently of size, attach across VMs. pd-ssd caps far below 350k IOPS. Local SSD is ephemeral and not detachable. Filestore is for shared NFS, not single-instance DB IOPS.\n\n\ud83d\udd0d Targeted Search: 'Hyperdisk Extreme provisioned IOPS', 'Hyperdisk vs pd-ssd database'."
    },
    # ── 23
    {
        "id": "q093",
        "domain": "Designing & Planning",
        "diff": "hard",
        "text": "A multi-tier application needs a shared filesystem accessible by 200 GKE pods across 3 zones in a region, with 99.99% availability and consistent sub-ms NFS latency. Which option is correct?",
        "opts": [
            "Filestore Zonal (Basic) — single zone, lowest cost",
            "**Filestore Enterprise** — regional availability across zones, 99.99% SLA, low-latency NFSv3/v4.1",
            "GCS FUSE mount on each pod",
            "Local SSD with a custom NFS server"
        ],
        "answer": 1,
        "explanation": "Filestore Enterprise gives regional (multi-zone) availability with the 99.99% SLA and low-latency NFS — the only option satisfying both. Zonal Filestore fails on availability. GCS FUSE doesn't satisfy POSIX/latency for shared filesystem semantics. Self-hosted NFS on Local SSD is fragile and ephemeral.\n\n\ud83d\udd0d Targeted Search: 'Filestore Enterprise vs Zonal', 'Filestore tiers SLA'."
    },
    # ── 24
    {
        "id": "q094",
        "domain": "Designing & Planning",
        "diff": "challenging",
        "text": "A Retrieval-Augmented Generation (RAG) chatbot must search 200M document embeddings (768-dim) at <50ms p99, support filtering by tenant ID, and refresh the index daily. Which managed service is BEST?",
        "opts": [
            "Memorystore for Redis with the RediSearch module",
            "**Vertex AI Vector Search** — managed ANN index over high-dim embeddings, low-latency online queries with restricts/filters, and batch index updates",
            "BigQuery ML with VECTOR_SEARCH on a sampled subset",
            "Cloud SQL pgvector extension"
        ],
        "answer": 1,
        "explanation": "Vertex AI Vector Search (formerly Matching Engine) is the managed ANN system for high-dim embeddings at scale, with namespace-style restricts and managed batch updates — fitting the RAG pattern at 200M vectors. Memorystore RediSearch is not on managed Memorystore. BQ ML VECTOR_SEARCH is great but optimized for analytic, not <50ms online. pgvector on Cloud SQL won't scale to 200M with that latency target.\n\n\ud83d\udd0d Targeted Search: 'Vertex AI Vector Search ANN', 'Vertex AI Matching Engine RAG'."
    },
    # ── 25
    {
        "id": "q095",
        "domain": "Managing Implementation",
        "diff": "hard",
        "text": "An accounts-payable team receives 10k vendor invoices per day in mixed PDF / scanned-image formats. They want structured fields (vendor, total, line items, due date) extracted with >95% F1 on their specific invoice templates. Which Google Cloud service is correct?",
        "opts": [
            "Cloud Vision OCR + Python regex post-processing",
            "**Document AI Custom Extractor** — train a model on labeled samples of your invoice templates; deploy to a Document AI processor; SDK calls return structured fields",
            "Vertex AI AutoML Vision",
            "Send each invoice to a Cloud Run service running Tesseract"
        ],
        "answer": 1,
        "explanation": "Document AI Custom Extractor is purpose-built for invoice/form extraction with template-specific fine-tuning and structured output. Vision OCR returns raw text. AutoML Vision is image classification. Tesseract isn't trainable for structured extraction.\n\n\ud83d\udd0d Targeted Search: 'Document AI Custom Extractor invoice', 'Document AI processor types'."
    },
    # ── 26
    {
        "id": "q096",
        "domain": "Managing Implementation",
        "diff": "challenging",
        "text": "An organization has 80 legacy Linux VMs running a stateless monolith. Goal: replatform to GKE with minimal code changes, automated discovery of dependencies/libraries, image generation, and a Kubernetes manifest with proper liveness/readiness probes inferred. Which service is correct?",
        "opts": [
            "Manual containerization team-by-team with `docker build` Dockerfiles",
            "**Migrate to Containers (M2C)** — discover VMs, generate Dockerfiles + Kubernetes YAML, optionally include readiness/liveness probes inferred from process behavior",
            "Anthos Config Management — sync existing VM configs as ConfigMaps",
            "Cloud Build with custom transformers per VM"
        ],
        "answer": 1,
        "explanation": "Migrate to Containers (M2C) automates VM-to-container modernization including dependency discovery and YAML/Dockerfile generation. Manual Dockerfiles is slow at 80 VMs. ACM is for cluster config sync. Cloud Build doesn't analyze running VMs.\n\n\ud83d\udd0d Targeted Search: 'Migrate to Containers M2C VM modernization', 'Migrate for Anthos Dockerfile generation'."
    },
    # ── 27
    {
        "id": "q097",
        "domain": "Designing & Planning",
        "diff": "challenging",
        "text": "A consumer API runs on Cloud Run in us-central1 and europe-west1 and must be exposed under a single global hostname with intelligent geo-routing, automatic regional failover, custom TLS, Cloud CDN at the edge, and a Cloud Armor WAF. Which architecture is correct?",
        "opts": [
            "Two Cloud Run services with separate public URLs and Cloud DNS round-robin",
            "Two Cloud Run services exposed via **regional Serverless Network Endpoint Groups (NEGs)** added as backends to a single **global external Application Load Balancer**, with Cloud CDN, Cloud Armor, and a Google-managed certificate",
            "One Cloud Run service in us-central1 only and a Cloud DNS geolocation policy returning that single IP",
            "Cloud Functions Gen 2 fronted by Cloud Endpoints"
        ],
        "answer": 1,
        "explanation": "Serverless NEGs are how you expose Cloud Run services as backends to the global external ALB, getting CDN, Cloud Armor, custom TLS, and intelligent failover for free. DNS round-robin lacks LB-level health/failover. Single-region routing breaks the global use case. Cloud Functions+Endpoints is a different pattern that doesn't satisfy CDN+WAF cleanly.\n\n\ud83d\udd0d Targeted Search: 'Serverless NEG Cloud Run global LB', 'Cloud Run multi-region external HTTPS LB'."
    },
    # ── 28
    {
        "id": "q098",
        "domain": "Managing Implementation",
        "diff": "hard",
        "text": "A team running services on App Engine Flex must migrate before the platform's deprecation, with minimal code changes, the same Dockerfile-based runtime, autoscaling, and deployment via gcloud CLI. Which target is the most natural replacement?",
        "opts": [
            "App Engine Standard with the Python runtime",
            "**Cloud Run** — same container model, gcloud-driven deploys, scale-to-zero or min-instances autoscaling, and direct VPC egress for connectivity",
            "Compute Engine MIGs with custom images",
            "GKE Autopilot with a service mesh"
        ],
        "answer": 1,
        "explanation": "Cloud Run is the documented modernization path for App Engine Flex — same container model, gcloud-driven deployment, autoscaling. Standard environment requires runtime-specific limitations and isn't container-based. MIGs and GKE both increase ops overhead unnecessarily.\n\n\ud83d\udd0d Targeted Search: 'App Engine Flex deprecation Cloud Run', 'GAE Flex migration'."
    },
    # ── 29
    {
        "id": "q099",
        "domain": "Designing & Planning",
        "diff": "challenging",
        "text": "A microservices team needs API management for internal service-to-service calls only (mTLS, quotas, basic rate limits, OpenAPI-defined contracts) without the cost of a full enterprise API platform. Which approach is correct?",
        "opts": [
            "Apigee X organization for internal services",
            "**Cloud Endpoints + Extensible Service Proxy v2 (ESPv2)** — define APIs in OpenAPI/gRPC, deploy ESPv2 alongside services, enforce auth/quotas/rate limits at the proxy",
            "GKE Gateway API only, no API management",
            "Cloud Armor edge security policies"
        ],
        "answer": 1,
        "explanation": "Cloud Endpoints + ESPv2 is the lighter-weight path for internal API management — OpenAPI/gRPC contracts, auth, quotas, rate limits — without paying for the Apigee X feature set the team doesn't need. Gateway API is L7 routing without API management. Cloud Armor is edge WAF, not API contracts/quotas.\n\n\ud83d\udd0d Targeted Search: 'Cloud Endpoints ESPv2 OpenAPI', 'Cloud Endpoints vs Apigee X'."
    },
    # ── 30
    {
        "id": "q100",
        "domain": "Analyzing & Optimizing",
        "diff": "hard",
        "text": "A media company uploads 8-hour audio recordings for batch transcription. Requirements: speaker diarization, automatic punctuation, multi-language support, and an asynchronous pattern (no client connection held open). Which approach is BEST?",
        "opts": [
            "Speech-to-Text v1 streaming API in chunks",
            "**Speech-to-Text v2 BatchRecognize** — async long-form recognition; output written to Cloud Storage; supports diarization, punctuation, and multi-language models",
            "Vertex AI custom Whisper model on a GPU VM",
            "Cloud Functions Gen 2 with synchronous Speech-to-Text per chunk"
        ],
        "answer": 1,
        "explanation": "Speech-to-Text v2 BatchRecognize handles long-form async transcription with output to Cloud Storage and supports diarization/punctuation/multi-language. Streaming v1 is for real-time. Custom Whisper is high-effort. Synchronous chunked Functions hit timeouts on 8-hour audio.\n\n\ud83d\udd0d Targeted Search: 'Speech-to-Text v2 BatchRecognize', 'Speech-to-Text long-form audio'."
    },
]

def main():
    if not os.path.exists(DB):
        print('ERROR: database.json missing', file=sys.stderr); sys.exit(1)
    with open(DB, 'r', encoding='utf-8') as f:
        db = json.load(f)
    qs = db.setdefault('pca:seed-questions', [])
    existing_ids = {q.get('id') for q in qs}
    existing_prefixes = {q.get('text', '').strip()[:90] for q in qs}

    appended = 0
    for nq in NEW:
        if nq['id'] in existing_ids:
            print(f"SKIP duplicate id {nq['id']}"); continue
        prefix = nq['text'].strip()[:90]
        if prefix in existing_prefixes:
            print(f"SKIP duplicate scenario prefix for {nq['id']}"); continue
        qs.append(nq)
        appended += 1
        existing_ids.add(nq['id'])
        existing_prefixes.add(prefix)

    with open(DB, 'w', encoding='utf-8') as f:
        json.dump(db, f, indent=2, ensure_ascii=True)

    print(f'Appended {appended}. Total: {len(qs)}')
    print('Diffs:', dict(Counter(q['diff'] for q in qs)))
    print('Domains:', dict(Counter(q['domain'] for q in qs)))
    prefixes = [q['text'].strip()[:90] for q in qs]
    dup = [p for p, c in Counter(prefixes).items() if c > 1]
    print('Duplicate prefixes:', dup if dup else 'none')

if __name__ == '__main__':
    main()
