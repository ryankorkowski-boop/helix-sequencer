# Source Registry Contract

Status: compliance contract  
Purpose: document permissions and storage boundaries for any source used by Helix quality, benchmark, or heuristic work

## Purpose

The source registry makes Helix audit-friendly. It records what sources were used, what permissions apply, and whether derived metrics may be stored.

This is especially important for showcase-parity work. Public visibility does not automatically mean training, scraping, redistribution, or derived choreography storage is allowed.

## Registry Shape

A source registry entry should follow this shape:

```json
{
  "source_id": "user_rules_001",
  "title": "User-authored sequencing guidelines",
  "source_type": "user_authored_rules",
  "url": null,
  "copyright_status": "user_owned_or_user_authorized",
  "permission_basis": "created_by_user",
  "storage_allowed": true,
  "raw_asset_storage_allowed": true,
  "derived_metrics_allowed": true,
  "training_allowed": false,
  "creator_specific_reproduction_allowed": false,
  "reviewed_by": "project_owner",
  "review_date": "2026-05-07",
  "notes": "General sequencing heuristics authored by the user."
}
```

## Required Fields

- `source_id`: stable unique id
- `title`: human-readable source name
- `source_type`: category listed below
- `url`: public/source URL when applicable, otherwise null
- `copyright_status`: permission summary
- `permission_basis`: why Helix may use it
- `storage_allowed`: whether any source metadata may be stored
- `raw_asset_storage_allowed`: whether raw source files may be stored
- `derived_metrics_allowed`: whether aggregate metrics may be stored
- `training_allowed`: whether model training is allowed
- `creator_specific_reproduction_allowed`: whether direct style/choreography reproduction is allowed
- `reviewed_by`: reviewer name/role
- `review_date`: ISO date
- `notes`: relevant restrictions or caveats

## Source Types

Allowed source type values:

- `user_authored_rules`
- `user_owned_sequence`
- `permissioned_sequence`
- `public_tutorial`
- `public_documentation`
- `licensed_dataset`
- `public_video_reference_only`
- `synthetic_fixture`
- `internal_generated_output`
- `unknown_or_unreviewed`

## Recommended Permission Defaults

| Source Type | Raw Asset Storage | Derived Metrics | Training | Direct Third-Party Reproduction |
| --- | --- | --- | --- | --- |
| `user_authored_rules` | yes | yes | no unless explicitly requested | no |
| `user_owned_sequence` | yes | yes | only if user permits | no unless user permits |
| `permissioned_sequence` | depends on permission | depends on permission | depends on permission | depends on permission |
| `public_tutorial` | no | yes, as manually reviewed heuristics | no | no |
| `public_documentation` | no | yes | no | no |
| `licensed_dataset` | depends on license | depends on license | depends on license | no unless license permits |
| `public_video_reference_only` | no | no raw choreography; high-level notes only | no | no |
| `synthetic_fixture` | yes | yes | yes | n/a |
| `internal_generated_output` | yes | yes | yes | n/a |
| `unknown_or_unreviewed` | no | no | no | no |

## Storage Rules

### Raw Assets

Raw media, sequence files, vendor assets, and screenshots may only be stored if the registry entry permits raw asset storage.

### Derived Metrics

Derived metrics should be aggregate and non-reconstructive. They should not be sufficient to recreate a third-party authored sequence.

Allowed examples:

```json
{
  "style_bucket": "orchestral_climax",
  "median_finale_escalation": 0.82,
  "median_chorus_contrast": 0.64
}
```

Disallowed examples:

```json
{
  "creator": "specific_person",
  "song": "specific_song",
  "frame_12231": {
    "mega_tree": "spiral red clockwise",
    "roofline": "green chase left"
  }
}
```

## Benchmark Manifest Rule

Benchmark manifests may reference public videos as `public_video_reference_only`, but Helix should not download, store, or train on those videos unless the registry entry has explicit permission.

Use them for:

- manual review notes
- source citation
- style bucket taxonomy
- high-level benchmark planning

Do not use them for:

- raw dataset creation
- direct third-party imitation
- frame-by-frame choreography storage

## Review Workflow

Before adding a new source to benchmark or learning work:

1. Add or update registry entry.
2. Verify permission basis.
3. Confirm storage flags.
4. Confirm tests use synthetic, internal, or permitted data.
5. Document any ambiguity in `notes`.

## Example: Public Video Reference Only

```json
{
  "source_id": "public_video_reference_001",
  "title": "Public showcase video used for human observation only",
  "source_type": "public_video_reference_only",
  "url": "https://example.invalid/video",
  "copyright_status": "publicly_viewable_not_licensed_for_training",
  "permission_basis": "human_reference_only",
  "storage_allowed": true,
  "raw_asset_storage_allowed": false,
  "derived_metrics_allowed": false,
  "training_allowed": false,
  "creator_specific_reproduction_allowed": false,
  "reviewed_by": "project_owner",
  "review_date": "2026-05-07",
  "notes": "Do not download, store, train on, or recreate choreography."
}
```

## Example: Synthetic Fixture

```json
{
  "source_id": "synthetic_trace_001",
  "title": "Synthetic showcase metric fixture",
  "source_type": "synthetic_fixture",
  "url": null,
  "copyright_status": "project_generated",
  "permission_basis": "created_for_tests",
  "storage_allowed": true,
  "raw_asset_storage_allowed": true,
  "derived_metrics_allowed": true,
  "training_allowed": true,
  "creator_specific_reproduction_allowed": false,
  "reviewed_by": "project_owner",
  "review_date": "2026-05-07",
  "notes": "Safe for tests and calibration examples."
}
```
