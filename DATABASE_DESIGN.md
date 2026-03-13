# Database Design — Road Management Platform

---

## Entity Relationship Overview

```
Organization
    │
    ├── HierarchyLevel (1:N)   ← defines the schema/template of levels
    │       └── self-referential (parent_level_id)
    │
    └── OrgUnit (1:N)          ← actual unit instances
            └── self-referential (parent_unit_id)  ← the TREE
                    │
                    └── Project (1:N)
                                │
                                └── Road (1:N)

User (Django)
    │
    └── UserOrgAccess (1:N)
              ├── OrgUnit (FK)
              └── role (enum)
```

---

## Table Definitions

### 1. `organizations_organization`

| Column       | Type         | Notes                    |
|--------------|--------------|--------------------------|
| id           | UUID (PK)    | primary key              |
| name         | VARCHAR(255) | unique per country       |
| country      | VARCHAR(100) |                          |
| created_at   | TIMESTAMP    | auto                     |
| updated_at   | TIMESTAMP    | auto                     |

---

### 2. `orgs_hierarchylevel`

| Column          | Type         | Notes                                    |
|-----------------|--------------|------------------------------------------|
| id              | UUID (PK)    |                                          |
| organization_id | UUID (FK)    | → organizations_organization             |
| level_name      | VARCHAR(100) | e.g. "HO", "RO", "PIU", "Project"       |
| level_order     | INTEGER      | 1 = top, higher = deeper                 |
| parent_level_id | UUID (FK)    | self-ref → orgs_hierarchylevel (nullable)|

**Constraints:**
- `UNIQUE(organization_id, level_order)`
- `UNIQUE(organization_id, level_name)`

**Purpose:** This table is the *template* — it says "Org A has levels: HO(1) → RO(2) → PIU(3) → Project(4)".

---

### 3. `orgs_orgunit`

| Column          | Type         | Notes                                     |
|-----------------|--------------|-------------------------------------------|
| id              | UUID (PK)    |                                           |
| organization_id | UUID (FK)    | → organizations_organization              |
| name            | VARCHAR(255) | e.g. "RO Lucknow"                         |
| level_id        | UUID (FK)    | → orgs_hierarchylevel                     |
| parent_unit_id  | UUID (FK)    | self-ref → orgs_orgunit (nullable for root)|

**Constraints:**
- `UNIQUE(organization_id, name)`
- A unit's level must belong to same organization as the unit

**This is the CORE of the hierarchy tree.**

```
HO Delhi  (level=HO, parent=NULL)
    ├── RO Lucknow  (level=RO, parent=HO Delhi)
    │       ├── PIU Agra     (level=PIU, parent=RO Lucknow)
    │       └── PIU Kanpur   (level=PIU, parent=RO Lucknow)
    └── RO Mumbai  (level=RO, parent=HO Delhi)
```

---

### 4. `roads_project`

| Column      | Type         | Notes                     |
|-------------|--------------|---------------------------|
| id          | UUID (PK)    |                           |
| name        | VARCHAR(255) |                           |
| org_unit_id | UUID (FK)    | → orgs_orgunit            |
| created_at  | TIMESTAMP    |                           |

---

### 5. `roads_road`

| Column      | Type         | Notes                              |
|-------------|--------------|------------------------------------|
| id          | UUID (PK)    |                                    |
| name        | VARCHAR(255) |                                    |
| project_id  | UUID (FK)    | → roads_project                    |
| length_km   | DECIMAL(10,3)|                                    |
| geometry    | JSONB        | GeoJSON LineString (Phase 1)       |
| created_at  | TIMESTAMP    |                                    |

> **Phase 2 upgrade:** Replace `geometry JSONB` with PostGIS `GeometryField(LineString)`.

---

### 6. `access_userorgaccess`

| Column      | Type        | Notes                              |
|-------------|-------------|------------------------------------|
| id          | UUID (PK)   |                                    |
| user_id     | INT (FK)    | → auth_user                        |
| org_unit_id | UUID (FK)   | → orgs_orgunit                     |
| role        | VARCHAR(50) | ENUM: admin/ho_user/ro_user/...   |
| created_at  | TIMESTAMP   |                                    |

**Constraints:**
- `UNIQUE(user_id, org_unit_id)` — one role per user per unit
- A user CAN have multiple rows (assigned to multiple units)

---

## Hierarchy Traversal Strategy

### Choice: Adjacency List + PostgreSQL Recursive CTE

**Why not MPTT/django-treebeard?**

| Approach           | Pros                         | Cons                               |
|--------------------|------------------------------|------------------------------------|
| MPTT               | Fast reads                   | Expensive inserts, complex updates |
| Closure Table      | Very fast all-ancestors      | O(n²) storage, complex writes      |
| Nested Sets        | Fast subtree reads           | Very expensive inserts             |
| **Adjacency List** | Simple, flexible, native SQL | Requires CTE for traversal         |

**Decision: Adjacency List** because:
1. PostgreSQL natively supports recursive CTEs (`WITH RECURSIVE`)
2. Hierarchy structure changes rarely — write cost is fine
3. Reads are cached in Redis (future)
4. Simpler model code, easier to reason about

### Recursive CTE Pattern (reference, no code)

```sql
-- Get all descendants of a given OrgUnit
WITH RECURSIVE subtree AS (
    SELECT id, name, parent_unit_id, 1 AS depth
    FROM orgs_orgunit
    WHERE id = :root_unit_id        -- anchor

    UNION ALL

    SELECT c.id, c.name, c.parent_unit_id, s.depth + 1
    FROM orgs_orgunit c
    JOIN subtree s ON c.parent_unit_id = s.id  -- recursive step
)
SELECT * FROM subtree;
```

This will be wrapped in `orgs/services/hierarchy_service.py`.

---

## Indexes

| Table              | Index                                     | Purpose                   |
|--------------------|-------------------------------------------|---------------------------|
| orgs_orgunit       | `idx_orgunit_parent` on `parent_unit_id`  | CTE join performance      |
| orgs_orgunit       | `idx_orgunit_org` on `organization_id`    | Filter by org             |
| access_userorgaccess | `idx_access_user` on `user_id`          | Role lookup per user      |
| roads_road         | `idx_road_project` on `project_id`        | Road listing per project  |
| roads_project      | `idx_project_orgunit` on `org_unit_id`    | Projects under a unit     |
