-- Part of Hibou Suite Professional.
--
-- Neutralize every encrypted blob in the database.
--
-- An encrypted field holds a secret by definition, and a neutralized copy is
-- one that must not be able to act as the original: no live API tokens, no
-- kubeconfigs, no backup keys, no field encryption keyrings. So rather than
-- maintain a list of tables per module -- which silently goes stale the moment
-- someone adds a field -- every encrypted column is discovered and cleared.
--
-- Discovery mirrors find_encryption_columns(): fields declared with ttype
-- 'encryption' (which covers custom blob names such as group_rec_encrypted),
-- plus any column literally named 'rec_encrypted', filtered down to columns
-- that really exist as bytea on a base table.
--
-- Note this cannot remove a single field from a blob: the blob is a Fernet
-- token and the key is not in the database. It is all or nothing per column,
-- which is why nothing that must survive a neutralize should ever share a blob
-- with something that must not.
DO $$
DECLARE
    target record;
BEGIN
    FOR target IN
        SELECT DISTINCT col.table_name AS tbl, col.column_name AS col
          FROM information_schema.columns col
          JOIN information_schema.tables tab
            ON tab.table_schema = col.table_schema
           AND tab.table_name = col.table_name
           AND tab.table_type = 'BASE TABLE'
         WHERE col.table_schema = current_schema()
           AND col.udt_name = 'bytea'
           AND (col.column_name = 'rec_encrypted'
                OR (col.table_name, col.column_name) IN (
                    SELECT replace(m.model, '.', '_'), f.name
                      FROM ir_model_fields f
                      JOIN ir_model m ON m.id = f.model_id
                     WHERE f.ttype = 'encryption'))
    LOOP
        EXECUTE format('UPDATE %I SET %I = NULL WHERE %I IS NOT NULL',
                       target.tbl, target.col, target.col);
        RAISE NOTICE 'Neutralized encrypted column %.%', target.tbl, target.col;
    END LOOP;
END $$;
