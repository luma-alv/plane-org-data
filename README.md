# plane-org-data
Extraction, storage, cleaning, and validation of public information from Plane to build the hybrid synthetic organization.

## Initial GitHub audit

The audit is a read-only, bounded inspection of the public GitHub API for `makeplane/plane` on the `preview` branch. It queries repository metadata, the observed branch/SHA, separate issue and pull-request search counts, and a sample of pull request `#10016` (reviews, commits, and comments). It does not download the full repository history or all artifact relationships.

Run it from the repository root:

```bash
python3 -m unittest discover -s tests
python3 -m src.validation.github_audit
```

The module name is `github_audit`; for example, use:

```bash
python3 -m src.validation.github_audit
```

The script writes a timestamped JSON manifest such as
`data/interim/github_audit_20261026T033424Z.json` and never overwrites an existing manifest. Each manifest includes:

- audit start/end timestamps and the read-only flag;
- repository, branch, and observed reference commit data;
- separate issue and pull-request counts;
- bounded sample results and pagination status;
- rate-limit headers, errors, and known limitations.

Set `GITHUB_TOKEN` only in the environment when authenticated API limits are needed; no token is stored by the project:

```bash
GITHUB_TOKEN="$GITHUB_TOKEN" python3 -m src.validation.github_audit
```

If the environment cannot reach `api.github.com`, the script still writes a manifest containing the timestamps and connection errors, and exits with a non-zero status. Such a manifest must not be interpreted as a completed API audit.

The historical observations documented in [`reports/data_audit.md`](reports/data_audit.md) are kept separate from downloaded records and from each generated manifest. Counts can change as GitHub changes.
