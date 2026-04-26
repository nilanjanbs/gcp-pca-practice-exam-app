#!/usr/bin/env python3
"""Append q051-q070: 20 brand-new most-challenging PCA scenarios.
Topics intentionally chosen to NOT duplicate q001-q050.
"""
import json, os, sys
from collections import Counter

DB = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'database.json'))

NEW = [
    # 1
    {
        "id": "q051",
        "domain": "Reliability & Operations",
        "diff": "challenging",
        "text": "A SaaS provider runs identical production stacks in us-east4 and europe-west4 behind a single corporate domain (api.example.com). Requirements: route 80% of EU client traffic to europe-west4 and 20% to us-east4 (a beta cohort), DNS-level failover within 60 seconds if a region becomes unhealthy, and clients must continue working through DNS caches without manual intervention. Which design satisfies ALL requirements?",
        "opts": [
            "A single A record pointing to a global external Application Load Balancer; rely on the LB to do health-check failover; cache TTL 300s",
            "Cloud DNS public zone with a Routing Policy of type 'weighted round-robin' nested inside a 'geolocation' policy with EU=80/20 weights; attach health checks to each weighted target so unhealthy IPs are drained automatically; TTL 30s",
            "Cloud DNS with a 'failover' routing policy (primary=us-east4, secondary=europe-west4) and a separate CNAME for EU clients pointing directly to the EU LB",
            "Two A records (one per region) and instruct EU clients to manually pick the EU endpoint; rely on browser caching"
        ],
        "answer": 1,
        "explanation": "Cloud DNS Routing Policies support nested compositions — a geolocation policy can map EU/US client geographies, and inside the EU branch a weighted round-robin gives the 80/20 split. Health checks tied to the weighted targets automatically remove unhealthy endpoints from rotation. A single global ALB cannot represent two distinct backends weighted by client geography this way. A pure failover policy can't do weighted splits. Manual pinning ignores the cache-failover requirement.\n\n\ud83d\udd0d Targeted Search: 'Cloud DNS routing policies geolocation weighted', 'Cloud DNS health check routing'."
    },
    # 2
    {
        "id": "q052",
        "domain": "Designing & Planning",
        "diff": "challenging",
        "text": "A real-time analytics platform stores 80 TB of time-series sensor data in Bigtable. Reads come from two regions (us-central1 and asia-east1) with strict <30ms p95 latency. Writes are 90% from us-central1 and 10% from asia-east1. The team needs an architecture that survives a regional outage with RPO <60s and minimizes cross-region read latency. Which Bigtable topology is BEST?",
        "opts": [
            "Single-cluster instance in us-central1 with a read replica configured via Bigtable Data Boost in asia-east1",
            "Two-cluster instance (us-central1 + asia-east1) with multi-cluster routing app profile and consistent timestamp-based conflict resolution at the application layer; a single-cluster app profile per region is also defined for low-latency single-row workloads",
            "Two-cluster instance (us-central1 + asia-east1) with single-cluster routing per region for both reads and writes; clients pick the region by IP",
            "Three-cluster instance across us-central1, us-east1, and asia-east1 with multi-cluster routing for writes only; reads pinned to us-central1"
        ],
        "answer": 1,
        "explanation": "Bigtable replication is eventually consistent. The right pattern is a multi-cluster instance with TWO routing styles: (a) single-cluster app profiles when callers need monotonic reads in one region (low latency), and (b) a multi-cluster app profile that automatically fails over for HA. App-level conflict resolution handles the rare cross-region write conflicts. Data Boost is for analytical isolation, not multi-region replicas. Single-cluster routing for both removes failover. Three clusters add cost without serving the access pattern.\n\n\ud83d\udd0d Targeted Search: 'Bigtable multi-cluster routing app profiles', 'Bigtable replication conflict resolution'."
    },
    # 3
    {
        "id": "q053",
        "domain": "Analyzing & Optimizing",
        "diff": "challenging",
        "text": "A retail chain has 4 PB of historical sales data sitting in AWS S3 (us-east-1) and 2 PB of clickstream in Azure Blob (eastus). Analysts want to JOIN both with a transactional product catalog already in BigQuery (US multi-region). Requirements: avoid moving the raw data out of AWS/Azure for compliance, query latency under 30 seconds for ad-hoc analytics, and consistent IAM with the existing BigQuery dataset. Which approach is correct?",
        "opts": [
            "Use Storage Transfer Service to copy S3 and Azure Blob daily into BigQuery; query in place after copy",
            "Provision BigQuery Omni reservations in AWS us-east-1 and Azure eastus; create external tables backed by S3 and Azure Blob; use cross-cloud transfer (CREATE TABLE ... AS SELECT) only for filtered joined results that need to land in BigQuery US",
            "Run a Dataflow pipeline that streams from S3/Azure into Pub/Sub and lands in BigQuery; use materialized views for joins",
            "Mount S3 and Azure Blob via Cloud Storage FUSE on a Compute Engine VM and run federated queries from BigQuery to that VM"
        ],
        "answer": 1,
        "explanation": "BigQuery Omni runs the BigQuery query engine inside AWS and Azure regions, so raw data never leaves the source cloud (compliance), while the SQL surface and IAM are unified. Cross-cloud transfer materializes only the small joined result back to BigQuery US. Daily copy violates 'avoid moving raw data'. Dataflow streaming would still move data. Cloud Storage FUSE on a VM is not a federated query path.\n\n\ud83d\udd0d Targeted Search: 'BigQuery Omni AWS Azure', 'BigQuery cross-cloud transfer'."
    },
    # 4
    {
        "id": "q054",
        "domain": "Managing & Provisioning",
        "diff": "challenging",
        "text": "A financial-services firm needs a recurring batch workload that ingests SFTP files every 30 minutes, performs CPU-intensive transformations (OpenMP, no GPU), tolerates failure with idempotent retries, and has unpredictable per-run runtime (90s to 25 minutes). They want to avoid provisioning idle capacity and prefer a serverless model. Which Google Cloud service is BEST?",
        "opts": [
            "Cloud Run services with min-instances=1 and Cloud Scheduler invocations every 30 minutes",
            "Cloud Run jobs triggered by Cloud Scheduler, with task retries enabled and per-task max duration set to 60 minutes",
            "GKE CronJob on a regional cluster with cluster autoscaler and node auto-provisioning",
            "Cloud Functions Gen 2 with a Cloud Scheduler HTTP target and concurrency=1"
        ],
        "answer": 1,
        "explanation": "Cloud Run jobs are purpose-built for run-to-completion batch workloads with up to 24h per task, idempotent retries, and zero idle cost (you pay only for execution). Cloud Run services are for serving traffic; min-instances incurs idle cost. Cloud Functions Gen 2 has lower concurrency and a 60-min cap but is request-driven, not job-driven (and not optimized for steady CPU bursts). GKE CronJob requires a cluster.\n\n\ud83d\udd0d Targeted Search: 'Cloud Run jobs vs services', 'Cloud Run jobs scheduler'."
    },
    # 5
    {
        "id": "q055",
        "domain": "Security & Compliance",
        "diff": "challenging",
        "text": "A regulated bank wants developer environments accessible only from corporate-managed devices, with no source code stored on local machines, full session recording for audit, and the ability to spin up a per-engineer environment in <60s with the latest toolchain pre-installed. Which Google Cloud service is correct?",
        "opts": [
            "Compute Engine VMs per engineer with OS Login, IAP TCP forwarding for SSH, and Cloud Audit Logs for the SSH sessions",
            "Cloud Workstations clusters with custom container images, IAP for ingress, BeyondCorp Enterprise device-trust posture checks, and per-workstation persistent disks; gcloud workstations start command for fast boot",
            "GKE pods running an in-browser IDE with VPC-SC and a sidecar for session recording",
            "Cloud Shell Editor with extensions disabled and a custom Cloud Build image"
        ],
        "answer": 1,
        "explanation": "Cloud Workstations were built for this exact problem: managed dev environments, custom images, IAP/BCE device-trust integration, fast start, and per-engineer persistent disks for caches. Cloud Audit logs SSH commands but doesn't record full sessions; CE VMs lack the managed lifecycle. GKE-based browser IDE rolls your own. Cloud Shell isn't device-bound and doesn't satisfy fast-spin per-engineer custom images.\n\n\ud83d\udd0d Targeted Search: 'Cloud Workstations BeyondCorp Enterprise', 'Cloud Workstations custom image'."
    },
    # 6
    {
        "id": "q056",
        "domain": "Designing & Planning",
        "diff": "challenging",
        "text": "A multinational must publish public APIs that conform to two regulatory regimes: EU APIs must run with API gateway compute and policy execution physically in EU territory, while US APIs may use Google's global edge. Both regimes need consistent OAuth, quota, and analytics. Which Apigee deployment is correct?",
        "opts": [
            "Single Apigee X organization with all routing policies executed in us-central1; rely on EU Cloud CDN edges",
            "Apigee X for US APIs (regional in us-central1 with global routing) AND Apigee Hybrid runtime in a GKE cluster in europe-west1 for EU APIs; both managed under one Apigee X management plane for consistent policies and analytics",
            "Two completely separate Apigee X organizations (one per region) with manual policy duplication",
            "Apigee Edge (legacy SaaS) regional pods with traffic mirroring to a control plane"
        ],
        "answer": 1,
        "explanation": "Apigee Hybrid runs the runtime in your own GKE cluster (you choose the region) while keeping a single management plane in Apigee X for policies, OAuth, quotas, and analytics. This satisfies EU residency without policy duplication. Two separate orgs duplicate work. Apigee Edge is legacy and not the architectural recommendation.\n\n\ud83d\udd0d Targeted Search: 'Apigee Hybrid runtime regional', 'Apigee X management plane Hybrid'."
    },
    # 7
    {
        "id": "q057",
        "domain": "Designing & Planning",
        "diff": "challenging",
        "text": "A platform team operates 6 GKE clusters across 3 regions and 2 environments. They need: a single global routable hostname for each microservice (svc.example.com) that automatically picks the closest healthy cluster, mTLS between services, weighted canary rollouts across clusters, and L7 routing rules expressed as Kubernetes resources rather than gcloud CLI. Which architecture is correct?",
        "opts": [
            "Per-cluster ingress controllers + Cloud DNS geolocation routing policies; mTLS via cert-manager",
            "Cloud Service Mesh (managed Anthos Service Mesh) configured as a fleet across all clusters, with multi-cluster Gateway API resources and TrafficPolicies/DestinationRules; mTLS enabled fleet-wide",
            "External global LB with multiple backend services, manually shaped weighted backend distributions; mTLS terminated at envoy sidecars",
            "Use Network Endpoint Groups (NEGs) per pod and Cloud DNS routing policies"
        ],
        "answer": 1,
        "explanation": "Cloud Service Mesh + multi-cluster Gateway gives you fleet-wide K8s-resource-driven L7 routing, automatic closest-cluster selection, mTLS enforcement, and weighted canaries via TrafficSplit/DestinationRule — the only choice that hits ALL constraints declaratively. Per-cluster ingress + DNS geolocation is fragmented and lacks mesh policy. Manual LB weights drift and don't enforce mTLS. NEGs+DNS won't express L7 rules.\n\n\ud83d\udd0d Targeted Search: 'GKE multi-cluster Gateway API', 'Cloud Service Mesh fleet mTLS'."
    },
    # 8
    {
        "id": "q058",
        "domain": "Security & Compliance",
        "diff": "challenging",
        "text": "Before enforcing a new VPC Service Controls perimeter that will lock down BigQuery, Cloud Storage, and Cloud KMS, the security team must understand which existing access patterns would break, without disrupting production. Additionally, partner organizations need read-only BigQuery access from outside the perimeter for a daily reporting job. Which configuration is correct?",
        "opts": [
            "Enable the perimeter immediately; rely on Cloud Audit Logs after-the-fact to discover breakage; create an access-level for the partners",
            "Configure the perimeter in dry-run mode first; analyze 'VPC Service Controls violations' in the Cloud Logging dry-run logs for at least one full business cycle; then add an Ingress Policy that allows the partner's identities (via a Service Account or Workforce Pool) into BigQuery read operations only; finally enforce the perimeter",
            "Use Organization Policy 'restrictedSharedVPCSubnetworks' as a substitute for VPC SC; partners get IAM roles directly",
            "Place partners inside the perimeter via VPN; do not use dry-run; rely on staging environments"
        ],
        "answer": 1,
        "explanation": "Dry-run mode emits violation logs without blocking traffic — exactly what 'understand impact without disrupting production' requires. Ingress Policies (with attribute conditions) let specific partner identities cross the perimeter for narrowly-scoped operations like BigQuery read. Skipping dry-run risks production outages. Org Policy restrictedSharedVPCSubnetworks doesn't replace VPC SC. VPN with partners inside the perimeter overshares.\n\n\ud83d\udd0d Targeted Search: 'VPC Service Controls dry-run mode', 'VPC SC Ingress Policy attribute conditions'."
    },
    # 9
    {
        "id": "q059",
        "domain": "Managing Implementation",
        "diff": "challenging",
        "text": "An ETL team must orchestrate a daily DAG with 60 tasks: BigQuery SQL, Dataflow Python jobs, REST calls to a third-party SaaS, and conditional branching based on row counts. Operators want a Python-defined DAG with built-in retries, calendar-based scheduling, dynamic task generation, and the ability to enforce per-task IAM. Which service is BEST?",
        "opts": [
            "Cloud Workflows with YAML steps and Cloud Scheduler triggers",
            "Cloud Composer 2 (Apache Airflow on GKE Autopilot) with the GoogleCloudPlatformHook operators and per-DAG service accounts for IAM scoping",
            "Cloud Tasks queues with scheduled Cloud Run targets",
            "Eventarc Advanced pipelines fan-in/fan-out"
        ],
        "answer": 1,
        "explanation": "Composer 2 (Airflow) excels at Python DAGs, dynamic task generation, calendar/cron schedules, retries, and per-task connections / service accounts for IAM. Workflows is YAML-only and weaker at dynamic DAG generation. Cloud Tasks is for queue-and-execute, not DAG orchestration. Eventarc is event routing, not orchestration.\n\n\ud83d\udd0d Targeted Search: 'Cloud Composer 2 vs Workflows', 'Airflow per-task service account'."
    },
    # 10
    {
        "id": "q060",
        "domain": "Analyzing & Optimizing",
        "diff": "challenging",
        "text": "A team needs near-real-time analytics on a Cloud SQL for PostgreSQL operational database (50 GB, 2k TPS write). Requirements: <60s lag from source to BigQuery, no impact on the OLTP database, schema evolution must propagate automatically, and analysts query with standard SQL. Which approach is correct?",
        "opts": [
            "Cloud Functions on a Cloud SQL trigger writing to BigQuery streaming inserts",
            "Datastream stream from Cloud SQL (logical replication) into BigQuery (with the BigQuery destination for Datastream); Datastream uses CDC and propagates schema changes",
            "Hourly batch SELECT * FROM TABLE WHERE updated_at > now() - 1h via Dataflow",
            "BigQuery Federated Query against Cloud SQL via EXTERNAL_QUERY()"
        ],
        "answer": 1,
        "explanation": "Datastream uses logical CDC replication, has a native BigQuery destination, supports automatic schema propagation, and incurs minimal load on the source. Cloud SQL doesn't support DB-side triggers that write to GCS/BQ securely. Hourly batch misses the 60s lag target. Federated Query loads the OLTP DB on every analyst query.\n\n\ud83d\udd0d Targeted Search: 'Datastream BigQuery destination CDC', 'Datastream schema evolution'."
    },
    # 11
    {
        "id": "q061",
        "domain": "Designing & Planning",
        "diff": "challenging",
        "text": "An e-commerce platform has 1 TB of transactional data in PostgreSQL and runs both: (a) low-latency OLTP transactions (10k TPS, single-row reads) and (b) analytical reporting that joins across 6 large tables. They want a single managed PostgreSQL-compatible engine that handles BOTH workloads with <100ms OLTP latency AND analytical query speed-ups, while keeping a single connection string. Which is BEST?",
        "opts": [
            "Cloud SQL for PostgreSQL Enterprise Plus with read replicas dedicated to analytics",
            "AlloyDB for PostgreSQL with the columnar engine enabled for analytical tables; OLTP traffic uses the row store transparently and analytics queries use the columnar accelerator",
            "Spanner with PostgreSQL interface and split tables for OLTP and OLAP",
            "BigQuery for analytics + Cloud SQL for OLTP with periodic ETL"
        ],
        "answer": 1,
        "explanation": "AlloyDB's columnar engine is an in-memory accelerator that automatically materializes hot analytical columns, while OLTP queries continue to hit the row store — all on a single PostgreSQL endpoint. This is the only HTAP-on-Postgres-compatible option without a second connection string or ETL. Cloud SQL EE+ replicas still require analytics-specific routing logic. Spanner doesn't support all PostgreSQL analytic functions and is overkill at 1 TB. BigQuery+Cloud SQL adds ETL.\n\n\ud83d\udd0d Targeted Search: 'AlloyDB columnar engine', 'AlloyDB HTAP'."
    },
    # 12
    {
        "id": "q062",
        "domain": "Reliability & Operations",
        "diff": "challenging",
        "text": "A regulated workload requires Cloud Storage data to be replicated to a secondary region with RPO under 15 minutes (not eventual consistency) and a cost premium that scales with replicated GB rather than total storage. Which feature is correct?",
        "opts": [
            "Dual-region bucket with default async replication (eventual consistency)",
            "Multi-region bucket with default async replication",
            "Dual-region or multi-region bucket with Turbo Replication enabled — provides a 15-minute SLO (not just SLA-style eventual replication) and is billed as a per-GB operation surcharge",
            "Object Lifecycle rule that copies objects nightly to a regional bucket in the secondary region"
        ],
        "answer": 2,
        "explanation": "Turbo Replication is the only Cloud Storage feature that provides a 15-minute RPO SLO with per-GB pricing. Default dual-region/multi-region replication is async/eventual without that guarantee. Lifecycle copies are nightly. The other options miss the 15-minute target.\n\n\ud83d\udd0d Targeted Search: 'Cloud Storage Turbo Replication 15-minute RPO', 'Cloud Storage dual-region turbo'."
    },
    # 13
    {
        "id": "q063",
        "domain": "Managing & Provisioning",
        "diff": "challenging",
        "text": "A team wants to add a structured-log forwarder and a service-mesh proxy alongside their existing Cloud Run service WITHOUT rebuilding the application image, and have the application container start ONLY after the proxy is ready. Which Cloud Run feature is correct?",
        "opts": [
            "Cloud Run multi-container deployments (sidecars) with one ingress container and additional sidecar containers; a startup-order dependency expressed via container ordering and a depends_on equivalent (startup probe on the proxy + dependsOn in the service definition)",
            "A second Cloud Run service that the main service calls over HTTP for logs and proxying",
            "Cloud Run jobs triggered by the service to handle log forwarding",
            "Run two Cloud Run revisions and use traffic-splitting to combine them"
        ],
        "answer": 0,
        "explanation": "Cloud Run multi-container (sidecars) lets you add proxies, log shippers, etc. into the same instance with shared localhost networking. Container start order can be enforced (startup probe + dependsOn) so the app waits for the proxy. The other choices either separate runtime context or misuse the feature.\n\n\ud83d\udd0d Targeted Search: 'Cloud Run sidecar container', 'Cloud Run multi-container dependsOn'."
    },
    # 14
    {
        "id": "q064",
        "domain": "Managing Implementation",
        "diff": "challenging",
        "text": "An ML team trains a recommendation model weekly. Requirements: tracked experiments, dataset and model lineage, parameterized recurring runs, drift-monitored deployment to a Vertex AI Endpoint, and rollback to a previous model version on metric regression. Which architecture is correct?",
        "opts": [
            "A custom Cloud Build pipeline that calls Vertex AI Custom Jobs and uses gcloud to deploy a model; rollback via manual gcloud commands",
            "Vertex AI Pipelines (KFP v2) with components for ingest \u2192 train \u2192 evaluate \u2192 conditional deploy; Vertex AI Model Registry stores versions; Vertex AI Model Monitoring on the endpoint emits drift alerts; Cloud Build triggers the pipeline weekly; rollback by routing endpoint traffic to the prior model version",
            "Argo Workflows on GKE manually wired to gcloud CLI",
            "Cloud Composer DAG that calls Python-SDK gcloud commands for training and deployment"
        ],
        "answer": 1,
        "explanation": "Vertex AI Pipelines is purpose-built for end-to-end ML lifecycle: lineage tracking, parameterized runs, conditional steps, and integrates natively with Model Registry, Endpoints, and Model Monitoring. Traffic split-based rollback on the endpoint is a one-liner. The other options reinvent these features and lack lineage/drift integration.\n\n\ud83d\udd0d Targeted Search: 'Vertex AI Pipelines KFP v2', 'Vertex AI Model Monitoring drift'."
    },
    # 15
    {
        "id": "q065",
        "domain": "Security & Compliance",
        "diff": "challenging",
        "text": "An internal HR application runs as a Compute Engine instance group with no public IP. Employees must reach it from any laptop (corporate or BYOD) without VPN, with continuous device-posture and identity verification, and access must be revoked instantly when an employee leaves. Which architecture is correct?",
        "opts": [
            "Cloud VPN to a corporate identity SAML IdP; per-user IAM bindings; manual offboarding script",
            "Identity-Aware Proxy (IAP) in front of an internal HTTP(S) Load Balancer with BeyondCorp Enterprise access levels using device-attribute conditions; identity provided by Workspace; offboarding via Workspace removes IAP access immediately",
            "External HTTPS LB with Cloud Armor policy listing approved IP CIDRs; IAM by Google Group",
            "Place the VMs on a public IP and rely on OS-level firewall rules + 2FA"
        ],
        "answer": 1,
        "explanation": "IAP + BeyondCorp Enterprise is the textbook zero-trust pattern: per-request identity + device posture, no VPN, instant revocation when the Workspace user is suspended. Cloud Armor IP allowlists don't do device posture. Public IPs + OS firewall is the wrong direction. VPN + manual offboarding can't deliver instant revocation reliably.\n\n\ud83d\udd0d Targeted Search: 'Identity-Aware Proxy BeyondCorp Enterprise', 'IAP access levels device posture'."
    },
    # 16
    {
        "id": "q066",
        "domain": "Designing & Planning",
        "diff": "challenging",
        "text": "An enterprise has 14 VPCs across 4 regions and 2 organizations (post-acquisition). They need consolidated transit between all VPCs, transitive on-prem connectivity from a single Dedicated Interconnect, and centralized routing policy. They want to avoid full-mesh VPC peering. Which Google Cloud service is correct?",
        "opts": [
            "Configure full-mesh VPC peering between every pair of VPCs and use custom routes",
            "Network Connectivity Center (NCC) with VPC spokes (or hybrid spokes for the Dedicated Interconnect) all attached to a single hub for transitive routing and centralized policy",
            "Place all workloads in a single Shared VPC across both organizations",
            "Multiple VPNs between every pair of VPCs"
        ],
        "answer": 1,
        "explanation": "Network Connectivity Center with VPC spokes provides transitive, hub-and-spoke routing across many VPCs and integrates hybrid spokes (Interconnect/VPN) — eliminating full-mesh peering and enabling centralized policy. Shared VPC across two orgs isn't possible. Full-mesh peering and pair-wise VPNs scale poorly and don't yield transitive routing.\n\n\ud83d\udd0d Targeted Search: 'Network Connectivity Center VPC spoke', 'NCC hybrid spoke transitive routing'."
    },
    # 17
    {
        "id": "q067",
        "domain": "Reliability & Operations",
        "diff": "challenging",
        "text": "A platform consumes events from 12 Cloud Storage buckets in 3 regions and routes them to region-local Cloud Run consumers, with delivery retries, dead-letter routing, attribute-based filtering, and a single declarative pipeline definition. Which service is correct?",
        "opts": [
            "Eventarc Standard with one trigger per bucket, written by hand for each region",
            "Eventarc Advanced pipelines: a region-aware pipeline with sources (Cloud Storage), transformations, and a Cloud Run destination; built-in retries, DLQs, attribute filters, and YAML/Terraform-friendly pipeline definitions",
            "Pub/Sub with bucket notifications + manual subscriptions; write Cloud Run destinations as push subscribers",
            "Cloud Workflows triggered by GCS finalize events for each bucket"
        ],
        "answer": 1,
        "explanation": "Eventarc Advanced pipelines deliver a single declarative pipeline definition with sources, transformations, filters, retries, and DLQ — the right managed primitive for multi-source/multi-region event mesh. Eventarc Standard scales by trigger count but lacks the unified pipeline. Pub/Sub-with-push works but you re-implement filters/DLQ/retries. Workflows is for orchestration, not event mesh.\n\n\ud83d\udd0d Targeted Search: 'Eventarc Advanced pipelines', 'Eventarc Advanced DLQ filter'."
    },
    # 18
    {
        "id": "q068",
        "domain": "Security & Compliance",
        "diff": "challenging",
        "text": "Compliance requires automatic detection and remediation when any Cloud Storage bucket becomes public, when any SQL instance disables backups, or when an organization-policy violation drift occurs. The team wants a single source of truth, near-real-time response, and to audit who/what changed every resource. Which architecture is correct?",
        "opts": [
            "Schedule a daily Cloud Function that calls gcloud asset list and compares against a JSON baseline",
            "Cloud Asset Inventory feeds (real-time change feed) to Pub/Sub \u2192 Cloud Run/Functions remediation handlers; combine with Security Command Center Premium for severity scoring; Cloud Audit Logs provide who/what",
            "Periodic Forseti scans triggered by Cloud Scheduler",
            "Custom Stackdriver alerting policies on log-based metrics for each violation type"
        ],
        "answer": 1,
        "explanation": "Cloud Asset Inventory feeds emit real-time change events to Pub/Sub for any resource type, enabling event-driven remediation. SCC Premium adds severity scoring and posture context. Audit Logs supply attribution. Daily Cloud Functions miss the near-real-time goal. Forseti is a community tool largely superseded by SCC. Custom log-based metrics scale poorly across many violation types.\n\n\ud83d\udd0d Targeted Search: 'Cloud Asset Inventory feed Pub/Sub', 'Security Command Center Premium posture'."
    },
    # 19
    {
        "id": "q069",
        "domain": "Managing Implementation",
        "diff": "challenging",
        "text": "An enterprise must migrate 600 VMware VMs (Windows + Linux) running stateful workloads from an on-prem vCenter to Google Cloud, with a 4-hour cutover window per wave, application-consistent snapshots, and the ability to do test failovers in an isolated VPC without disturbing production. Which service is correct?",
        "opts": [
            "Migrate to Containers (Migrate for Anthos) to convert VMs to containers and deploy on GKE",
            "Backup and DR Service (formerly Actifio GO) with continuous block-change replication to GCS-backed appliances; isolated test failover into a non-routable VPC; final cutover via DNS swing",
            "Storage Transfer Service to copy VM disks to Cloud Storage and recreate VMs in Compute Engine",
            "Manually export OVAs and import via gcloud compute images create"
        ],
        "answer": 1,
        "explanation": "Backup and DR Service (the former Actifio offering) is purpose-built for VMware VM workloads with application-consistent snapshots, low-RPO replication, and isolated test failover into a non-routable VPC. M2C is for containerization (different goal). STS doesn't handle live VMs. OVA imports lack continuous replication and isolated test failover.\n\n\ud83d\udd0d Targeted Search: 'Backup and DR Service VMware migration', 'Actifio GO test failover'."
    },
    # 20
    {
        "id": "q070",
        "domain": "Reliability & Operations",
        "diff": "challenging",
        "text": "A global SaaS sets a single 99.95% availability SLO across 3 regions for a customer-facing API. The SRE team wants the SLO to reflect 'the user could complete the request from anywhere' rather than per-region availability, and the alerting must be driven by a unified error budget across all regions. Which strategy is correct?",
        "opts": [
            "Define one SLO per region; alert when any region individually breaches 99.95%; declare incident if any region degrades",
            "Define a single global SLO using a Cloud Monitoring service-level indicator that aggregates per-region good/bad event counters into a single ratio; configure multi-window multi-burn-rate alerts on that aggregated SLI; per-region dashboards remain for diagnostics only",
            "Define one SLO per region and average them in a custom dashboard for reporting",
            "Use Service Monitoring 'auto-detected' SLOs with default thresholds and aggregate by labels in a separate Looker Studio report"
        ],
        "answer": 1,
        "explanation": "User-facing SLOs should reflect user experience, not infrastructure topology. A single global SLI aggregating good/bad events across regions yields one error budget, one set of burn-rate alerts, and aligns with Google SRE guidance. Per-region SLOs over-page for partial regional dips that users may not feel (because of LB failover). Averaging SLOs is mathematically wrong (hides outages). Auto-SLOs without aggregation misses the whole point.\n\n\ud83d\udd0d Targeted Search: 'Cloud Monitoring SLO aggregated SLI', 'global SLO multi-region SRE'."
    },
]

def main():
    if not os.path.exists(DB):
        print('ERROR: database.json missing', file=sys.stderr); sys.exit(1)
    with open(DB, 'r', encoding='utf-8') as f:
        db = json.load(f)
    qs = db.setdefault('pca:seed-questions', [])
    existing_ids = {q.get('id') for q in qs}
    existing_texts = {q.get('text', '').strip()[:80] for q in qs}

    appended = 0
    for nq in NEW:
        if nq['id'] in existing_ids:
            print(f"SKIP duplicate id {nq['id']}"); continue
        prefix = nq['text'].strip()[:80]
        if prefix in existing_texts:
            print(f"SKIP duplicate scenario prefix for {nq['id']}"); continue
        qs.append(nq)
        appended += 1

    with open(DB, 'w', encoding='utf-8') as f:
        json.dump(db, f, indent=2, ensure_ascii=True)

    print(f'Appended {appended}. Total: {len(qs)}')
    print('Diffs:', dict(Counter(q['diff'] for q in qs)))
    print('Domains:', dict(Counter(q['domain'] for q in qs)))
    # Sanity: ensure no dup scenarios across the entire set (first 80 chars)
    prefixes = [q['text'].strip()[:80] for q in qs]
    dup = [p for p, c in Counter(prefixes).items() if c > 1]
    print('Duplicate prefixes:', dup if dup else 'none')

if __name__ == '__main__':
    main()
