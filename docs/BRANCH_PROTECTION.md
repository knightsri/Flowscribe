# Branch Protection Settings

This document outlines the recommended branch protection rules for the Flowscribe repository to ensure code quality and prevent accidental changes to critical branches.

## Overview

Branch protection rules help maintain code quality by requiring code reviews, status checks, and other safeguards before changes can be merged into protected branches.

## Recommended Settings

### Main Branch Protection

Configure the following settings for the `main` (or `master`) branch:

#### General Settings

- **Branch name pattern:** `main` (or `master`)
- **Require a pull request before merging:** ✅ Enabled
  - **Require approvals:** 1 (minimum)
  - **Dismiss stale pull request approvals when new commits are pushed:** ✅ Enabled
  - **Require review from Code Owners:** ⬜ Optional (if CODEOWNERS file exists)

#### Status Checks

- **Require status checks to pass before merging:** ✅ Enabled
  - **Require branches to be up to date before merging:** ✅ Enabled
  - **Status checks that are required:**
    - `ci/lint` - Code linting (pylint, black)
    - `ci/test` - Unit tests
    - `ci/security` - Security scanning (bandit)
    - `ci/integration` - Integration tests (optional)

#### Additional Rules

- **Require conversation resolution before merging:** ✅ Enabled
- **Require signed commits:** ⬜ Optional (recommended for production)
- **Require linear history:** ⬜ Optional (prevents merge commits)
- **Include administrators:** ⬜ Optional (enforce rules on admins too)

#### Restrictions

- **Restrict pushes that create matching branches:** ⬜ Optional
- **Allow force pushes:** ❌ Disabled (IMPORTANT)
- **Allow deletions:** ❌ Disabled (IMPORTANT)

### Development Branch Protection

For development or staging branches, you may use slightly relaxed rules:

- **Branch name pattern:** `develop` or `staging`
- **Require approvals:** 1 (can be same as main)
- **Require status checks:** ✅ Enabled (same checks as main)
- **Allow force pushes:** ❌ Disabled

### Feature Branch Naming

Enforce consistent branch naming conventions:

- **Feature branches:** `feature/*` or `feat/*`
- **Bug fixes:** `bugfix/*` or `fix/*`
- **Hotfixes:** `hotfix/*`
- **Claude AI branches:** `claude/*`

## Setting Up Branch Protection

### Via GitHub Web Interface

1. Navigate to your repository on GitHub
2. Go to **Settings** → **Branches**
3. Click **Add rule** under "Branch protection rules"
4. Enter the branch name pattern (e.g., `main`)
5. Configure the settings as outlined above
6. Click **Create** or **Save changes**

### Via GitHub CLI

You can also configure branch protection using the GitHub CLI:

```bash
# Protect main branch
gh api repos/{owner}/{repo}/branches/main/protection \
  --method PUT \
  --input - <<EOF
{
  "required_status_checks": {
    "strict": true,
    "contexts": ["ci/lint", "ci/test", "ci/security"]
  },
  "enforce_admins": false,
  "required_pull_request_reviews": {
    "dismissal_restrictions": {},
    "dismiss_stale_reviews": true,
    "require_code_owner_reviews": false,
    "required_approving_review_count": 1
  },
  "restrictions": null,
  "allow_force_pushes": false,
  "allow_deletions": false
}
EOF
```

### Via GitHub API

Using curl:

```bash
curl -X PUT \
  -H "Accept: application/vnd.github+json" \
  -H "Authorization: token YOUR_TOKEN" \
  https://api.github.com/repos/{owner}/{repo}/branches/main/protection \
  -d '{
    "required_status_checks": {
      "strict": true,
      "contexts": ["ci/lint", "ci/test", "ci/security"]
    },
    "enforce_admins": false,
    "required_pull_request_reviews": {
      "dismiss_stale_reviews": true,
      "require_code_owner_reviews": false,
      "required_approving_review_count": 1
    },
    "restrictions": null,
    "allow_force_pushes": false,
    "allow_deletions": false
  }'
```

## Status Checks Setup

To enable status checks, you need to set up CI/CD workflows. See `.github/workflows/ci.yml` for the implementation.

Required status checks:

1. **Linting** (`ci/lint`)
   - Runs pylint on all Python files
   - Runs black to check code formatting
   - Exits with non-zero if issues found

2. **Testing** (`ci/test`)
   - Runs pytest with coverage
   - Requires minimum 80% code coverage
   - Exits with non-zero if tests fail

3. **Security** (`ci/security`)
   - Runs bandit security scanner
   - Checks for common security issues
   - Exits with non-zero if high-severity issues found

4. **Integration** (`ci/integration`) - Optional
   - Tests LLM integration with mocked responses
   - Verifies end-to-end workflows
   - Can be optional for faster PR merges

## CODEOWNERS File

Create a `.github/CODEOWNERS` file to automatically request reviews from specific people or teams:

```
# Default owners for everything in the repo
* @your-github-username

# Python scripts
/scripts/*.py @your-github-username

# Docker configuration
/Dockerfile* @your-github-username
/docker-compose.yml @your-github-username

# Documentation
/docs/ @your-github-username

# CI/CD workflows
/.github/ @your-github-username
```

## Best Practices

1. **Always create pull requests** - Never push directly to protected branches
2. **Keep PRs small and focused** - Easier to review and less likely to introduce bugs
3. **Write descriptive PR descriptions** - Explain what changed and why
4. **Respond to review comments** - Address all feedback before merging
5. **Keep branches up to date** - Regularly merge main into your feature branch
6. **Delete merged branches** - Keep repository clean
7. **Use conventional commits** - Follow commit message conventions

## Troubleshooting

### Cannot push to protected branch

**Error:** "You cannot push to this branch because it is protected"

**Solution:** Create a pull request instead of pushing directly

### Status checks not running

**Possible causes:**
- CI/CD workflow file missing or misconfigured
- GitHub Actions disabled in repository settings
- Workflow not triggered for this branch

**Solution:** Check `.github/workflows/` directory and repository settings

### Cannot merge despite passing checks

**Possible causes:**
- Stale approvals (new commits pushed after approval)
- Conversations not resolved
- Branch not up to date with base branch

**Solution:** Get new approval, resolve conversations, or update branch

## References

- [GitHub Branch Protection Documentation](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches)
- [GitHub Status Checks](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/collaborating-on-repositories-with-code-quality-features/about-status-checks)
- [CODEOWNERS File](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners)

## Checklist

Use this checklist to ensure branch protection is properly configured:

- [ ] Main branch protection enabled
- [ ] Pull request reviews required (minimum 1)
- [ ] Status checks configured and required
- [ ] Force pushes disabled
- [ ] Branch deletions disabled
- [ ] Conversation resolution required
- [ ] CI/CD workflows created and working
- [ ] CODEOWNERS file created (optional)
- [ ] Team members aware of branching strategy
- [ ] Documentation updated

---

**Last Updated:** 2025-11-15
**Applies to:** Flowscribe repository
**Maintained by:** Repository administrators
