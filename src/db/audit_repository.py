import sqlite3
from datetime import datetime
from .database import DB_FILE

def log_audit_event(user_id, action_type, details=None):
    now = datetime.now().isoformat()
    try:
        con = sqlite3.connect(DB_FILE)
        cur = con.cursor()
        cur.execute("INSERT INTO audit_logs (timestamp, user_id, action_type, details) VALUES (?, ?, ?, ?)",
                    (now, user_id, action_type, details))
        con.commit()
        con.close()
    except sqlite3.Error as e: print(f"Falha ao registrar evento de auditoria: {e}")