-- This migration only runs AFTER tables are created by SQLAlchemy
-- It's a safety check, not initial setup. Skip if tables don't exist.

DO $$
BEGIN
    -- Only run if transactions table exists
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'transactions') THEN
        -- Remove any duplicates (keeping the first occurrence)
        DELETE FROM transactions t1
        USING transactions t2
        WHERE t1.id > t2.id
        AND t1.blaze_trans_id = t2.blaze_trans_id
        AND t1.blaze_trans_id IS NOT NULL;

        -- Add unique constraint if it doesn't exist
        IF NOT EXISTS (
            SELECT 1 FROM pg_constraint
            WHERE conname = 'uq_transactions_blaze_trans_id'
        ) THEN
            BEGIN
                ALTER TABLE transactions
                ADD CONSTRAINT uq_transactions_blaze_trans_id UNIQUE (blaze_trans_id);
                RAISE NOTICE 'Added unique constraint on blaze_trans_id';
            EXCEPTION WHEN duplicate_object THEN
                RAISE NOTICE 'Constraint already exists';
            END;
        END IF;

        RAISE NOTICE 'Migration complete';
    ELSE
        RAISE NOTICE 'Tables not yet created, skipping migration';
    END IF;
END $$;
