from backend.database import db, AuditLog

def log_action(action_text):
    log = AuditLog(action=action_text)
    db.session.add(log)
    db.session.commit()