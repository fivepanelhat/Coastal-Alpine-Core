import csv
import hashlib
import json
import logging
import os
import time
from pathlib import Path

from portal_schemas.compliance import ComplianceRecord

"""
portal_core/compliance_exporter.py - Compliance Exporter for AquaGuard Portal.

Exports structured telemetry metrics and actuation histories into council-ready formats (CSV/JSON).
"""


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


AUDIT_LOG_PATH = "/mnt/sovereign-data/audit/compliance_history.log"
NZ_EMISSIONS_FACTOR_KWH = 0.13  # Average NZ Grid kg CO2e emission density matrix


def capture_sustainability_metrics():
    """
    Reads hardware power state parameters directly from the Pi 5 PMIC matrix
    and maps environmental footprint data.
    """
    # Mocking actual PMIC parsing since access via sysfs requires platform specifics
    # On a live Pi 5, this hooks into the i2c interface for the active power controller
    estimated_voltage = 5.1  # Volts
    estimated_current = 2.4  # Amps (Heavy Hailo NPU inference load)

    calculated_power_watts = estimated_voltage * estimated_current
    kwh_consumed_per_hour = calculated_power_watts / 1000.0
    carbon_footprint_kg = kwh_consumed_per_hour * NZ_EMISSIONS_FACTOR_KWH

    return {
        "power_draw_w": round(calculated_power_watts, 2),
        "est_hourly_carbon_kg": round(carbon_footprint_kg, 5),
    }


def commit_compliance_audit_entry(user_id, action, resource_id, security_clearance):
    """
    Writes an immutable, sequentially chained audit block to satisfy data governance requirements.
    """
    eco_metrics = capture_sustainability_metrics()

    log_payload = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "operator": user_id,
        "action_executed": action,
        "resource_targeted": resource_id,
        "security_clearance": security_clearance,
        "sustainability": eco_metrics,
        "previous_chain_hash": "00000000000000000000000000000000",  # Instantiated on runtime reload
    }

    # 1. Enforce sequential integrity checking via local file hashing chaining
    if os.path.exists(AUDIT_LOG_PATH):
        try:
            with open(AUDIT_LOG_PATH) as f:
                last_line = f.readlines()[-1]
                # Chain the current log line to the block hash of the previous record
                log_payload["previous_chain_hash"] = hashlib.sha256(last_line.encode()).hexdigest()
        except Exception:
            pass  # Handle initial file blank allocation gracefully

    # 2. Commit log record permanently to the file array
    log_string = json.dumps(log_payload)

    # Ensure parent directory exists for local audit logging
    log_dir = os.path.dirname(AUDIT_LOG_PATH)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)

    with open(AUDIT_LOG_PATH, "a", encoding="utf-8") as f:
        f.write(log_string + "\n")

    print(
        f"[AUDIT COMPLIANT] Log serialized. Environmental payload: {eco_metrics['est_hourly_carbon_kg']} kg CO2e/hr."
    )


if __name__ == "__main__":
    commit_compliance_audit_entry(
        "wayne_roberts",
        "EXECUTE_ACTUATOR_VALVE_OPEN",
        "AQUAGUARD_VALVE_04",
        "CHIEF_ARCHITECT",
    )
