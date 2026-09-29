import sys; sys.path.insert(0, '.')
from app.db.session import engine
from sqlalchemy import text

with engine.connect() as conn:
    users = conn.execute(text("SELECT u.user_id, u.email, u.role_id, r.role_name FROM core.users u JOIN core.roles r ON r.role_id = u.role_id")).fetchall()
    for u in users:
        print(u)
    perms = conn.execute(text("SELECT p.permission_code FROM core.role_permissions rp JOIN core.permissions p ON p.permission_id = rp.permission_id WHERE rp.role_id = 1")).fetchall()
    print("Role 1 perms:", [p[0] for p in perms])
