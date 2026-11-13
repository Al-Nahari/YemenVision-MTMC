-- Production target: PostgreSQL 16. SQLite is for local development only.
CREATE TABLE cameras (id varchar(64) PRIMARY KEY, zone text, direction text, active boolean NOT NULL DEFAULT true);
CREATE TABLE video_sources (id uuid PRIMARY KEY, camera_id varchar(64) REFERENCES cameras(id), object_uri text NOT NULL, started_at timestamptz, ended_at timestamptz, metadata jsonb NOT NULL DEFAULT '{}');
CREATE TABLE processing_jobs (id uuid PRIMARY KEY, video_source_id uuid REFERENCES video_sources(id), state text NOT NULL, idempotency_key text UNIQUE NOT NULL, created_at timestamptz NOT NULL DEFAULT now(), detail jsonb NOT NULL DEFAULT '{}');
CREATE TABLE detection_events (id varchar(128) PRIMARY KEY, camera_id varchar(64) REFERENCES cameras(id), occurred_at timestamptz NOT NULL, payload jsonb NOT NULL);
CREATE INDEX ix_detection_camera_time ON detection_events(camera_id,occurred_at DESC);
CREATE TABLE tracklets (id uuid PRIMARY KEY, camera_id varchar(64) REFERENCES cameras(id), video_id text NOT NULL, local_track_id bigint NOT NULL, start_time timestamptz NOT NULL, end_time timestamptz NOT NULL, payload jsonb NOT NULL, UNIQUE(camera_id,video_id,local_track_id));
CREATE INDEX ix_tracklets_camera_time ON tracklets(camera_id,start_time DESC);
CREATE TABLE association_events (id uuid PRIMARY KEY, occurred_at timestamptz NOT NULL, state text NOT NULL, payload jsonb NOT NULL);
CREATE TABLE traffic_aggregates (id uuid PRIMARY KEY, camera_id varchar(64) REFERENCES cameras(id), bucket_start timestamptz NOT NULL, granularity text NOT NULL, payload jsonb NOT NULL);
CREATE INDEX ix_traffic_camera_bucket ON traffic_aggregates(camera_id,bucket_start DESC);
CREATE TABLE model_versions (id uuid PRIMARY KEY, stage text NOT NULL, version text NOT NULL, artifact_uri text NOT NULL, metadata_json jsonb NOT NULL, UNIQUE(stage,version));
CREATE TABLE audit_logs (id uuid PRIMARY KEY, occurred_at timestamptz NOT NULL DEFAULT now(), actor text NOT NULL, action text NOT NULL, resource text NOT NULL, detail jsonb NOT NULL);
CREATE INDEX ix_audit_actor_time ON audit_logs(actor,occurred_at DESC);
