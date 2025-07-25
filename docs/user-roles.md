# User Role Management

## Role Hierarchy

The CommonGraph system implements a three-tier user role system:

### 1. Regular User
- **Default role** for all new users
- Can view and interact with content according to system permissions
- Cannot manage other users

### 2. Admin
- **Administrative privileges** including:
  - User management (approve, promote, demote other users)
  - System configuration
  - Content moderation
- **Can be promoted/demoted** by Super Admins
- **Cannot demote Super Admins**

### 3. Super Admin
- **Highest level** of system access
- **Cannot be demoted** by regular Admins
- **Only other Super Admins** can revoke Super Admin status
- Typically reserved for:
  - System founders
  - Technical administrators
  - Key stakeholders who need permanent access

## Permission Matrix

| Action | User | Admin | Super Admin |
|--------|------|-------|-------------|
| View content | ✅ | ✅ | ✅ |
| Manage own profile | ✅ | ✅ | ✅ |
| Approve new users | ❌ | ✅ | ✅ |
| Promote to Admin | ❌ | ✅ | ✅ |
| Demote Admin | ❌ | ✅ | ✅ |
| Manage Super Admin status | ❌ | ❌ | ✅ |
| Demote Super Admin | ❌ | ❌ | ✅ |

## API Endpoints

### User Management
- `GET /users/` - List all users (Admin+ required)
- `PATCH /users/{username}/approve` - Approve user account (Admin+ required)
- `PATCH /users/{username}/promote` - Promote to Admin (Admin+ required)
- `PATCH /users/{username}/demote` - Demote from Admin (Admin+ required, cannot demote Super Admins)
- `PATCH /users/{username}/super-admin` - Toggle Super Admin status (Super Admin only)

### Security Features
- **Super Admins cannot be accidentally demoted** by regular Admins
- **Super Admin status can only be managed** by other Super Admins
- **Automatic Admin privileges** when promoted to Super Admin
- **Protection against lockout** - system should always have at least one Super Admin

## Database Schema

The `user` table includes:
- `username` (Primary Key)
- `is_active` - Account approval status
- `is_admin` - Administrative privileges
- `is_super_admin` - Permanent administrative privileges

## Frontend Implementation

The admin interface provides:
- **Clear visual indicators** for different role levels
- **Checkbox controls** for toggling Admin status
- **Restricted controls** for Super Admin management (only visible to Super Admins)
- **Disabled states** for actions that aren't permitted
- **Responsive design** that works on mobile devices

## Best Practices

1. **Limit Super Admin accounts** - Only grant to trusted, permanent stakeholders
2. **Regular audits** - Periodically review user roles and permissions
3. **Backup Super Admin** - Always maintain at least 2 Super Admin accounts
4. **Clear documentation** - Ensure all team members understand the role hierarchy
5. **Audit logging** - Track all role changes for security and compliance
