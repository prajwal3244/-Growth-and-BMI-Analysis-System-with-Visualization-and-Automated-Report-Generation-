# CI workflow — activation

The GitHub Actions workflow lives here as [`ci.yml`](./ci.yml) instead of
`.github/workflows/ci.yml` because the credential used to push this branch did
not carry GitHub's `workflow` OAuth scope (GitHub blocks pushing workflow files
without it).

**To enable CI** (lint + tests on Python 3.10/3.11/3.12 + Docker build), do either:

1. **GitHub web UI** — open the repo → *Add file* → *Create new file* →
   name it `.github/workflows/ci.yml`, paste the contents of
   [`ci.yml`](./ci.yml), and commit. The web session has the needed scope.

2. **Locally with a workflow-scoped token** —
   ```bash
   mkdir -p .github/workflows
   git mv docs/ci/ci.yml .github/workflows/ci.yml   # or copy
   git commit -m "ci: enable GitHub Actions workflow"
   git push
   ```
   using a Personal Access Token that includes the `workflow` scope.

Once the file is at `.github/workflows/ci.yml`, the CI badge in the root README
turns green on the next push.
