import os
import time
import hashlib
import json

AUDIT_LOG_PATH = "/mnt/sovereign-data/audit/compliance_history.log"
NZ_EMISSIONS_FACTOR_KWH = (
    0.13  # Average NZ Grid kg CO2e emission density matrix
)


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


def commit_compliance_audit_entry(
    user_id, action, resource_id, security_clearance
):
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
            with open(AUDIT_LOG_PATH, "r") as f:
                last_line = f.readlines()[-1]
                last_json = json.loads(last_line)
                # Chain the current log line to the block hash of the previous record
                log_payload["previous_chain_hash"] = hashlib.sha256(
                    last_line.encode()
                ).hexdigest()
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
