from accounts.models import SystemRole

class RoleQuerySetMixin:
    """
    Mixin for DRF ViewSets to automatically filter querysets based on user's role.
    Assumes models have an `organization` field or a path to it. 
    Models connected to `org_units` also require hierarchical filtering.
    """
    def get_queryset(self):
        user = self.request.user
        qs = super().get_queryset()

        if user.is_anonymous:
            return qs.none()

        # SUPER ADMIN: Sees everything
        if user.role == SystemRole.SUPER_ADMIN:
            return qs

        # If user has an organization, filter inherently
        # ORG ADMIN: filter by organization
        if user.role == SystemRole.ORG_ADMIN:
            return self.filter_for_org_admin(qs, user.organization)

        # LEVEL USERS: filter by their assigned hierarchical units
        return self.filter_for_level_user(qs, user)

    def filter_for_org_admin(self, queryset, organization):
        """
        By default, we assume the model has an `organization` field.
        Subclasses should override if the relation path is different.
        """
        if hasattr(queryset.model, 'organization'):
            return queryset.filter(organization=organization)
        # Fallback if no direct field
        return queryset.none()

    def filter_for_level_user(self, queryset, user):
        """
        Level users must be restricted to their assigned OrgUnit and its descendants.
        This relies on how user is attached. Assuming `UserOrgAccess` or similar setup links user to OrgUnits.
        """
        org_unit_ids = self.get_accessible_org_units(user)
        # Implement the filtering logic assuming the model has an `org_unit` field
        if hasattr(queryset.model, 'org_unit'):
            return queryset.filter(org_unit_id__in=org_unit_ids)
        return queryset.none()

    def get_accessible_org_units(self, user):
        """
        Resolves the IDs of all org units accessible by the given level user.
        E.g., if user is RO_USER assigned to RO_X, they access RO_X + all PIU and Project units under it.
        """
        # Placeholder for tree traversal logic based on user's OrgUnit access mappings
        from access.models import UserOrgAccess
        user_accesses = UserOrgAccess.objects.filter(user=user, is_active=True).select_related('org_unit')
        unit_ids = set()
        for access in user_accesses:
            # Assuming you have a get_descendants() method from MPTT or a custom tree logic
            if hasattr(access.org_unit, 'get_descendants'):
                descendants = access.org_unit.get_descendants(include_self=True).values_list('id', flat=True)
                unit_ids.update(descendants)
            else:
                unit_ids.add(access.org_unit_id)
        return list(unit_ids)
