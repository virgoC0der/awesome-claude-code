Create a GitHub pull request to the upstream branch: $ARGUMENTS

1. Use `gh pr create` with the template from `.github/pull_request_template.md`

2. Set target branch to `$ARGUMENTS` (default to `master` if empty, if `master` does not exist, try `main`)

3. If current branch matches pattern "AFD-*" and targe branch is `master`, prefix PR title with "[AFD-xxxx]"

4. If the target branch is not `master` or `canary`, prefix PR title with "[CI]"

4. For "目的或是相关联的 Jira tickets" section, generate Jira link: https://aftership.atlassian.net/browse/AFD-xxxx
