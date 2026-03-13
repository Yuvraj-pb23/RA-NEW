import uuid

from django.db import models


class UUIDModel(models.Model):
    """
    Abstract base that replaces the default auto-increment integer PK
    with a UUID. UUIDs are:
      - Safe to expose in URLs (no enumeration attacks)
      - Globally unique across tables (useful for event sourcing / merges)
      - PostgreSQL stores them natively as 128-bit values (not strings)
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        db_index=True,
    )

    class Meta:
        abstract = True


class TimestampedModel(models.Model):
    """
    Abstract base that adds created_at and updated_at to every model.
    Both are indexed to allow efficient time-range queries.
    """

    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
    )
    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        abstract = True


class BaseModel(UUIDModel, TimestampedModel):
    """
    Canonical base model for every domain entity in this project.
    Combines:
      - UUID primary key     (UUIDModel)
      - Timestamps           (TimestampedModel)

    All domain models (Organization, OrgUnit, Road, etc.) extend this.
    """

    class Meta:
        abstract = True
