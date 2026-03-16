from accounts.models import SystemRole

def role_permissions(request):
    """
    Context processor to make user roles easily accessible in templates.
    Used for hiding or showing sidebar navigation links according to role hierarchies.
    """
    if not request.user.is_authenticated:
        return {}

    user_role = getattr(request.user, 'role', None)

    return {
        'is_super_admin': user_role == SystemRole.SUPER_ADMIN,
        'is_org_admin': user_role == SystemRole.ORG_ADMIN,
        'is_level_user': user_role in [
            SystemRole.HO_USER,
            SystemRole.RO_USER,
            SystemRole.PIU_USER,
            SystemRole.PROJECT_USER
        ],
        'SystemRole': SystemRole,
    }
