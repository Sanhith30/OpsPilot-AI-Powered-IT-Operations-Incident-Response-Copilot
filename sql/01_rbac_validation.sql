-- Read-only RBAC validation. Run against database: opspilot
SELECT role_id, role_name, description FROM core.roles ORDER BY role_id;
SELECT permission_id, permission_code, description FROM core.permissions ORDER BY permission_id;
SELECT r.role_name, p.permission_code FROM core.role_permissions rp JOIN core.roles r ON r.role_id=rp.role_id JOIN core.permissions p ON p.permission_id=rp.permission_id ORDER BY r.role_id,p.permission_code;
SELECT u.user_id,u.full_name,u.email,r.role_name,u.is_active FROM core.users u JOIN core.roles r ON r.role_id=u.role_id ORDER BY u.user_id;
SELECT u.user_id,u.email,p.permission_code FROM core.users u JOIN core.role_permissions rp ON rp.role_id=u.role_id JOIN core.permissions p ON p.permission_id=rp.permission_id ORDER BY u.user_id,p.permission_code;
