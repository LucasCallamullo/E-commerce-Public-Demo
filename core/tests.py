
# Create your tests here.
from django.test import TestCase
from django.db import connection

class PgTrgmTest(TestCase):
    """
    Test to ensure that the PostgreSQL pg_trgm extension is enabled and working.

    Important notes:
    1. The pg_trgm extension is required for trigram-based similarity searches
       (e.g., using the similarity() function for fuzzy search).
    2. There is a migration file in `core/migrations/002_enable_pg_trgm.py`:
       this migration runs `CREATE EXTENSION IF NOT EXISTS pg_trgm;` to enable
       the extension in the database.
    3. This test verifies that similarity calculations work, which is critical
       for features like prefix/fuzzy search and SearchRank combinations.
    """

    def test_pg_trgm_enabled(self):
        # Open a raw SQL cursor
        with connection.cursor() as cursor:
            # Execute a simple similarity check
            cursor.execute("SELECT similarity('redragon', 'redra');")
            result = cursor.fetchone()[0]

        # Assert that similarity returned a value
        self.assertIsNotNone(result)

        # Assert that the similarity is greater than zero (indicating a match)
        self.assertGreater(result, 0)
