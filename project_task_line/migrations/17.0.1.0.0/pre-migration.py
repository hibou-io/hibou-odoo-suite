def migrate(cr, installed_version):
    cr.execute(
        """
        ALTER TABLE project_task_line
        ADD COLUMN IF NOT EXISTS state VARCHAR
        """,
    )
    cr.execute(
        """
        UPDATE project_task_line
        SET state = kanban_state
        WHERE kanban_state IN ('done', 'blocked')
        """,
    )
