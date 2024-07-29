import hashlib
import os
import sqlite3
from contextlib import contextmanager
from typing import Any, Dict, List, Optional, Tuple


class DatabaseError(Exception):
    pass


class MutationDatabase:
    def __init__(self, db_path: str = "mutahunter.db"):
        self.db_path = db_path
        self.conn = None
        self.create_tables()

    @contextmanager
    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        try:
            yield conn
        finally:
            conn.close()

    def create_tables(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.executescript(
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
                    mutant_path TEXT,
                    original_code TEXT,
                    mutated_code TEXT,
                    description TEXT,
                    error_msg TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (file_version_id) REFERENCES FileVersions(id)
                );
            """
            )
            conn.commit()

    def get_file_version(self, file_path: str) -> Tuple[int, int, bool]:
        """
        Get or create a file version for the given file path.
        Returns: (file_version_id, source_file_id, is_new_version)
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            with open(file_path, "r") as f:
                content = f.read()
            file_hash = hashlib.md5(content.encode()).hexdigest()
            try:

                # Get or create SourceFile
                cursor.execute(
                    """
                    INSERT OR IGNORE INTO SourceFiles (file_path, last_modified)
                    VALUES (?, ?)
                """,
                    (file_path, os.path.getmtime(file_path)),
                )
                cursor.execute(
                    "SELECT id FROM SourceFiles WHERE file_path = ?", (file_path,)
                )
                source_file_id = cursor.fetchone()[0]

                # Check if FileVersion exists
                cursor.execute(
                    """
                    SELECT id FROM FileVersions 
                    WHERE source_file_id = ? AND version_hash = ?
                """,
                    (source_file_id, file_hash),
                )
                result = cursor.fetchone()

                if result:
                    return result[0], source_file_id, False
                else:
                    # Create new FileVersion
                    cursor.execute(
                        """
                        INSERT INTO FileVersions (source_file_id, version_hash, content)
                        VALUES (?, ?, ?)
                    """,
                        (source_file_id, file_hash, content),
                    )
                    conn.commit()
                    return cursor.lastrowid, source_file_id, True
            except sqlite3.Error as e:
                conn.rollback()
                raise DatabaseError(f"Error processing file version: {str(e)}")

    def add_mutant(self, file_version_id: int, mutant_data: dict):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(
                    """
                    INSERT INTO Mutants (
                        file_version_id, status, type, line_number, 
                        original_code, mutated_code, description, mutant_path, error_msg
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        file_version_id,
                        mutant_data["status"],
                        mutant_data["type"],
                        mutant_data["line_number"],
                        mutant_data["original_code"],
                        mutant_data["mutated_code"],
                        mutant_data["description"],
                        mutant_data.get("mutant_path", ""),
                        mutant_data.get("error_msg", ""),
                    ),
                )
                conn.commit()
            except sqlite3.Error as e:
                conn.rollback()
                raise DatabaseError(f"Error adding mutant: {str(e)}")

    def get_mutants_by_file_version_id(self, file_version_id: int) -> List[Dict]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(
                    "SELECT * FROM Mutants WHERE file_version_id = ?",
                    (file_version_id,),
                )
                data = []
                for row in cursor.fetchall():
                    data.append(
                        {
                            "id": row[0],
                            "file_version_id": row[1],
                            "status": row[2],
                            "type": row[3],
                            "line_number": row[4],
                            "mutant_path": row[5],
                            "original_code": row[6],
                            "mutated_code": row[7],
                            "description": row[8],
                            "error_msg": row[9],
                            "created_at": row[10],
                        }
                    )
                return data
            except sqlite3.Error as e:
                raise DatabaseError(f"Error fetching mutants: {str(e)}")

    def get_mutants(self, file_path: Optional[str] = None) -> list:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                if file_path:
                    cursor.execute(
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
                    cursor.execute(
                        "SELECT * FROM Mutants ORDER BY file_version_id, line_number"
                    )
                data = []
                for row in cursor.fetchall():
                    data.append(
                        {
                            "id": row[0],
                            "file_version_id": row[1],
                            "status": row[2],
                            "type": row[3],
                            "line_number": row[4],
                            "mutant_path": row[5],
                            "original_code": row[6],
                            "mutated_code": row[7],
                            "description": row[8],
                            "error_msg": row[9],
                            "created_at": row[10],
                        }
                    )
                return data
            except sqlite3.Error as e:
                raise DatabaseError(f"Error fetching mutants: {str(e)}")

    def update_mutant_status(self, mutant_id: int, status: str):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(
                    "UPDATE Mutants SET status = ? WHERE id = ?", (status, mutant_id)
                )
                conn.commit()
            except sqlite3.Error as e:
                conn.rollback()
                raise DatabaseError(f"Error updating mutant status: {str(e)}")

    def get_survived_mutants(self, source_file_path):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(
                    """
                    SELECT * FROM Mutants 
                    WHERE file_version_id IN (
                        SELECT id FROM FileVersions WHERE source_file_id = (
                            SELECT id FROM SourceFiles WHERE file_path = ?
                        )
                    ) AND status = 'SURVIVED'
                    ORDER BY line_number
                """,
                    (source_file_path,),
                )
                data = []
                for row in cursor.fetchall():
                    data.append(
                        {
                            "id": row[0],
                            "file_version_id": row[1],
                            "status": row[2],
                            "type": row[3],
                            "line_number": row[4],
                            "mutant_path": row[5],
                            "original_code": row[6],
                            "mutated_code": row[7],
                            "description": row[8],
                            "error_msg": row[9],
                            "created_at": row[10],
                        }
                    )
                return data
            except sqlite3.Error as e:
                raise DatabaseError(f"Error fetching survived mutants: {str(e)}")

    def get_survived_mutants_by_file_version_id(self, file_version_id: int) -> list:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(
                    """
                    SELECT * FROM Mutants 
                    WHERE file_version_id = ? AND status = 'SURVIVED'
                    ORDER BY line_number
                """,
                    (file_version_id,),
                )
                data = []
                for row in cursor.fetchall():
                    data.append(
                        {
                            "id": row[0],
                            "file_version_id": row[1],
                            "status": row[2],
                            "type": row[3],
                            "line_number": row[4],
                            "mutant_path": row[5],
                            "original_code": row[6],
                            "mutated_code": row[7],
                            "description": row[8],
                            "error_msg": row[9],
                            "created_at": row[10],
                        }
                    )
                return data
            except sqlite3.Error as e:
                raise DatabaseError(f"Error fetching survived mutants: {str(e)}")

    def get_file_mutations(self, file_name: str) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(
                    """
                        SELECT m.id, m.status, m.type, m.description, m.line_number, m.original_code, m.mutated_code, m.error_msg
                        FROM Mutants m
                        JOIN FileVersions fv ON m.file_version_id = fv.id
                        JOIN SourceFiles sf ON fv.source_file_id = sf.id
                        WHERE sf.file_path = ?
                        ORDER BY m.line_number
                    """,
                    (file_name,),
                )
                return [
                    {
                        "id": row[0],
                        "status": row[1],
                        "type": row[2],
                        "description": row[3],
                        "line_number": row[4],
                        "original_code": row[5],
                        "mutated_code": row[6],
                        "error_msg": row[7],
                    }
                    for row in cursor.fetchall()
                ]
            except sqlite3.Error as e:
                raise DatabaseError(f"Error fetching file mutations: {str(e)}")

    def get_file_data(self) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(
                    """
                    SELECT 
                        sf.id,
                        sf.file_path,
                        COUNT(m.id) as total_mutants,
                        SUM(CASE WHEN m.status = 'KILLED' THEN 1 ELSE 0 END) as killed_mutants,
                        SUM(CASE WHEN m.status = 'SURVIVED' THEN 1 ELSE 0 END) as survived_mutants
                    FROM SourceFiles sf
                    JOIN FileVersions fv ON sf.id = fv.source_file_id
                    JOIN Mutants m ON fv.id = m.file_version_id
                    GROUP BY sf.file_path
                """
                )
                return [
                    {
                        "id": row[0],
                        "name": row[1],
                        "totalMutants": row[2],
                        "mutationCoverage": (
                            f"{(row[3] / row[2] * 100):.2f}" if row[2] > 0 else "0.00"
                        ),
                        "survivedMutants": row[4],
                    }
                    for row in cursor.fetchall()
                ]
            except sqlite3.Error as e:
                raise DatabaseError(f"Error fetching file data: {str(e)}")

    def get_mutant_summary(self) -> Dict[str, int]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(
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
                result = cursor.fetchone()
                if result[0] == 0:
                    return None
                return {
                    "total_mutants": result[0],
                    "killed_mutants": result[1],
                    "survived_mutants": result[2],
                    "timeout_mutants": result[3],
                    "compile_error_mutants": result[4],
                }
            except sqlite3.Error as e:
                raise DatabaseError(f"Error fetching mutant summary: {str(e)}")

    def remove_mutants_by_file_version_id(self, file_version_id: int):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(
                    "DELETE FROM Mutants WHERE file_version_id = ?", (file_version_id,)
                )
                conn.commit()
            except sqlite3.Error as e:
                conn.rollback()
                raise DatabaseError(f"Error removing mutants: {str(e)}")

    def get_mutation_coverage(self) -> float:
        summary = self.get_mutant_summary()
        if not summary:
            return 0.0
        valid_mutants = (
            summary["total_mutants"]
            - summary["compile_error_mutants"]
            - summary["timeout_mutants"]
        )
        return summary["killed_mutants"] / valid_mutants if valid_mutants > 0 else 0.0

    def get_source_file_by_id(self, source_file_id: int) -> str:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(
                    "SELECT file_path FROM SourceFiles WHERE id = ?", (source_file_id,)
                )
                return cursor.fetchone()[0]
            except sqlite3.Error as e:
                raise DatabaseError(f"Error fetching source file: {str(e)}")
