from __future__ import annotations

import json
from pathlib import Path

from app.database import Base, import_models
from app.privacy.categories import SECURITY_SECRET_FIELDS
from app.privacy.inventory import personal_data_categories, table_category_map, table_registry

ROOT = Path(__file__).resolve().parents[3]
REPORT = ROOT / "reports" / "privacy" / "personal-data-inventory-audit-task12b.json"


def main() -> int:
    import_models()
    registry = table_registry()
    category_map = table_category_map()
    findings: list[dict[str, str]] = []
    for table in sorted(Base.metadata.tables.values(), key=lambda item: item.name):
        if table.name not in registry:
            findings.append({"category": "unclassified_table", "table": table.name, "message": "Table is absent from registry."})
        if registry.get(table.name) == "personal-user-data" and not category_map.get(table.name):
            findings.append({"category": "personal_table_without_category", "table": table.name, "message": "Personal table has no export/delete category."})
        user_like = [column.name for column in table.columns if column.name.endswith("_user_id") or column.name in {"user_id", "profile_id", "conversation_id"}]
        if user_like and table.name not in registry:
            findings.append({"category": "user_identifier_absent_from_registry", "table": table.name, "message": "User-like identifier found on unregistered table."})

    for category in personal_data_categories():
        if not category.ownership_paths:
            findings.append({"category": "missing_ownership_path", "table": category.key, "message": "Category has no ownership path."})
        if "never" not in category.export_behavior.lower():
            for table_name in category.tables:
                table = Base.metadata.tables.get(table_name)
                if table is None:
                    findings.append({"category": "missing_category_table", "table": table_name, "message": f"{category.key} references an unknown table."})
                    continue
                secret_columns = sorted(SECURITY_SECRET_FIELDS & {column.name for column in table.columns})
                if secret_columns and "exclude" not in category.export_behavior.lower() and "never" not in category.export_behavior.lower():
                    findings.append({"category": "exported_security_field", "table": table_name, "message": "Category export behavior does not exclude security fields."})
        if "delete" not in category.deletion_behavior.lower() and "retain" not in category.deletion_behavior.lower():
            findings.append({"category": "missing_deletion_strategy", "table": category.key, "message": "Category has no deletion strategy."})

    blocking = [finding for finding in findings if finding["category"] != "personal_table_without_category"]
    report = {
        "formatVersion": 1,
        "tableCount": len(Base.metadata.tables),
        "classifiedTableCount": len(registry),
        "personalCategoryCount": len(personal_data_categories()),
        "blockingFindingCount": len(blocking),
        "advisoryFindingCount": len(findings) - len(blocking),
        "findings": findings,
        "secretValuesIncluded": False,
        "rowContentIncluded": False,
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 1 if blocking else 0


if __name__ == "__main__":
    raise SystemExit(main())
