# Product profiles

Snapshot verified on 2026-09-01. Product IDs and service IDs are stable lookup hints, but live name equality wins. Checklist IDs are included only for diagnosis; always fetch the current template and copy current todos/owners.

## Feed

- User aliases: Feed, AfterShip Feed.
- CMDB product: `AfterShip Feed`, `product_id=98`, Jira board `AFD`.
- Important exception: App Center service `prod-af-mcp-server` (`application_id=2323`, CI `1203`, `python-http`) belongs to `AfterShip Feed`, even for Affiliate MCP features.

Preferred normal-release templates:

| Purpose | Exact live name | 2026-09-01 ID |
|---|---|---:|
| Backend-only PO pre-check | `Feed BE PO (BE Only)` | 333 |
| Frontend PO pre-check | `Feed FE PO` | 330 |
| Security pre-check | `Feed Security` | 337 |
| QA pre-check | `Automizely Feed QA Pre-Check` | 378 |
| Backend pre-check | `Feed BE pre-check` | 324 |
| Frontend pre-check | `Feed FE Pre-Check` | 331 |
| Backend post-check | `Feed BE Post-Check  - Simple` | 450 |
| Frontend post-check | `Feed FE Post-Check` | 332 |

Reject the Feed templates whose names say `限紧急发版` for normal releases.

## Affiliate

- User aliases: Affiliate, Affiliates, AfterShip Affiliates.
- CMDB product: `AfterShip Affiliates`, `product_id=152`, Jira board `FEED`.
- Do not confuse it with `Platform Affiliates`, `product_id=144`, whose Release Train mode was `disabled` at verification.

Known release-controlled App Center services (verify live):

| Service | Application ID | Repo | Type |
|---|---:|---|---|
| `prod-af-affiliate` | 1631 | `prod-af-affiliates` | `golang-http` |
| `prod-af-affiliate-java` | 1832 | `prod-af-affiliates-java` | `java-http` |
| `sdks.am-static.com_affiliates-admin` | 1863 | same as service | `frontend` |
| `bff-api.automizely.com_affiliates_admin` | 1864 | same as service | `nodejs-http` |
| `worker-prod-af-affiliate` | 2136 | `worker-prod-af-affiliates` | `worker` |

Preferred normal-release templates:

| Purpose | Exact live name | 2026-09-01 ID |
|---|---|---:|
| PO pre-check | `发布前 Checklist - PO` | 524 |
| Security pre-check | `Security-Pre-Check` | 604 |
| QA pre-check | `发布前 Checklist - QA` | 518 |
| Backend pre-check | `发布前 Checklist - BE` | 522 |
| Frontend pre-check | `发布前 Checklist - FE` | 520 |
| Backend post-check | `发布后 Checklist - BE` | 523 |
| Frontend post-check | `发布后 Checklist - FE` | 521 |

## Listing

- User aliases: Listing, Listings, Product Listing, Product Listings.
- Release Train product: `Platform Products`, `product_id=138`, Jira board `CNT`.
- Resolve the requested service exactly; `Platform Products` also owns non-Listing services, so the product name alone does not authorize adding them.

Known release-controlled Listing services (verify live):

| Service | Application ID | Repo | Type |
|---|---:|---|---|
| `pltf-pd-product-listings` | 1357 | same as service | `golang-http` |
| `worker-pltf-pd-product-listings` | 1400 | same as service | `worker` |

Preferred normal-release templates:

| Purpose | Exact live name | 2026-09-01 ID |
|---|---|---:|
| Backend pre-check | `BE Pre-Check` | 419 |
| QA pre-check | `QA Pre-Check` | 424 |
| Security pre-check | `Security` | 423 |
| Backend-only PO pre-check | `BE PO (BE Only)` | 422 |
| Backend post-check | `BE Post-Check` | 421 |

## Stale profile recovery

Discard a profile hint and resolve from live data when any exact name is missing, an ID echoes a different name, a template is expired/unreviewed, a service is not release-controlled, or the user's service belongs to another product. Do not repair the skill during a release. Finish or stop the release safely, then propose a focused skill update with the newly verified mapping.
