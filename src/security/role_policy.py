from __future__ import annotations


class RolePolicy:
    ALL_PAGES = frozenset({
        "Dashboard",
        "Master Import",
        "User Management",
        "Product",
        "Machine",
        "Employee",
        "Routing",
        "Work Order",
        "CNC",
        "Robot",
        "Inventory",
        "Machine Utilization Report",
        "Production Inventory Reconciliation",
        "Production",
        "Production Assignment",
        "Production Execution",
        "Production Downtime",
        "Production NG",
        "OEE Dashboard",
    })

    ROLE_PAGES = {
        "ADMIN": ALL_PAGES,
        "WAREHOUSE": frozenset({
            "Dashboard",
            "Inventory",
            "Production Inventory Reconciliation",
            "Machine Utilization Report",
            "OEE Dashboard",
        }),
        "PRODUCTION": frozenset({
            "Dashboard",
            "Product",
            "Machine",
            "Employee",
            "Routing",
            "Work Order",
            "CNC",
            "Robot",
            "Production",
            "Production Assignment",
            "Production Execution",
            "Production Downtime",
            "Production NG",
            "Machine Utilization Report",
            "Production Inventory Reconciliation",
            "OEE Dashboard",
        }),
        "VIEWER": frozenset({
            "Dashboard",
            "Machine Utilization Report",
            "Production Inventory Reconciliation",
            "OEE Dashboard",
        }),
    }

    @classmethod
    def allowed_pages_for(cls, user):
        if user is None:
            return cls.ALL_PAGES
        role = str(
            getattr(user, "role", "") or ""
        ).strip().upper()
        return cls.ROLE_PAGES.get(
            role,
            cls.ROLE_PAGES["VIEWER"],
        )

    @classmethod
    def can_access(cls, user, page_name) -> bool:
        return str(page_name or "").strip() in (
            cls.allowed_pages_for(user)
        )
