CREATE TABLE IF NOT EXISTS project (
  uid TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  description TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS script (
  uid TEXT PRIMARY KEY,
  project_uid TEXT NOT NULL,
  name TEXT NOT NULL,
  content TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS script_project_uid_idx ON script (project_uid);

CREATE TABLE IF NOT EXISTS normalized_script (
  uid TEXT PRIMARY KEY,
  script_uid TEXT NOT NULL,
  version TEXT,
  content_json JSONB NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS normalized_script_script_uid_idx ON normalized_script (script_uid);

CREATE TABLE IF NOT EXISTS extraction_run (
  uid TEXT PRIMARY KEY,
  project_uid TEXT NOT NULL,
  script_uid TEXT NOT NULL,
  step INTEGER NOT NULL,
  status TEXT,
  model_config JSONB,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  finished_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS extraction_run_project_uid_idx ON extraction_run (project_uid);
CREATE INDEX IF NOT EXISTS extraction_run_script_uid_idx ON extraction_run (script_uid);

CREATE TABLE IF NOT EXISTS artifact_snapshot (
  uid TEXT PRIMARY KEY,
  run_uid TEXT NOT NULL,
  content_json JSONB NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS artifact_snapshot_run_uid_idx ON artifact_snapshot (run_uid);

CREATE TABLE IF NOT EXISTS candidate_entity (
  uid TEXT PRIMARY KEY,
  run_uid TEXT NOT NULL,
  raw_name TEXT NOT NULL,
  entity_type TEXT NOT NULL,
  confidence DOUBLE PRECISION,
  canonical_asset_uid TEXT,
  is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS candidate_entity_run_uid_idx ON candidate_entity (run_uid);
CREATE INDEX IF NOT EXISTS candidate_entity_canonical_asset_uid_idx ON candidate_entity (canonical_asset_uid);

CREATE TABLE IF NOT EXISTS candidate_evidence (
  uid TEXT PRIMARY KEY,
  candidate_uid TEXT NOT NULL,
  line_id TEXT NOT NULL,
  quote TEXT NOT NULL,
  reason TEXT,
  is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS candidate_evidence_candidate_uid_idx ON candidate_evidence (candidate_uid);

CREATE TABLE IF NOT EXISTS canonical_asset (
  uid TEXT PRIMARY KEY,
  project_uid TEXT NOT NULL,
  run_uid TEXT,
  name TEXT NOT NULL,
  type TEXT NOT NULL,
  aliases JSONB,
  description TEXT,
  status TEXT NOT NULL,
  is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS canonical_asset_project_uid_type_idx ON canonical_asset (project_uid, type);
CREATE INDEX IF NOT EXISTS canonical_asset_run_uid_idx ON canonical_asset (run_uid);
