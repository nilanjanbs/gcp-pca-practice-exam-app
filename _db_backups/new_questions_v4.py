#!/usr/bin/env python3
"""Append q101-q120: 20 brand-new HARD + CHALLENGING PCA scenarios.
10 hard + 10 challenging. All topics distinct from q001-q100.
"""
import json, os, sys
from collections import Counter

DB = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'database.json'))

NEW = [
    # 1
    {
        "id": "q101",
        "domain": "Security & Compliance",
        "diff": "challenging",
        "text": "A `customer_orders` BigQuery table contains PII (email, phone) and is queried by three audiences: (a) finance analysts who need full data for one EU country only, (b) data scientists who must NOT see PII but need to see all rows globally, and (c) a marketing team that should only see orders > $1000 with email shown as `j****@gmail.com`. The team wants this enforced inside BigQuery, not via copies. Which combination is correct?",
        "opts": [
            "Three Authorized Views with hard-coded WHERE clauses; share each view with the right group",
            "**Row-level security** policies on the country column for finance + data scientists; **column-level access control** (policy tags via Data Catalog) hiding `email`/`phone` from data scientists; **dynamic data masking** rules for marketing that mask the `email` column with a partial-mask routine",
            "BigQuery Authorized UDFs that re-implement masking logic in SQL",
            "Materialize three tables (one per audience) refreshed nightly via Dataform"
        ],
        "answer": 1,
        "explanation": "BigQuery's three native fine-grained controls compose for exactly this case: row-level security filters rows, column-level access control (policy tags) hides whole columns from a principal, and dynamic data masking transforms values without copies. Authorized Views are coarse and proliferate. UDFs re-implement features that already exist. Triple-materialization adds cost and freshness lag.\n\n\ud83d\udd0d Targeted Search: 'BigQuery row-level security', 'BigQuery dynamic data masking policy tags'."
    },
    # 2
    {
        "id": "q102",
        "domain": "Analyzing & Optimizing",
        "diff": "hard",
        "text": "Operators investigate incidents by running ad-hoc text searches across 12 TB of stringified payload columns in BigQuery (e.g., LIKE '%trace_id_abc%'). Each query scans the whole table and is slow + expensive. Which BigQuery feature most directly addresses this?",
        "opts": [
            "Materialized views aggregating by hour",
            "**BigQuery search indexes** on the high-cardinality string columns; queries use `SEARCH()` to skip non-matching files at scan time",
            "Partition the table by `_PARTITIONTIME` and require partition filter",
            "BI Engine reservation for the table"
        ],
        "answer": 1,
        "explanation": "BigQuery search indexes (CREATE SEARCH INDEX...) accelerate token/substring lookups via the SEARCH() function, dramatically reducing bytes scanned. MVs help aggregations, not text scan. Partitioning by ingestion time doesn't help arbitrary substring searches. BI Engine accelerates aggregation in memory but not text search.\n\n\ud83d\udd0d Targeted Search: 'BigQuery CREATE SEARCH INDEX', 'BigQuery SEARCH function'."
    },
    # 3
    {
        "id": "q103",
        "domain": "Reliability & Operations",
        "diff": "challenging",
        "text": "An analyst accidentally ran `TRUNCATE TABLE customers` in BigQuery 3 hours ago. Requirements: recover the table to its state from 4 hours ago, ensure it can be recovered up to 7 days post-incident if needed again, and minimize ongoing cost. Which approach is correct?",
        "opts": [
            "Restore from a daily Cloud Storage snapshot; create a Dataflow pipeline to keep snapshots fresh",
            "Use BigQuery **time travel** (default 7-day window) with `FOR SYSTEM_TIME AS OF TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 4 HOUR)` to copy data back; create a **table snapshot** afterward to lock in the recovered state and extend retention beyond the 7-day window",
            "Restore from the BigQuery Failsafe storage tier via support ticket",
            "Replay from the source by re-running the upstream Dataflow pipeline"
        ],
        "answer": 1,
        "explanation": "BigQuery time travel covers up to 7 days at no extra cost — perfect for fast 4-hour-ago recovery. Table snapshots are zero-copy point-in-time captures and can be retained beyond the time-travel window cheaply. Snapshot-then-restore is the standard incident response pattern. Failsafe is an internal tier and not a self-service feature. Replay is brittle and slow.\n\n\ud83d\udd0d Targeted Search: 'BigQuery time travel FOR SYSTEM_TIME AS OF', 'BigQuery table snapshots'."
    },
    # 4
    {
        "id": "q104",
        "domain": "Security & Compliance",
        "diff": "hard",
        "text": "A SaaS app stores customer documents in Cloud Storage. Compliance requires: (a) a 30-day grace period to recover any object accidentally or maliciously deleted, even if a service account with delete permission was compromised, AND (b) per-object retention up to 7 years for regulatory holds — independent of the bucket's lifecycle. Which feature combination is correct?",
        "opts": [
            "Object Versioning + a daily lifecycle rule to NoncurrentTimeBefore",
            "**Soft Delete policy** on the bucket (30-day default retention for deleted objects, recoverable via API even by attackers' deletes) + **Object Retention** locks for 7-year per-object regulatory holds",
            "Bucket Lock with a 7-year retention policy",
            "Manual nightly copies to a second bucket with public access prevention"
        ],
        "answer": 1,
        "explanation": "Cloud Storage Soft Delete recovers any deleted object within the configured policy window — even if delete permissions were used. Object Retention locks individual objects for a per-object duration independent of the bucket's lifecycle, which is exactly what 'per-object 7-year hold' requires. Bucket Lock applies one retention to the whole bucket. Object Versioning + lifecycle is brittle and doesn't survive a permissioned delete attack the same way.\n\n\ud83d\udd0d Targeted Search: 'Cloud Storage soft delete policy', 'Cloud Storage object retention lock'."
    },
    # 5
    {
        "id": "q105",
        "domain": "Analyzing & Optimizing",
        "diff": "challenging",
        "text": "A genomics workload reads a 200 TB Cloud Storage dataset from many GKE clusters across us-central1, us-east1, and europe-west1. Egress charges and read latency to the bucket's home region are unacceptable. Requirements: read-through cache that's transparent to existing GCS clients, billed only for cached data, and consistent with the underlying bucket. Which feature is correct?",
        "opts": [
            "Replicate the whole bucket nightly to per-region buckets and update clients to use the closest one",
            "Enable **Cloud Storage Anywhere Cache** zonal caches in each consuming region; clients use the same bucket URL and reads are served from the cache automatically",
            "Use Cloud CDN with a backend bucket and signed URLs",
            "Mount the bucket via Cloud Storage FUSE on each pod and rely on local OS cache"
        ],
        "answer": 1,
        "explanation": "Anywhere Cache is the managed, zonal read-through cache for Cloud Storage — clients keep using the bucket URL, only cached data is billed, consistency is preserved. Nightly replicas duplicate 200 TB and require client routing. Cloud CDN is for HTTP edge serving, not GCS-native compute reads. FUSE per-pod cache is fragmented and not coherent.\n\n\ud83d\udd0d Targeted Search: 'Cloud Storage Anywhere Cache', 'GCS zonal read-through cache'."
    },
    # 6
    {
        "id": "q106",
        "domain": "Designing & Planning",
        "diff": "challenging",
        "text": "Two GKE clusters in different regions belong to the same fleet. Workloads in cluster-A must call services in cluster-B by their Kubernetes Service name (e.g., `payments.api.svc.cluster.local`) without inventing per-cluster DNS hacks or operating an external service registry. Which feature is correct?",
        "opts": [
            "Manually create headless Services in each cluster and synchronize endpoints with a custom controller",
            "**Multi-cluster Services (MCS)** with Fleet — export a Service from cluster-B (`ServiceExport`) and import it in cluster-A (`ServiceImport`); cross-cluster requests resolve via the fleet's coordinated DNS",
            "Cloud DNS private zones with one record per Service, manually maintained",
            "External global LB with each Service registered as a backend NEG"
        ],
        "answer": 1,
        "explanation": "GKE Fleet's Multi-cluster Services (MCS) is the K8s-native answer: ServiceExport/ServiceImport CRDs cause services to be reachable by Kubernetes name across the fleet. The other choices either reinvent service discovery or push it into infrastructure layers that don't preserve K8s naming.\n\n\ud83d\udd0d Targeted Search: 'GKE Multi-cluster Services MCS ServiceExport', 'GKE Fleet MCS'."
    },
    # 7
    {
        "id": "q107",
        "domain": "Managing Implementation",
        "diff": "hard",
        "text": "A regulated team must produce SLSA Level 3 build provenance for every container image, sign images, and prevent unsigned images from running on GKE — all using Google-native tooling. Which combination is correct?",
        "opts": [
            "GitHub Actions with cosign + a custom admission webhook on GKE",
            "**Cloud Build** with provenance generation enabled (SLSA L3) + **Artifact Analysis** vulnerability scanning + **Binary Authorization** policy that requires attestations from a Cloud Build attestor before deploy on GKE",
            "Spinnaker pipelines with manual sign-off",
            "Anthos Config Management as the only enforcement"
        ],
        "answer": 1,
        "explanation": "Cloud Build natively emits SLSA L3 provenance, Artifact Analysis (formerly Container Analysis) scans + signs, and Binary Authorization gates deployment based on attestations — the integrated, Google-native answer. The other options either rely on third-party tooling or skip the gating step.\n\n\ud83d\udd0d Targeted Search: 'Cloud Build SLSA Level 3 provenance', 'Binary Authorization Cloud Build attestor'."
    },
    # 8
    {
        "id": "q108",
        "domain": "Managing & Provisioning",
        "diff": "hard",
        "text": "Developers consume thousands of npm/PyPI/Maven packages from public registries. The platform team wants to (a) cache and proxy upstream so the build doesn't fail when pypi.org is down, (b) scan all consumed packages for vulnerabilities, and (c) provide ONE registry URL to internal builds that aggregates internal + upstream. Which Artifact Registry feature is correct?",
        "opts": [
            "Standard repositories per language with manual mirroring scripts",
            "**Remote repositories** (proxy + cache upstream registries) plus **Virtual repositories** that aggregate internal + remote + standard repositories under a single URL; combine with Artifact Analysis vulnerability scanning",
            "Cloud Source Repositories with per-package mirrors",
            "GCS bucket with package tarballs"
        ],
        "answer": 1,
        "explanation": "Artifact Registry Remote repositories proxy/cache upstream registries; Virtual repositories aggregate multiple repositories behind one URL — together solving the resilience and unification needs. Manual mirroring is operationally costly. CSR is git, not packages. GCS lacks package-manager semantics.\n\n\ud83d\udd0d Targeted Search: 'Artifact Registry remote repository', 'Artifact Registry virtual repository'."
    },
    # 9
    {
        "id": "q109",
        "domain": "Designing & Planning",
        "diff": "challenging",
        "text": "An enterprise replaces Cloud Interconnect with a VPN-based hybrid for a secondary data center. Requirements: 99.99% availability, both on-prem and GCP gateways must run active-active, BGP routing exchanged dynamically, and traffic spread across both tunnels in steady state. Which architecture is correct?",
        "opts": [
            "Single Classic VPN gateway with a static route to on-prem",
            "**HA VPN** with two interfaces on each side (active-active), four IPsec tunnels (2x2 mesh), Cloud Router on GCP and the on-prem router exchanging BGP, ECMP for traffic distribution",
            "Two Classic VPN gateways in different regions with static routes",
            "HA VPN with one tunnel and a backup Classic VPN as failover"
        ],
        "answer": 1,
        "explanation": "HA VPN with two interfaces per side (so 4 tunnels in a 2x2 mesh) and dynamic BGP via Cloud Router meets the 99.99% SLA in active-active. Classic VPN does not. Single-tunnel HA VPN doesn't reach 99.99%. Two Classic gateways with static routes lacks BGP and the 99.99% SLA.\n\n\ud83d\udd0d Targeted Search: 'HA VPN 99.99% SLA', 'HA VPN active-active BGP'."
    },
    # 10
    {
        "id": "q110",
        "domain": "Designing & Planning",
        "diff": "hard",
        "text": "A private internal service must be reachable from any VPC in any region inside the same organization, with a single private DNS name, automatic failover, and no public IP. Which load balancer is correct?",
        "opts": [
            "Regional Internal HTTP(S) Load Balancer in each region; Cloud DNS geolocation policy",
            "**Cross-region Internal Application Load Balancer** (global ILB) — one global private VIP, multi-region backends, internal access from peered VPCs across the org",
            "Internal Network Load Balancer (TCP) with regional fallback",
            "External Application Load Balancer with allowlisted internal CIDRs"
        ],
        "answer": 1,
        "explanation": "The cross-region (global) Internal Application Load Balancer gives a single private VIP that load-balances across regional backends, with multi-region failover — all without exposing public IPs. Per-region ILBs require client-side routing. Internal NLB is L4 only. External LB exposes a public IP.\n\n\ud83d\udd0d Targeted Search: 'Cross-region Internal Application Load Balancer', 'global internal HTTPS LB'."
    },
    # 11
    {
        "id": "q111",
        "domain": "Reliability & Operations",
        "diff": "challenging",
        "text": "An SRE diagnoses why a Compute Engine VM in us-east4 cannot reach a Cloud SQL instance in europe-west1 over Private Service Connect. They need a tool that simulates the path, shows the firewall rules and routes evaluated, and reports where the packet is dropped — without sending production traffic. Which feature is correct?",
        "opts": [
            "Run `traceroute` from the VM and inspect Cloud Logging",
            "Use **Network Intelligence Center \u2192 Connectivity Tests** to simulate the path between source and destination; the report shows route lookups, firewall rules, NAT, and the drop reason",
            "Enable VPC Flow Logs and grep for the destination IP",
            "Use Cloud Trace to follow the packet"
        ],
        "answer": 1,
        "explanation": "Connectivity Tests in Network Intelligence Center is the GCP-native simulator that walks the path, evaluates each network construct, and pinpoints drop reasons — without injecting traffic. Traceroute can fail through Google's fabric. Flow Logs help post-mortem but not pre-flight simulation. Cloud Trace is for application traces.\n\n\ud83d\udd0d Targeted Search: 'Network Intelligence Center Connectivity Tests', 'GCP connectivity test drop reason'."
    },
    # 12
    {
        "id": "q112",
        "domain": "Security & Compliance",
        "diff": "hard",
        "text": "A regulated workload must restrict a service account's `roles/storage.admin` so it only applies (a) on weekdays 09:00\u201318:00 in Asia/Kolkata, (b) when the request comes from the corporate IP range, and (c) only on buckets whose name starts with `prod-`. Which mechanism is correct?",
        "opts": [
            "Set Org Policy constraints on bucket access",
            "**IAM Conditions** on the binding using attribute conditions: `request.time` for the time window, `request.auth.access_levels` (Access Context Manager) for the IP range, and `resource.name.startsWith('projects/_/buckets/prod-')` for the resource scope",
            "Cloud Functions audit hook that revokes the role outside hours",
            "Multiple service accounts, one per condition combination"
        ],
        "answer": 1,
        "explanation": "IAM Conditions (CEL) attach attribute predicates to a role binding — covering time window, request source (via Access Context Manager access levels), and resource name prefix in one binding. Org Policy is coarser. Custom audit hooks have race windows. Multiple SAs explode operational overhead.\n\n\ud83d\udd0d Targeted Search: 'IAM Conditions request.time access levels', 'IAM Conditions resource.name.startsWith'."
    },
    # 13
    {
        "id": "q113",
        "domain": "Security & Compliance",
        "diff": "challenging",
        "text": "A CI/CD pipeline runs on GKE. It needs to deploy to a customer project for each tenant, each customer has their own GCP project and grants only the rights they need. The platform team wants ZERO long-lived service-account keys, attribute-bound delegation, and full audit trail of who-did-what across project boundaries. Which approach is correct?",
        "opts": [
            "Generate a JSON key per customer service account and store in Secret Manager",
            "Workload Identity Federation from GKE \u2192 a platform service account; that platform SA uses **service account impersonation chains** (via `iam.serviceAccounts.getAccessToken`) to assume customer-specific service accounts in tenant projects, with audit logs capturing every impersonation hop",
            "Cross-project IAM bindings granting the GKE node SA Editor in every customer project",
            "OAuth2 client credentials flow with shared client secret"
        ],
        "answer": 1,
        "explanation": "Workload Identity (GKE) eliminates long-lived keys; impersonation chains (the platform SA can call `serviceAccounts.getAccessToken` to mint tokens for tenant SAs) provide bounded, audited delegation. Cross-project Editor is over-privileged and broad. JSON keys are exactly what we want to avoid. Shared client secrets are insecure.\n\n\ud83d\udd0d Targeted Search: 'service account impersonation chain', 'iam.serviceAccounts.getAccessToken Workload Identity'."
    },
    # 14
    {
        "id": "q114",
        "domain": "Security & Compliance",
        "diff": "hard",
        "text": "Security must continuously identify over-privileged service accounts (granted Editor but only ever using Storage Object Viewer in the past 90 days) across the organization and produce remediation suggestions, without manually reviewing each project. Which Google-native capability is correct?",
        "opts": [
            "Cloud Audit Logs + a custom BigQuery query and Looker Studio dashboard",
            "**Policy Intelligence \u2192 IAM Recommender** — uses 90-day usage analysis to recommend least-privilege role changes for principals (including service accounts), surfaced in the Console and via API",
            "Cloud Asset Inventory exports + manual triage",
            "Security Command Center misconfiguration findings only"
        ],
        "answer": 1,
        "explanation": "IAM Recommender (part of Policy Intelligence) uses ML on access patterns to suggest least-privilege role changes for principals, surfacing actionable recommendations org-wide. Custom queries reinvent this. Asset Inventory shows state but not 'used what'. SCC findings cover misconfigurations but not least-privilege analysis.\n\n\ud83d\udd0d Targeted Search: 'IAM Recommender least privilege', 'Policy Intelligence Recommender'."
    },
    # 15
    {
        "id": "q115",
        "domain": "Designing & Planning",
        "diff": "challenging",
        "text": "A workload has Microsoft and Oracle BYOL licenses tied to physical CPU sockets, plus an audit requirement that no other tenant's workload may share the same physical host. The team also needs live migration during host maintenance and the ability to scale up/down within Compute Engine. Which is correct?",
        "opts": [
            "Standard Compute Engine VMs with high CPU reservations",
            "**Sole-Tenant Nodes** \u2014 dedicated physical hosts per tenant; supports BYOL socket licensing, live migration during host maintenance, and standard Compute Engine VM lifecycle on top",
            "Bare Metal Solution",
            "Cloud Workstations with custom images"
        ],
        "answer": 1,
        "explanation": "Sole-Tenant Nodes give dedicated physical hosts per tenant with BYOL socket licensing, live migration, and the same VM management as the rest of Compute Engine. Bare Metal Solution is for SAP/Oracle on dedicated bare metal but doesn't run as Compute Engine VMs. Standard CE shares hosts. Cloud Workstations is for IDE environments.\n\n\ud83d\udd0d Targeted Search: 'Compute Engine Sole-Tenant Nodes BYOL', 'Sole-Tenant node group affinity'."
    },
    # 16
    {
        "id": "q116",
        "domain": "Managing Implementation",
        "diff": "hard",
        "text": "An enterprise must run a 20 TB Oracle Exadata workload in Google Cloud with native Oracle features (Real Application Clusters, ASM, Data Guard), unmodified Oracle binaries, and certified database hardware. Which Google Cloud option is correct?",
        "opts": [
            "Cloud SQL for PostgreSQL after migration",
            "**Bare Metal Solution** \u2014 dedicated certified Oracle-grade hardware in a Google Cloud-adjacent data center, low-latency Partner Interconnect to GCP, runs unmodified Oracle including RAC and Data Guard",
            "Compute Engine VMs running Oracle binaries with persistent disks",
            "Anthos clusters on bare metal"
        ],
        "answer": 1,
        "explanation": "Bare Metal Solution is the only Google offering for Oracle-certified bare-metal hardware (RAC/ASM/Data Guard) co-located with GCP via low-latency Interconnect. Cloud SQL/PG isn't Oracle. CE VMs aren't certified for RAC. Anthos on Bare Metal is for K8s, not Oracle.\n\n\ud83d\udd0d Targeted Search: 'Bare Metal Solution Oracle RAC', 'Bare Metal Solution data guard'."
    },
    # 17
    {
        "id": "q117",
        "domain": "Designing & Planning",
        "diff": "challenging",
        "text": "An enterprise builds an internal employee assistant: search across SharePoint, Confluence, ServiceNow, and Drive; conversational follow-ups grounded in those sources; per-user document ACLs preserved end-to-end; and citations in the response. Which Google Cloud product is BEST?",
        "opts": [
            "Vertex AI Vector Search + a custom RAG application",
            "**Vertex AI Agent Builder + Vertex AI Search** \u2014 connectors to SharePoint/Confluence/Drive/etc., document-level ACL propagation to the search results, conversational answer generation with citations",
            "BigQuery ML AI.GENERATE_TEXT with manually loaded documents",
            "Dialogflow CX with webhook to a custom search endpoint"
        ],
        "answer": 1,
        "explanation": "Vertex AI Search (part of Agent Builder) is the managed enterprise search + RAG product with native connectors, ACL propagation, and citation-aware generation. Hand-rolling on Vector Search is more work and you must reimplement ACLs. BQ ML is for SQL-native LLM calls, not document search. Dialogflow CX is a conversation manager but not an enterprise search engine.\n\n\ud83d\udd0d Targeted Search: 'Vertex AI Search enterprise', 'Vertex AI Agent Builder ACL'."
    },
    # 18
    {
        "id": "q118",
        "domain": "Analyzing & Optimizing",
        "diff": "hard",
        "text": "A data team wants to summarize each customer support ticket stored in BigQuery (3M rows) with a Gemini model, returning the result as a new column, scheduled to refresh daily. They want to keep all data in BigQuery, no external pipelines. Which approach is correct?",
        "opts": [
            "Export rows to Cloud Storage, run Vertex AI Batch Prediction, re-import",
            "Use **BigQuery ML's `AI.GENERATE_TEXT`** with a remote model bound to a Vertex AI Gemini endpoint; schedule via a Dataform release; results land in a new column inside BigQuery",
            "Cloud Functions iterating row-by-row calling Gemini",
            "Use Cloud Composer to orchestrate Vertex AI online prediction calls per row"
        ],
        "answer": 1,
        "explanation": "AI.GENERATE_TEXT (and friends) lets you call Vertex AI Gemini models directly from BigQuery SQL via a remote model binding; combined with Dataform scheduling, all data and orchestration stay in the warehouse. The other options move data out unnecessarily or are operationally heavy.\n\n\ud83d\udd0d Targeted Search: 'BigQuery AI.GENERATE_TEXT', 'BigQuery ML remote model Gemini'."
    },
    # 19
    {
        "id": "q119",
        "domain": "Security & Compliance",
        "diff": "challenging",
        "text": "Across 30 GKE clusters, security must enforce: no privileged containers, only images from Artifact Registry, no `latest` tag, mandatory `app` and `team` labels, and a 'block-rather-than-warn' default. Violations must be auditable centrally. Which approach is correct?",
        "opts": [
            "Hand-write admission webhooks per cluster",
            "**Anthos Policy Controller (OPA Gatekeeper)** with a centralized constraint library applied via Config Sync; constraints set to `enforcementAction: deny`; audit results aggregated in Cloud Logging across the fleet",
            "Pod Security Standards (Restricted profile) only",
            "Binary Authorization to block all unsigned images"
        ],
        "answer": 1,
        "explanation": "Policy Controller (OPA Gatekeeper) is the policy enforcement plane for GKE Enterprise, distributed via Config Sync; constraints with enforcementAction=deny block violations and emit audit logs. PSS covers some of these but not labels or registry whitelisting. Binary Authorization complements (image signing) but doesn't enforce labels/privileged-container rules. Custom webhooks per-cluster doesn't scale.\n\n\ud83d\udd0d Targeted Search: 'Anthos Policy Controller Gatekeeper enforcementAction', 'Config Sync constraint template'."
    },
    # 20
    {
        "id": "q120",
        "domain": "Managing Implementation",
        "diff": "hard",
        "text": "A Cloud SQL for PostgreSQL 12 instance must be upgraded in-place to PostgreSQL 15. Requirements: minimal downtime, ability to validate the new version with production-like traffic before cutover, and the option to roll back if regressions are discovered. Which approach is correct?",
        "opts": [
            "Run `pg_upgrade` manually on the primary during a maintenance window",
            "Use Cloud SQL **major version upgrade** for a quick path AND, for de-risking, run **Database Migration Service** to replicate Cloud SQL PG12 \u2192 a new Cloud SQL PG15 instance via logical replication; validate against the new instance, then cut over and decommission the old one",
            "Take a backup, restore into a new instance, no replication",
            "Snapshot the persistent disk and re-import into a new instance"
        ],
        "answer": 1,
        "explanation": "DMS supports homogeneous PostgreSQL major-version upgrades via logical replication \u2014 you keep the old instance running while validating the new one, then cut over with minimal downtime. Direct in-place major upgrade is supported but harder to roll back. Backup-restore loses post-backup writes. Snapshot import doesn't migrate replicated state cleanly across major versions.\n\n\ud83d\udd0d Targeted Search: 'Cloud SQL major version upgrade DMS', 'Database Migration Service PostgreSQL upgrade'."
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
