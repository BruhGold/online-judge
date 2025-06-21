from django.db import migrations, connection

# REFERENTIAL_CONSTRAINTS: https://mariadb.com/docs/server/reference/sql-statements/administrative-sql-statements/system-tables/information-schema/information-schema-tables/information-schema-referential_constraints-table
# KEY_COLUMN_USAGE: https://mariadb.com/docs/server/reference/sql-statements/administrative-sql-statements/system-tables/information-schema/information-schema-tables/information-schema-key_column_usage-table
# This SQL get all the FK constraint in dmoj that is restricted
# and return table_name, contraint_name, ref_table, delete_rule

FETCH_RESTRICT_FKS = """
SELECT
    rc.TABLE_NAME AS table_name,
    kcu.COLUMN_NAME as col,
    rc.CONSTRAINT_NAME AS fk,
    rc.REFERENCED_TABLE_NAME as ref_table,
    kcu.REFERENCED_COLUMN_NAME as ref_col,
    rc.UPDATE_RULE AS upd_rule
FROM information_schema.KEY_COLUMN_USAGE AS kcu
JOIN information_schema.REFERENTIAL_CONSTRAINTS AS rc
      USING (CONSTRAINT_SCHEMA, CONSTRAINT_NAME)
WHERE kcu.REFERENCED_TABLE_SCHEMA = 'dmoj'
  AND kcu.REFERENCED_COLUMN_NAME = 'id'
  AND DELETE_RULE = 'RESTRICT';
"""

# Run the previous command to collect all rows
# then DROP and re-ADD the FOREIGN KEY of each row with ON DELETE CASCADE
# old UPDATE_RULE should be retained
def apply_cascade(apps, schema_editor):
    with connection.cursor() as cur:
        cur.execute("SET FOREIGN_KEY_CHECKS = 0")

        cur.execute(FETCH_RESTRICT_FKS)
        for table, col, fk, ref_table, ref_col, upd_rule in cur.fetchall():
            drop_sql = (
                f"ALTER TABLE `{table}` "
                f"DROP FOREIGN KEY `{fk}`;"
            )
            add_sql = (
                f"ALTER TABLE `{table}` "
                f"ADD CONSTRAINT `{fk}` "
                f"FOREIGN KEY ({col}) REFERENCES `{ref_table}` ({ref_col}) "
                f"ON DELETE CASCADE ON UPDATE {upd_rule};"
            )
            cur.execute(drop_sql)
            cur.execute(add_sql)

        cur.execute("SET FOREIGN_KEY_CHECKS = 1")


class Migration(migrations.Migration):

    dependencies = [
        ('judge', '0165_contestfollow'),
    ]

    operations = [
        migrations.RunPython(apply_cascade, reverse_code=migrations.RunPython.noop),
    ]
