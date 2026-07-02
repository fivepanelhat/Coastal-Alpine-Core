import math

# Registered cryptographic baselines for authorized edge hardware profiles
VALID_FIRMWARE_HASHES = {
    "ESP32_MANAKAI_SOIL": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",  # pragma: allowlist secret
    "PI5_STING_VISION": "7f83b1657ff1fc53b92c48da1bf5553d684d054611ba4f1f4d9240d8bf1b3a1a",  # pragma: allowlist secret
}

# In-memory rolling telemetry cache to calculate statistical anomalies (sliding window)
HISTORY_WINDOW = {}


def input_guard_check(device_id, payload):
    """
    Executes continuous device posture verification and mathematical telemetry anomaly detection.
    """
    try:
        # 1. Parse Sub-Structures
        posture = payload.get("posture", {})
        telemetry = payload.get("telemetry", {})

        # 2. Cryptographic Posture Check
        expected_hash = VALID_FIRMWARE_HASHES.get(payload.get("device_type"))
        if not expected_hash or posture.get("firmware_hash") != expected_hash:
            print(
                f"[SECOPS ANOMALY] Posture validation failed for {device_id}! Rogue firmware detected."
            )
            return False, "INVALID_POSTURE_HASH"

        # Check for impossible process loops (e.g., critical background security daemon missing)
        if "sec_daemon" not in posture.get("running_processes", []):
            print(f"[SECOPS ANOMALY] Device {device_id} is running in a degraded security posture.")
            return False, "MUTATED_PROCESS_STATE"

        # 3. Telemetry Statistical Anomaly Detection (Z-Score)
        current_val = float(telemetry.get("value", 0))
        if device_id not in HISTORY_WINDOW:
            HISTORY_WINDOW[device_id] = []

        history = HISTORY_WINDOW[device_id]

        if len(history) > 10:
            # Calculate Mean and Standard Deviation over the local window
            mean = sum(history) / len(history)
            variance = sum((x - mean) ** 2 for x in history) / len(history)
            std_dev = math.sqrt(variance)

            # If standard deviation is trivial, skip Z-Score to avoid division by zero
            if std_dev > 0.5:
                z_score = abs(current_val - mean) / std_dev
                # A Z-score greater than 3.5 indicates an extreme statistical outlier
                if z_score > 3.5:
                    print(
                        f"[ALERT] Statistical anomaly flagged on {device_id}. Value: {current_val} (Z-Score: {z_score:.2f})"
                    )
                    return False, "TELEMETRY_OUTLIER"

        # Update sliding window (Keep last 50 readings)
        history.append(current_val)
        if len(history) > 50:
            history.pop(0)

        return True, "VERIFIED"

    except Exception as e:
        print(f"[ERROR] Input guard failed to process incoming packet: {e}")
        return False, "PROCESSING_FAULT"
