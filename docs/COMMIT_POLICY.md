# Commit Policy

Technical draft - requires operational review before remote enforcement.

Commit format:

```text
type(scope): concise description
```

Allowed types:

```text
feat
fix
docs
test
refactor
security
privacy
ops
ci
build
chore
```

Examples:

```text
ops(staging): add local observability validation
privacy(export): harden archive exclusions
ci(actions): pin workflow actions to immutable SHAs
```

Do not include nonexistent ticket numbers, secrets, personal data or provider object identifiers in commit messages.
