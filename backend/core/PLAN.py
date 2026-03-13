# =============================================================================
# APP: core
# Purpose: Shared abstract base classes and utilities
# =============================================================================
#
# FILES TO CREATE:
#
# core/
# ├── models.py          ← Abstract base models
# │     TimestampedModel   (created_at, updated_at)
# │     UUIDModel          (id = UUIDField primary key)
# │     BaseModel          (TimestampedModel + UUIDModel combined)
# │
# ├── permissions.py     ← Shared DRF permission base classes
# │
# ├── pagination.py      ← Standard PageNumberPagination config
# │     DefaultPagination: page_size=20
# │     LargePagination:   page_size=100
# │
# ├── exceptions.py      ← Custom API exception handlers
# │     HierarchyError, AccessDeniedError
# │
# ├── utils.py           ← Helper functions (no business logic)
# │     make_tree_response()   → converts flat list → nested dict
# │
# └── tests/
#       test_utils.py
# =============================================================================
