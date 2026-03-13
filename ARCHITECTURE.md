# Road Management Platform — System Architecture

**Date:** 12 March 2026  
**Stack:** Django · DRF · PostgreSQL · TailwindCSS · Alpine.js

---

## 1. High-Level System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLIENT LAYER                             │
│                                                                 │
│   ┌─────────────────┐        ┌──────────────────────────┐      │
│   │  Admin Dashboard │        │   Field / Public Portal  │      │
│   │  (TailwindCSS   │        │   (Future: Maps + Roads)  │      │
│   │   + Alpine.js)  │        │   (Leaflet / Mapbox)      │      │
│   └────────┬────────┘        └───────────┬──────────────┘      │
└────────────┼─────────────────────────────┼─────────────────────┘
             │ HTTPS                        │ HTTPS
┌────────────┼─────────────────────────────┼─────────────────────┐
│                        API GATEWAY / NGINX                      │
│                   (Static Files + Reverse Proxy)                │
└────────────┼─────────────────────────────┼─────────────────────┘
             │                             │
┌────────────▼─────────────────────────────▼─────────────────────┐
│                    DJANGO APPLICATION LAYER                      │
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │  accounts    │  │  orgs        │  │  roads               │  │
│  │  (Auth/JWT)  │  │  (Hierarchy) │  │  (Projects + Roads)  │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │  access      │  │  dashboard   │  │  api                 │  │
│  │  (RBAC)      │  │  (Templates) │  │  (DRF Router)        │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │               services/  (Business Logic Layer)         │   │
│  │   hierarchy_service.py · access_service.py · ...        │   │
│  └─────────────────────────────────────────────────────────┘   │
└──────────────────────────┬──────────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────────┐
│                      DATA LAYER                                  │
│                                                                 │
│  ┌─────────────────────┐    ┌───────────────────────────────┐  │
│  │   PostgreSQL         │    │   Redis (Cache + Sessions)    │  │
│  │   (Primary DB)       │    │   (Future: Celery Tasks)      │  │
│  └─────────────────────┘    └───────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. Django Applications (Apps) Breakdown

| App          | Responsibility                                            |
|--------------|-----------------------------------------------------------|
| `accounts`   | User model, authentication, JWT, profile                  |
| `orgs`       | Organization, HierarchyLevel, OrgUnit (the tree)         |
| `roads`      | Project, Road, geometry/spatial data                      |
| `access`     | UserOrgAccess, role management, RBAC enforcement         |
| `dashboard`  | Template views for admin UI (non-API HTML pages)         |
| `api`        | Central DRF router, versioning, API schema               |
| `core`       | Shared utilities, base models, pagination, exceptions    |

### Why separate apps?
- **`orgs`** owns the hierarchy tree — all structural data
- **`roads`** owns the domain data — projects and roads
- **`access`** owns who-can-see-what — pure RBAC
- **`dashboard`** is purely UI rendering — no business logic
- **`core`** holds abstract base models (`TimestampedModel`, `UUIDModel`) shared across all apps

---

## 3. Request-Response Flow

### Scenario: RO User fetches roads

```
User (JWT)
   │
   ▼
DRF View → [Permission Class: HasOrgAccess]
   │              │
   │              └── access.services.get_user_org_units(user)
   │                        └── returns: [RO Lucknow]
   │
   ▼
orgs.services.get_descendant_units(org_unit_ids)
   │  (recursive CTE or adjacency-list traversal)
   └── returns: [RO Lucknow, PIU Agra, PIU Kanpur, ...]
   │
   ▼
roads.services.get_roads_for_units(unit_ids)
   └── returns: Roads queryset filtered by project__org_unit__in
   │
   ▼
Serializer → JSON Response
```

---

## 4. Authentication Strategy

```
Login ─► Django Session (Admin Dashboard HTML views)
     ─► JWT Token  (DRF API consumers, future mobile)

Both strategies co-exist.
Admin dashboard uses Django session auth (simpler, secure).
API endpoints use JWT (stateless, scalable).
```

---

## 5. Key Architectural Decisions

| Decision                  | Choice                              | Reason                                      |
|---------------------------|-------------------------------------|---------------------------------------------|
| Hierarchy storage         | Adjacency List + Recursive CTE      | PostgreSQL native support, flexible depth   |
| Role system               | DB-level roles via UserOrgAccess    | Multi-org, multi-role per user              |
| Spatial data              | `geometry` as TextField (phase 1)   | GeoJSON stored as JSON, migrate to PostGIS  |
| Caching                   | Redis (future)                      | Cache hierarchy trees (expensive recursive) |
| API versioning            | URL-based `/api/v1/`                | Easy to maintain and evolve                 |
| Permissions               | DRF custom Permission classes       | Composable, testable                        |
| Admin UI                  | Custom Django templates + Tailwind  | Full control over UI, no 3rd-party admin    |
