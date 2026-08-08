# Canonical schema 1.1

`chart_data.json` retains the 1.0 top-level fields and adds deterministic audit fields:

```json
{
  "schema_version": "1.1.0",
  "engine": {"name": "six-school-calculator", "version": "1.1.0"},
  "chart_id": "chart_<content hash prefix>",
  "calc_version_hash": "<sha256>",
  "subject": {},
  "calculation_context": {
    "timezone_resolution": {
      "iana_tz": "Asia/Hong_Kong",
      "utc_offset_minutes": 480,
      "dst_applied": false,
      "dst_fold": 0,
      "resolution_method": "iana_tzdata"
    },
    "as_of": null,
    "east_asian_time_basis": {"bazi": "true_solar", "ziwei": "civil"},
    "civil_datetime_local": "2000-01-01 12:00:00",
    "true_solar_datetime_local": "2000-01-01 12:00:00",
    "boundary_warnings": {}
  },
  "system_policy": {
    "core": ["bazi", "ziwei", "western", "vedic"],
    "auxiliary": ["human_design", "numerology"],
    "default_convergence_profile": "core_plus_aux"
  },
  "systems": {
    "bazi": {
      "role": "core",
      "status": "ok",
      "engine": "native-python-bazi",
      "engine_version": "3.1.0",
      "data": {},
      "validation": {"ok": true, "checks": []}
    }
  },
  "validation_summary": {"ok": true, "core_failures": [], "auxiliary_failures": []}
}
```

## Stability rules

- Same normalized input, explicit `as_of`, engine versions, and policies must produce identical canonical JSON.
- Runtime timestamps are not canonical fields.
- Omit volatile transits, current markers, and personal-year data when `as_of` is absent.
- Add fields without renaming existing fields inside schema major version 1.
- Downstream readers must ignore systems whose status is not `ok`.
- Keep raw degrees numeric and source-specific system data opaque.
