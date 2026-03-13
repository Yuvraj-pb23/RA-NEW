"""
road_service.py
===============
Data access helpers for the Road resource.
All queries are scoped to the new roads.Road -> projects.Project -> orgs.Organization chain.
"""
from __future__ import annotations

from django.db.models import Count, QuerySet, Sum

from roads.models import Road


def get_roads_for_project(project_id) -> QuerySet:
    """Returns all roads belonging to the given project."""
    return (
        Road.objects
        .filter(project_id=project_id)
        .select_related("project", "project__organization")
    )


def get_roads_for_organization(organization_id) -> QuerySet:
    """Returns all roads belonging to any project in the given organization."""
    return (
        Road.objects
        .filter(project__organization_id=organization_id)
        .select_related("project", "project__organization")
    )


def get_road_statistics(organization_id=None) -> dict:
    """
    Returns aggregate road statistics.
    If organization_id is provided, scopes to that organization.
    """
    qs = Road.objects.all()
    if organization_id:
        qs = qs.filter(project__organization_id=organization_id)

    totals = qs.aggregate(
        total_roads=Count("id"),
        total_length=Sum("length"),
    )

    type_rows = (
        qs.values("road_type")
        .annotate(count=Count("id"), length=Sum("length"))
        .order_by("road_type")
    )

    return {
        "total_roads":     totals["total_roads"] or 0,
        "total_length_km": float(totals["total_length"] or 0),
        "roads_by_type":   list(type_rows),
    }
