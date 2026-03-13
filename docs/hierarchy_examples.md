# =============================================================================
# Hierarchy Examples — Road Management Platform
# =============================================================================
#
# Example Org A: Country → HO → RO → PIU → Project → Roads
# ─────────────────────────────────────────────────────────
#
# HierarchyLevel records:
#   order=1  name=HO      parent=NULL
#   order=2  name=RO      parent=HO
#   order=3  name=PIU     parent=RO
#   order=4  name=Project parent=PIU
#
# OrgUnit tree:
#   HO Delhi          (level=HO,  parent=NULL)
#   └─ RO Lucknow     (level=RO,  parent=HO Delhi)
#      ├─ PIU Agra    (level=PIU, parent=RO Lucknow)
#      │  └─ NH-58    (level=Project, parent=PIU Agra)
#      └─ PIU Kanpur  (level=PIU, parent=RO Lucknow)
#         └─ NH-91    (level=Project, parent=PIU Kanpur)
#
# ─────────────────────────────────────────────────────────
# Example Org B: Country → HO → RO → Project → Roads
# ─────────────────────────────────────────────────────────
#
# HierarchyLevel records:
#   order=1  name=HO      parent=NULL
#   order=2  name=RO      parent=HO
#   order=3  name=Project parent=RO
#   (No PIU level)
#
# ─────────────────────────────────────────────────────────
# Example Org C: Country → Project → Roads
# ─────────────────────────────────────────────────────────
#
# HierarchyLevel records:
#   order=1  name=Project parent=NULL
#
# OrgUnit tree:
#   NH-24  (level=Project, parent=NULL)
#   NH-48  (level=Project, parent=NULL)
#
# ─────────────────────────────────────────────────────────
# Access Examples
# ─────────────────────────────────────────────────────────
#
# User A → assigned to RO Lucknow (role=ro_user)
#   → can see: RO Lucknow, PIU Agra, PIU Kanpur, NH-58, NH-91
#   → can see roads: all roads under NH-58, NH-91
#
# User B → assigned to PIU Agra (role=piu_user)
#   → can see: PIU Agra, NH-58
#   → can see roads: only roads under NH-58
#
# User C → assigned to HO Delhi (role=ho_user)
#          AND assigned to NH-24 in Org C (role=project_user)
#   → can see: everything under HO Delhi + only NH-24 roads
#   → Multi-org, multi-unit user example
# =============================================================================
