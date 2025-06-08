DO $$ 
DECLARE
    r RECORD;
BEGIN
    -- Disable foreign key constraints
    SET session_replication_role = 'replica';
    
    FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname = 'citydb') 
    LOOP
        EXECUTE 'TRUNCATE TABLE citydb.' || quote_ident(r.tablename) || ' CASCADE';
    END LOOP;
    
    -- Re-enable foreign key constraints
    SET session_replication_role = 'origin';
END $$;
