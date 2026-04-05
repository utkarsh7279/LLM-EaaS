-- LLM EaaS database schema
-- Note: primary keys are provided by the application layer (uuid4),
-- so this schema does not require DB extensions for UUID generation.

CREATE TABLE IF NOT EXISTS experiments (
    id UUID PRIMARY KEY,
    name TEXT,
    description TEXT,
    status TEXT NOT NULL DEFAULT 'created',
    is_baseline BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS evaluation_items (
    id UUID PRIMARY KEY,
    experiment_id UUID NOT NULL REFERENCES experiments(id) ON DELETE CASCADE,
    prompt TEXT NOT NULL,
    model_output TEXT NOT NULL,
    reference_output TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS evaluation_results (
    id UUID PRIMARY KEY,
    experiment_id UUID NOT NULL REFERENCES experiments(id) ON DELETE CASCADE,
    item_id UUID NOT NULL REFERENCES evaluation_items(id) ON DELETE CASCADE,
    rubric_scores JSONB NOT NULL,
    overall_score DOUBLE PRECISION NOT NULL,
    reasoning TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS experiment_metrics (
    id UUID PRIMARY KEY,
    experiment_id UUID NOT NULL UNIQUE REFERENCES experiments(id) ON DELETE CASCADE,
    mean_score DOUBLE PRECISION NOT NULL,
    safety_fail_rate DOUBLE PRECISION NOT NULL,
    std_dev DOUBLE PRECISION NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_evaluation_items_experiment_id
    ON evaluation_items (experiment_id);

CREATE INDEX IF NOT EXISTS idx_evaluation_results_experiment_id
    ON evaluation_results (experiment_id);

CREATE INDEX IF NOT EXISTS idx_evaluation_results_item_id
    ON evaluation_results (item_id);

CREATE INDEX IF NOT EXISTS idx_experiment_metrics_experiment_id
    ON experiment_metrics (experiment_id);

CREATE INDEX IF NOT EXISTS idx_experiments_is_baseline
    ON experiments (is_baseline);
