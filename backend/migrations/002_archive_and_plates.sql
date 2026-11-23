-- Additive migration for databases created with 001_initial.sql.
ALTER TABLE cameras ADD COLUMN IF NOT EXISTS stream_url text;
ALTER TABLE detection_events ADD COLUMN IF NOT EXISTS plate_text varchar(64);
CREATE INDEX IF NOT EXISTS ix_detection_plate ON detection_events(plate_text);

CREATE TABLE IF NOT EXISTS processed_videos (
    id varchar(64) PRIMARY KEY,
    file_name text UNIQUE NOT NULL,
    original_name text NOT NULL,
    video_id text NOT NULL,
    camera_id varchar(64) REFERENCES cameras(id) ON DELETE SET NULL,
    created_at timestamptz NOT NULL,
    frames_processed integer NOT NULL DEFAULT 0,
    duration_seconds double precision NOT NULL DEFAULT 0,
    file_size bigint NOT NULL DEFAULT 0,
    model_version text,
    plate_count integer NOT NULL DEFAULT 0,
    source text NOT NULL DEFAULT 'upload'
);
CREATE INDEX IF NOT EXISTS ix_video_camera_created ON processed_videos(camera_id,created_at DESC);
CREATE INDEX IF NOT EXISTS ix_video_id ON processed_videos(video_id);
