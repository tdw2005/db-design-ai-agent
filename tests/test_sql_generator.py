import unittest
from pathlib import Path

from app.sql_generator import _validate_sql


PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCHEMA_FILE = PROJECT_ROOT / "schema.sql"


class SqlGeneratorValidationTests(unittest.TestCase):
    def test_schema_sql_passes_validation(self) -> None:
        _validate_sql(SCHEMA_FILE.read_text(encoding="utf-8"))

    def test_create_table_requires_if_not_exists(self) -> None:
        sql = """
        CREATE TABLE demo_users (
            id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            PRIMARY KEY (id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """

        with self.assertRaisesRegex(ValueError, "IF NOT EXISTS"):
            _validate_sql(sql)

    def test_rejects_destructive_statements(self) -> None:
        sql = """
        CREATE TABLE IF NOT EXISTS demo_users (
            id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            PRIMARY KEY (id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

        DROP TABLE demo_users;
        """

        with self.assertRaisesRegex(ValueError, "destructive statements"):
            _validate_sql(sql)

    def test_foreign_key_column_must_be_bigint_unsigned(self) -> None:
        sql = """
        CREATE TABLE IF NOT EXISTS parent_entities (
            id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            PRIMARY KEY (id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

        CREATE TABLE IF NOT EXISTS child_entities (
            id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
            parent_id INT NOT NULL,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            PRIMARY KEY (id),
            KEY idx_child_entities_parent_id (parent_id),
            CONSTRAINT fk_child_entities_parent_id FOREIGN KEY (parent_id) REFERENCES parent_entities (id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """

        with self.assertRaisesRegex(ValueError, "BIGINT UNSIGNED"):
            _validate_sql(sql)


if __name__ == "__main__":
    unittest.main()
