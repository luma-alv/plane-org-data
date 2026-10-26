# Data Audit — Plane Hybrid Synthetic Organization

## 1. Scope

Initial availability audit of the public GitHub repository
`makeplane/plane`, used as the source for the Plane hybrid synthetic
organization dataset.

This report records exploratory API observations. It does not claim
that the complete dataset has been extracted or validated.

## 2. Source metadata

- Repository: `https://github.com/makeplane/plane`
- Visibility: public
- License reported by GitHub API: AGPL-3.0
- Default branch observed: `preview`
- Repository size reported by API: 219030 KB
- Reference commit SHA:
  `d9726d5c9615756135f3d6cd512ece8e2dd42902`
- Reference commit date: `2026-10-23T15:33:23Z`

## 3. Observed resource counts

Counts obtained from GitHub Search API during the initial audit:

| Resource | Count |
|---|---:|
| Open issues | 804 |
| Closed issues | 1211 |
| Total issues | 2015 |
| Open pull requests | 346 |
| Closed pull requests | 7476 |
| Total pull requests | 7822 |
| Merged pull requests | 6604 |
| Closed unmerged pull requests | 1218 |

These are API observations at query time. They are not downloaded
record counts. Search results and repository activity may change.

## 4. Representative pull request sample

Sample: pull request #10016.

The following counts were returned by the first page of each endpoint:

| Resource | Records returned |
|---|---:|
| Reviews | 18 |
| Commits | 5 |
| Comments | 21 |

These values describe the sample only. Pagination completeness and
coverage across all pull requests have not yet been evaluated.

## 5. Preliminary findings

- The public repository API is accessible without GitHub CLI.
- Issues and pull requests can be queried separately.
- Pull request metadata and related review, commit, and comment
  endpoints are available.
- The default branch is `preview`; the reference SHA must be recorded
  for reproducibility.
- Repository metadata counts should not be interpreted as issue-only
  counts because the open issue count can include pull requests.
- References between issues, pull requests, and commits must be
  validated before being treated as confirmed relationships.

## 6. Limitations and pending checks

- Record extraction has not been implemented.
- Pagination completeness has not been audited.
- The audit script is implemented, but no live execution result is committed by default.
- API rate limits are recorded only when the audit script is run.
- Issue comment and pull request review coverage across the full
  dataset has not been measured.
- Relationship validity between issues, pull requests, and commits
  has not been systematically checked.
- Documentation and release coverage remain pending.
- Snapshot start and end timestamps are recorded in each generated JSON manifest.

## 7. Next steps

1. Run the read-only API audit script and retain its timestamped manifest.
2. Review extraction timestamps, reference SHA, API responses,
   pagination status, errors, and rate-limit observations.
3. Measure resource coverage and missing fields on bounded samples.
4. Define normalized schemas while preserving raw API responses.
5. Implement ingestion only after audit requirements are established.
