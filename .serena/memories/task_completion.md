# Task Completion

Before delivering docs/planning changes:
- Run `git diff --check`.
- Run a targeted `rg` consistency scan for changed architecture terms.
- Run a basic secret-pattern scan over touched docs.
- Commit with a Conventional Commit message and push the branch/main as appropriate.

Before future scaffold/code delivery:
- Add and run project-native `make test`.
- Add and run `make eval` for gold/adversarial questions.
- Verify unsupported claim count is 0 and ACL leak count is 0 for demo fixtures.
- Run browser validation for Streamlit UI when UI exists.
- Update Serena memories only with stable verified facts.