"""
portal_core/compliance_exporter.py - Compliance Exporter for AquaGuard Portal.

Exports structured telemetry metrics and actuation histories into council-ready formats (CSV/JSON).
"""

import csv
import logging
from pathlib import Path

from portal_schemas.compliance import ComplianceRecord

logger = logging.getLogger(__name__)


class ComplianceExporter:
    """
    Serializes Pydantic-validated ComplianceRecord models to disk.
    Creates structured JSON audits for raw trace records and appends to a consolidated CSV log.
    CSV format matches horizons / Waikato Permitted Activity guidelines.
    """

    def __init__(self, compliance_dir: str = "./telemetry_data/compliance"):
        self.compliance_dir = Path(compliance_dir)
        self.compliance_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Compliance Exporter active. Directory target: {self.compliance_dir}")

    async def export_record(self, record: ComplianceRecord) -> bool:
        """
        Exports a compliance audit record.
        - Writes a single detailed JSON file for structural verification.
        - Appends a line item to the master CSV audit ledger.
        """
        try:
            # 1. Export JSON Record
            json_filename = (
                f"audit_{record.timestamp.strftime('%Y%m%d_%H%M%S')}_{record.audit_id}.json"
            )
            json_path = self.compliance_dir / json_filename

            if hasattr(record, "model_dump_json"):
                json_data = record.model_dump_json(indent=2)
            else:
                json_data = record.json(indent=2)

            with open(json_path, "w", encoding="utf-8") as f:
                f.write(json_data)

            logger.debug(f"Saved audit JSON record to {json_path.name}")

            # 2. Append to Rolling CSV log matching consent ID
            csv_filename = f"compliance_ledger_{record.consent_id}.csv"
            csv_path = self.compliance_dir / csv_filename

            file_exists = csv_path.exists()

            row = {
                "timestamp": record.timestamp.isoformat(),
                "audit_id": record.audit_id,
                "regional_council": record.regional_council,
                "consent_id": record.consent_id,
                "compliance_status": record.status,
                "actions_executed": "; ".join(record.actions_taken),
                "operator_notes": record.operator_notes or "",
            }

            # Add all metrics dynamically
            key_map = {
                "moisture": "moisture_pct",
                "electrical_conductivity": "EC_dS_m",
                "temperature": "temp_C",
                "nitrogen": "N_mgL",
                "phosphorus": "P_mgL",
                "potassium": "K_mgL",
                "pH": "pH",
                "turbidity": "turbidity_NTU",
                "dissolved_oxygen": "DO_mgL",
                "nitrate": "nitrate_mgL",
            }
            for k, v in record.metrics.items():
                mapped_key = key_map.get(k, k)
                row[f"metric_{mapped_key}"] = v

            headers = list(row.keys())

            with open(csv_path, "a", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=headers)
                if not file_exists:
                    # Write regional council metadata and headers
                    writer.writeheader()
                writer.writerow(row)

            logger.info(f"✓ Compliance Record exported successfully to {csv_filename}")
            return True

        except Exception as e:
            logger.error(f"✗ Failed exporting compliance audit records: {e}")
            return False
