# Legacy 256 Permission Notes

Status: placeholder; update before committing any source LMS or derived converted assets.

## Source LMS

- Source owner / permission giver: GP / Greg
- Permission status: user has stated permission exists
- Allowed local inspection: yes, pending detailed written scope
- Allowed repo commit of source LMS: unknown until documented
- Allowed redistribution: unknown until documented
- Allowed derived xLights template commit: unknown until documented

## Safe Default

Keep source LMS and audio local-only:

```text
local_fixtures/legacy_256/source_lms/
local_fixtures/legacy_256/audio/
```

Commit only metadata, tests, tooling, and user-authored manifests unless permission explicitly allows more.

## Required Before Committing Source Assets

Document:

1. filename
2. permission giver
3. date permission was granted
4. allowed uses
5. whether committing to GitHub is allowed
6. whether redistribution is allowed
7. whether converted `.xsq` artifacts may be committed
8. whether derived metrics/reports may be committed
