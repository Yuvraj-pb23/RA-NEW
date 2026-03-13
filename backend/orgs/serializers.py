from rest_framework import serializers

from .models import Organization, HierarchyLevel, OrgUnit


# =============================================================================
# Organization
# =============================================================================

class OrganizationSerializer(serializers.ModelSerializer):
    """
    Full representation of an Organization.
    Includes computed counts for dashboard stats.
    """

    unit_count    = serializers.IntegerField(read_only=True)
    project_count = serializers.IntegerField(read_only=True)
    road_count    = serializers.IntegerField(read_only=True)

    class Meta:
        model  = Organization
        fields = [
            "id",
            "name",
            "country",
            "description",
            "is_active",
            "unit_count",
            "project_count",
            "road_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class OrganizationMinimalSerializer(serializers.ModelSerializer):
    """Lightweight nested reference — used inside HierarchyLevel and OrgUnit serializers."""

    class Meta:
        model  = Organization
        fields = ["id", "name", "country"]
        read_only_fields = fields


# =============================================================================
# HierarchyLevel
# =============================================================================

class HierarchyLevelSerializer(serializers.ModelSerializer):
    """
    Full representation of a HierarchyLevel.
    `organization_detail` is a read-only nested object.
    `organization` (write) accepts a UUID for create/update.
    """

    organization_detail = OrganizationMinimalSerializer(
        source="organization", read_only=True
    )
    parent_level_name = serializers.CharField(
        source="parent_level.level_name", read_only=True, default=None
    )

    class Meta:
        model  = HierarchyLevel
        fields = [
            "id",
            "organization",
            "organization_detail",
            "level_name",
            "level_order",
            "parent_level",
            "parent_level_name",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "organization_detail",
            "parent_level_name",
            "created_at",
            "updated_at",
        ]

    def validate(self, attrs):
        """
        Delegate cross-field validation to the model's clean() method.
        This ensures consistency whether data arrives via API or admin.
        """
        # Build a temporary instance to run model-level clean()
        instance = self.instance or HierarchyLevel()
        for attr, value in attrs.items():
            setattr(instance, attr, value)
        instance.clean()
        return attrs


# =============================================================================
# OrgUnit
# =============================================================================

class OrgUnitMinimalSerializer(serializers.ModelSerializer):
    """Lightweight nested reference — avoids deep nesting in list endpoints."""

    level_name = serializers.CharField(source="level.level_name", read_only=True)

    class Meta:
        model  = OrgUnit
        fields = ["id", "name", "level_name"]
        read_only_fields = fields


class OrgUnitSerializer(serializers.ModelSerializer):
    """
    Full OrgUnit representation.

    Read fields:
    - `organization_detail` — nested organization object
    - `level_detail`        — nested level object with name and order
    - `parent_unit_detail`  — nested minimal parent unit
    - `level_name`          — shortcut string

    Write fields:
    - `organization`  — UUID FK
    - `level`         — UUID FK
    - `parent_unit`   — UUID FK (nullable)
    """

    organization_detail = OrganizationMinimalSerializer(
        source="organization", read_only=True
    )
    level_detail = HierarchyLevelSerializer(
        source="level", read_only=True
    )
    parent_unit_detail = OrgUnitMinimalSerializer(
        source="parent_unit", read_only=True
    )
    level_name    = serializers.CharField(source="level.level_name", read_only=True)
    children_count = serializers.SerializerMethodField()

    class Meta:
        model  = OrgUnit
        fields = [
            "id",
            "organization",
            "organization_detail",
            "name",
            "level",
            "level_detail",
            "level_name",
            "parent_unit",
            "parent_unit_detail",
            "children_count",
            "metadata",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "organization_detail",
            "level_detail",
            "parent_unit_detail",
            "level_name",
            "children_count",
            "created_at",
            "updated_at",
        ]

    def get_children_count(self, obj) -> int:
        # Uses the `children` related_name defined on the FK
        return obj.children.filter(is_active=True).count()

    def validate(self, attrs):
        instance = self.instance or OrgUnit()
        for attr, value in attrs.items():
            setattr(instance, attr, value)
        instance.clean()
        return attrs


class OrgUnitTreeSerializer(serializers.ModelSerializer):
    """
    Recursive serializer used by the /tree/ endpoint.
    Builds the full nested hierarchy in a single pass.
    Note: Deep trees are assembled in Python, not via recursive DB calls.
    The view fetches ALL units for the org in one query, then nests them.
    """

    level_name    = serializers.CharField(source="level.level_name", read_only=True)
    level_order   = serializers.IntegerField(source="level.level_order", read_only=True)
    children      = serializers.SerializerMethodField()

    class Meta:
        model  = OrgUnit
        fields = [
            "id",
            "name",
            "level",
            "level_name",
            "level_order",
            "parent_unit",
            "children",
            "is_active",
        ]

    def get_children(self, obj):
        # `_children_cache` is populated by the view before serialization
        children = getattr(obj, "_children_cache", [])
        return OrgUnitTreeSerializer(children, many=True).data
