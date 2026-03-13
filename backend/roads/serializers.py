"""
roads/serializers.py
====================
DRF serializers for the Road resource.

RoadSerializer
  - Full CRUD with read-only display fields.
  - validate_geometry() validates GeoJSON LineString format.

RoadMinimalSerializer
  - Lightweight (id + name) for embedding in other serializers.
"""

from rest_framework import serializers

from .models import Road


class RoadSerializer(serializers.ModelSerializer):
    # ── Read-only display fields ───────────────────────────────────────────
    project_name = serializers.CharField(
        source="project.name",
        read_only=True,
    )
    organization_name = serializers.CharField(
        source="project.organization.name",
        read_only=True,
    )
    road_type_display = serializers.CharField(
        source="get_road_type_display",
        read_only=True,
    )
    has_geometry = serializers.BooleanField(read_only=True)

    class Meta:
        model = Road
        fields = [
            "id",
            "name",
            "project",
            "project_name",
            "organization_name",
            "length",
            "geometry",
            "road_type",
            "road_type_display",
            "has_geometry",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    # ── Field-level validation ─────────────────────────────────────────────

    def validate_length(self, value):
        if value < 0:
            raise serializers.ValidationError("Length must be 0 or greater.")
        return value

    def validate_geometry(self, value):
        """Ensure geometry is a valid GeoJSON LineString dict, if provided."""
        if value is None:
            return value
        if not isinstance(value, dict):
            raise serializers.ValidationError(
                "Geometry must be a GeoJSON object (dict)."
            )
        if value.get("type") != "LineString":
            raise serializers.ValidationError(
                "Only GeoJSON LineString geometries are supported. "
                f"Got type: {value.get('type')!r}."
            )
        coords = value.get("coordinates")
        if not isinstance(coords, list) or len(coords) < 2:
            raise serializers.ValidationError(
                "LineString must have at least 2 coordinate pairs."
            )
        for pair in coords:
            if not (isinstance(pair, (list, tuple)) and len(pair) >= 2):
                raise serializers.ValidationError(
                    "Each coordinate must be a [longitude, latitude] pair."
                )
        return value


class RoadMinimalSerializer(serializers.ModelSerializer):
    """Lightweight serializer for embedding a road reference."""

    class Meta:
        model = Road
        fields = ["id", "name"]
