"""
Database views used for alias clustering.
Pure SQL definitions.
"""

def ensure_alias_views(c):
    c.execute("""
        CREATE VIEW IF NOT EXISTS alias_pairs_sha256 AS
        SELECT f1.id file_id, f2.id other_file_id, 'sha256' signal_type, 1.0 strength
        FROM files f1
        JOIN files f2 ON f1.sha256 = f2.sha256 AND f1.id < f2.id
        WHERE f1.sha256 IS NOT NULL
    """)

    c.execute("""
        CREATE VIEW IF NOT EXISTS alias_pairs_fingerprint AS
        SELECT f1.id file_id, f2.id other_file_id, 'fingerprint' signal_type, 0.9 strength
        FROM files f1
        JOIN files f2 ON f1.fingerprint = f2.fingerprint AND f1.id < f2.id
        WHERE f1.fingerprint IS NOT NULL
    """)