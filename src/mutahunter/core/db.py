import sqlite3
import hashlib
import os
from typing import Optional, Tuple, Dict


class MutationDatabase:
    def __init__(self):
        if os.path.exists("mutahunter.db"):
            print("Removing existing database")
            os.remove("mutahunter.db")
        self.conn = sqlite3.connect("mutahunter.db")
        self.cursor = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        self.cursor.executescript(
            """
            CREATE TABLE IF NOT EXISTS SourceFiles (
                id INTEGER PRIMARY KEY,
                file_path TEXT UNIQUE NOT NULL,
                last_modified TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS FileVersions (
                id INTEGER PRIMARY KEY,
                source_file_id INTEGER,
                version_hash TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (source_file_id) REFERENCES SourceFiles(id),
                UNIQUE (source_file_id, version_hash)
            );

            CREATE TABLE IF NOT EXISTS Mutants (
                id INTEGER PRIMARY KEY,
                file_version_id INTEGER,
                status TEXT,
                type TEXT,
                line_number INTEGER,
                original_code TEXT,
                mutated_code TEXT,
                description TEXT,
                error_msg TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (file_version_id) REFERENCES FileVersions(id)
            );
        """
        )
        self.conn.commit()

    def get_file_version(self, file_path: str) -> Tuple[int, int, bool]:
        """
        Get or create a file version for the given file path.
        Returns: (file_version_id, source_file_id, is_new_version)
        """
        with open(file_path, "r") as f:
            content = f.read()
        file_hash = hashlib.md5(content.encode()).hexdigest()

        # Get or create SourceFile
        self.cursor.execute(
            """
            INSERT OR IGNORE INTO SourceFiles (file_path, last_modified)
            VALUES (?, ?)
        """,
            (file_path, os.path.getmtime(file_path)),
        )
        self.cursor.execute(
            "SELECT id FROM SourceFiles WHERE file_path = ?", (file_path,)
        )
        source_file_id = self.cursor.fetchone()[0]

        # Check if FileVersion exists
        self.cursor.execute(
            """
            SELECT id FROM FileVersions 
            WHERE source_file_id = ? AND version_hash = ?
        """,
            (source_file_id, file_hash),
        )
        result = self.cursor.fetchone()

        if result:
            return result[0], source_file_id, False
        else:
            # Create new FileVersion
            self.cursor.execute(
                """
                INSERT INTO FileVersions (source_file_id, version_hash, content)
                VALUES (?, ?, ?)
            """,
                (source_file_id, file_hash, content),
            )
            self.conn.commit()
            return self.cursor.lastrowid, source_file_id, True

    def add_mutant(self, file_version_id: int, mutant_data: dict):
        self.cursor.execute(
            """
            INSERT INTO Mutants (
                file_version_id, status, type, line_number, 
                original_code, mutated_code, description, error_msg
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                file_version_id,
                mutant_data["status"],
                mutant_data["type"],
                mutant_data["line_number"],
                mutant_data["original_code"],
                mutant_data["mutated_code"],
                mutant_data["description"],
                mutant_data.get("error_msg", ""),
            ),
        )
        self.conn.commit()

    def get_mutants(self, file_path: Optional[str] = None) -> list:
        if file_path:
            self.cursor.execute(
                """
                SELECT m.* FROM Mutants m
                JOIN FileVersions fv ON m.file_version_id = fv.id
                JOIN SourceFiles sf ON fv.source_file_id = sf.id
                WHERE sf.file_path = ?
                ORDER BY m.line_number
            """,
                (file_path,),
            )
        else:
            self.cursor.execute(
                "SELECT * FROM Mutants ORDER BY file_version_id, line_number"
            )
        return self.cursor.fetchall()

    def get_mutant_summary(self) -> Dict[str, int]:
        self.cursor.execute(
            """
            SELECT 
                COUNT(*) as total_mutants,
                SUM(CASE WHEN status = 'KILLED' THEN 1 ELSE 0 END) as killed_mutants,
                SUM(CASE WHEN status = 'SURVIVED' THEN 1 ELSE 0 END) as survived_mutants,
                SUM(CASE WHEN status = 'TIMEOUT' THEN 1 ELSE 0 END) as timeout_mutants,
                SUM(CASE WHEN status = 'COMPILE_ERROR' THEN 1 ELSE 0 END) as compile_error_mutants
            FROM Mutants
        """
        )
        result = self.cursor.fetchone()
        return {
            "total_mutants": result[0],
            "killed_mutants": result[1],
            "survived_mutants": result[2],
            "timeout_mutants": result[3],
            "compile_error_mutants": result[4],
        }

    def get_source_file_by_id(self, source_file_id: int) -> str:
        self.cursor.execute(
            "SELECT file_path FROM SourceFiles WHERE id = ?", (source_file_id,)
        )
        return self.cursor.fetchone()[0]

    def close(self):
        self.conn.close()
