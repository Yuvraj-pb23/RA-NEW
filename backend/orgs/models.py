from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from core.models import BaseModel


# =============================================================================
# Organization
# =============================================================================

class Organization(BaseModel):
    """
    Top-level tenant in the system.

    Each organization is fully isolated:
    - It has its own HierarchyLevel template
    - It has its own OrgUnit tree
    - Users are scoped to org units within an organization

    Examples: NHAI, MoRTH, UP PWD, Bihar PWD
    """

    name = models.CharField(
        _("organization name"),
        max_length=255,
    )
    country = models.CharField(
        _("country"),
        max_length=100,
        default="India",
    )
    description = models.TextField(
        _("description"),
        blank=True,
    )
    is_active = models.BooleanField(
        _("active"),
        default=True,
        db_index=True,
    )

    class Meta:
        db_table = "orgs_organization"
        verbose_name = _("organization")
        verbose_name_plural = _("organizations")
        ordering = ["name"]
        indexes = [
            models.Index(fields=["country"], name="idx_org_country"),
            models.Index(fields=["is_active"], name="idx_org_active"),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["name", "country"],
                name="uq_org_name_country",
            )
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.country})"

    @property
    def root_units(self):
        """Returns top-level OrgUnits (no parent) for this organization."""
        return self.org_units.filter(parent_unit__isnull=True)


# =============================================================================
# HierarchyLevel
# =============================================================================

class HierarchyLevel(BaseModel):
    """
    Defines the TEMPLATE/SCHEMA of an organization's hierarchy.

    This table answers: "What levels does Org A have, in what order?"

    It does NOT store actual units — OrgUnit does.
    Think of HierarchyLevel as the column headers and OrgUnit as the rows.

    Example for Org A (NHAI):
        level_order=1  level_name=HO    parent_level=NULL
        level_order=2  level_name=RO    parent_level=HO
        level_order=3  level_name=PIU   parent_level=RO
        level_order=4  level_name=Project parent_level=PIU

    Example for Org B (UP PWD):
        level_order=1  level_name=HO    parent_level=NULL
        level_order=2  level_name=RO    parent_level=HO
        level_order=3  level_name=Project parent_level=RO

    The parent_level FK allows branching hierarchies (future use).
    """

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="hierarchy_levels",
        db_index=True,
    )
    level_name = models.CharField(
        _("level name"),
        max_length=100,
        help_text=_("Short label, e.g. HO, RO, PIU, Project"),
    )
    level_order = models.PositiveSmallIntegerField(
        _("level order"),
        help_text=_("1 = top of hierarchy, higher number = deeper level"),
    )
    parent_level = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="child_levels",
        db_index=True,
        help_text=_("The level immediately above this one. NULL for root levels."),
    )

    class Meta:
        db_table = "orgs_hierarchylevel"
        verbose_name = _("hierarchy level")
        verbose_name_plural = _("hierarchy levels")
        ordering = ["organization", "level_order"]
        indexes = [
            models.Index(
                fields=["organization", "level_order"],
                name="idx_hlevel_org_order",
            ),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "level_order"],
                name="uq_hlevel_org_order",
            ),
            models.UniqueConstraint(
                fields=["organization", "level_name"],
                name="uq_hlevel_org_name",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.organization.name} — {self.level_name} (order {self.level_order})"

    def clean(self):
        """
        Ensure level_order is consistent within the organization.
        Parent level must have a strictly lower level_order than this level.
        """
        if self.parent_level is not None:
            if self.parent_level.organization_id != self.organization_id:
                raise ValidationError(
                    _("Parent level must belong to the same organization.")
                )
            if self.parent_level.level_order >= self.level_order:
                raise ValidationError(
                    _(
                        "Parent level order (%(parent)s) must be less than "
                        "this level's order (%(current)s)."
                    ),
                    params={
                        "parent": self.parent_level.level_order,
                        "current": self.level_order,
                    },
                )


# =============================================================================
# OrgUnit
# =============================================================================

class OrgUnit(BaseModel):
    """
    A single node in an organization's unit tree.

    This is the CORE of the system — all access control, project assignment,
    and road visibility flows through this tree.

    The tree is stored as an ADJACENCY LIST:
        - Each row stores its direct parent (parent_unit FK)
        - Traversal uses PostgreSQL recursive CTEs (see hierarchy_service.py)
        - This is simpler to write/update than MPTT or Nested Sets
        - Reads are O(depth) but are cached in Redis in production

    Example tree for NHAI:
        HO Delhi          parent=NULL   level=HO
        ├─ RO Lucknow     parent=HO     level=RO
        │   ├─ PIU Agra   parent=RO Lk  level=PIU
        │   └─ PIU Kanpur parent=RO Lk  level=PIU
        └─ RO Mumbai      parent=HO     level=RO
            └─ PIU Pune   parent=RO Mb  level=PIU

    The `metadata` JSONField allows storing extra attributes per unit
    (state code, budget code, etc.) without schema migrations.
    """

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="org_units",
        db_index=True,
    )
    name = models.CharField(
        _("unit name"),
        max_length=255,
        help_text=_("e.g. HO Delhi, RO Lucknow, PIU Agra"),
    )
    level = models.ForeignKey(
        HierarchyLevel,
        on_delete=models.PROTECT,  # PROTECT: prevent deleting a level if units use it
        related_name="org_units",
        db_index=True,
    )
    parent_unit = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,  # Deleting a parent cascades to children
        null=True,
        blank=True,
        related_name="children",
        db_index=True,  # Critical — used in CTE JOIN
        help_text=_("Direct parent unit. NULL means this is a root node."),
    )
    metadata = models.JSONField(
        _("metadata"),
        default=dict,
        blank=True,
        help_text=_(
            "Flexible key-value storage for extra attributes "
            "(budget code, state code, etc.)."
        ),
    )
    is_active = models.BooleanField(
        _("active"),
        default=True,
        db_index=True,
    )

    class Meta:
        db_table = "orgs_orgunit"
        verbose_name = _("org unit")
        verbose_name_plural = _("org units")
        ordering = ["organization", "level__level_order", "name"]
        indexes = [
            # Primary traversal index: used in recursive CTE JOIN
            models.Index(
                fields=["parent_unit"],
                name="idx_orgunit_parent",
            ),
            # Filter by org (most queries are scoped to an org)
            models.Index(
                fields=["organization"],
                name="idx_orgunit_org",
            ),
            # Filter active units under a level
            models.Index(
                fields=["level", "is_active"],
                name="idx_orgunit_level_active",
            ),
            # Composite: all active units in an org
            models.Index(
                fields=["organization", "is_active"],
                name="idx_orgunit_org_active",
            ),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "name"],
                name="uq_orgunit_org_name",
            )
        ]

    def __str__(self) -> str:
        return f"{self.name} [{self.level.level_name}]"

    def clean(self):
        """
        Validates the tree structure:
        1. Unit's level must belong to the same organization as the unit.
        2. Parent unit must belong to the same organization.
        3. Unit's level order must be GREATER than parent's level order
           (i.e., you can only go deeper, not loop back up).
        4. Prevent a unit from being its own parent (direct self-reference).
        """
        # Rule 1: level must belong to same org
        if self.level.organization_id != self.organization_id:
            raise ValidationError(
                _("The hierarchy level must belong to the same organization as this unit.")
            )

        if self.parent_unit is not None:
            # Rule 2: parent must belong to same org
            if self.parent_unit.organization_id != self.organization_id:
                raise ValidationError(
                    _("Parent unit must belong to the same organization.")
                )

            # Rule 3: this unit's level must be deeper than parent's level
            if self.level.level_order <= self.parent_unit.level.level_order:
                raise ValidationError(
                    _(
                        "A unit's level (order %(child)s) must be deeper than "
                        "its parent's level (order %(parent)s)."
                    ),
                    params={
                        "child": self.level.level_order,
                        "parent": self.parent_unit.level.level_order,
                    },
                )

            # Rule 4: prevent direct self-reference
            if self.pk and self.parent_unit_id == self.pk:
                raise ValidationError(_("A unit cannot be its own parent."))

    @property
    def level_name(self) -> str:
        return self.level.level_name

    @property
    def depth(self) -> int:
        """
        Returns depth from root (root = 0).
        Walks up the parent chain. For display only — do not use in bulk queries.
        Use hierarchy_service.get_depth() for bulk/cached computation.
        """
        depth = 0
        node = self
        while node.parent_unit_id is not None:
            depth += 1
            node = node.parent_unit
        return depth

    def get_ancestors(self) -> list:
        """
        Returns ordered list of ancestors from root to direct parent.
        Walks the parent chain iteratively.
        For bulk use, call hierarchy_service.get_ancestors() instead.
        """
        ancestors = []
        node = self
        while node.parent_unit is not None:
            ancestors.insert(0, node.parent_unit)
            node = node.parent_unit
        return ancestors
