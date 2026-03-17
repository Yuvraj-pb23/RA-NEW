"""roads/models.py
==================
Defines the Road model.

A Road belongs to a Project (projects.Project) and represents a
single named road segment within that project.

Geometry is stored as a JSONField (GeoJSON LineString) — no PostGIS
required in Phase 1. Upgrade path: swap JSONField for
django.contrib.gis.db.models.GeometryField in Phase 2.
"""

from django.core.validators import MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from core.models import BaseModel
from projects.models import Project


class Road(BaseModel):
    """
    A single road segment belonging to a Project.

    Inherits from BaseModel:
      - id          UUIDField  (primary key, auto-generated)
      - created_at  DateTimeField (auto_now_add)
      - updated_at  DateTimeField (auto_now)
    """

    class RoadTypeChoices(models.TextChoices):
        NATIONAL_HIGHWAY = "NH",  _("National Highway")
        STATE_HIGHWAY    = "SH",  _("State Highway")
        MAJOR_DISTRICT   = "MDR", _("Major District Road")
        OTHER_DISTRICT   = "ODR", _("Other District Road")
        VILLAGE_ROAD     = "VR",  _("Village Road")

    name = models.CharField(
        _("road name"),
        max_length=255,
        help_text=_("e.g. NH-58 Km 0.00-25.00"),
    )
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="roads",
        db_index=True,
        help_text=_("The project this road belongs to."),
    )
    gpx_file = models.FileField(
        _("GPX File"),
        upload_to="gpx/",
        null=True,
        blank=True,
        help_text=_("Upload a GPX file for this road segment."),
    )
    length = models.DecimalField(
        _("length (km)"),
        max_digits=10,
        decimal_places=3,
        default=0,
        validators=[MinValueValidator(0)],
        help_text=_("Road length in kilometres."),
    )
    geometry = models.JSONField(
        _("geometry"),
        null=True,
        blank=True,
        default=None,
        help_text=_(
            "GeoJSON LineString. "
            "Example: {'type': 'LineString', 'coordinates': [[lon, lat], ...]}"
        ),
    )
    road_type = models.CharField(
        _("road type"),
        max_length=10,
        choices=RoadTypeChoices.choices,
        blank=True,
        db_index=True,
    )

    class Meta:
        db_table = "roads_road"
        verbose_name = _("road")
        verbose_name_plural = _("roads")
        ordering = ["project", "name"]
        indexes = [
            models.Index(fields=["project"],   name="idx_road_project"),
            models.Index(fields=["road_type"], name="idx_road_type"),
            models.Index(
                fields=["project", "road_type"],
                name="idx_road_project_type",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.project.name})"

    @property
    def has_geometry(self) -> bool:
        return self.geometry is not None
