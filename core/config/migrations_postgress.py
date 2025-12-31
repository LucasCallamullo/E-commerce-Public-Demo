
"""
from django.db import migrations

class Migration(migrations.Migration):
    
    Migration to enable the PostgreSQL pg_trgm extension.

    Context / History:
    1. Initially, the 'core' app only had 0001_initial.py as its first migration.
    2. To enable trigram-based similarity searches (used for fuzzy search),
       we need the 'pg_trgm' extension in PostgreSQL.
    3. Two empty migrations were initially created with:
           python manage.py makemigrations --empty core
       This was done to prepare a place to add custom SQL operations.
    4. This migration (0002_enable_pg_trgm.py) runs the SQL command to
       create the extension if it doesn't exist:
           CREATE EXTENSION IF NOT EXISTS pg_trgm;
    5. Once applied, functions like similarity(), word_similarity(), and
       trigram indexes can be used in the database.

    This migration is required for features that rely on fuzzy search,
    prefix search, or trigram similarity in the 'Product' model.
    

    dependencies = [
        ('core', '0001_initial'),  # the last migration of the core app
    ]

    operations = [
        migrations.RunSQL(
            "CREATE EXTENSION IF NOT EXISTS pg_trgm;"
        ),
    ]
    
    
    
"""


