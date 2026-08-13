// Simple persistent memory matrix tracking command metrics.
// A Map, not a plain object: nodeIds like "__proto__" or "constructor"
// must be ordinary keys, never prototype-pollution vectors.
const commandHistory = new Map();

// Cap on distinct node histories: spoofed nodeIds must not grow this map
// without bound (memory DoS). Oldest entries are evicted FIFO at the cap.
const MAX_TRACKED_NODES = 1024;

/**
 * Assesses the behavioral validity of an actuator command prior to execution.
 * @param {string} nodeId - Target hardware node.
 * @param {string} commandType - Action profile (e.g., "VALVE_OPEN").
 * @returns {boolean} True if command behavior aligns with secure historical metrics.
 */
function analyzeActuatorBehavior(nodeId, commandType) {
    // Fail-closed: actuator commands with malformed identifiers are never
    // "benign by default" on physical infrastructure.
    if (typeof nodeId !== 'string' || !/^[A-Za-z0-9._-]{1,64}$/.test(nodeId)
        || typeof commandType !== 'string' || commandType.length > 64) {
        console.error("[BEHAVIORAL ANOMALY] Malformed nodeId or commandType rejected.");
        return false;
    }

    const now = new Date();
    const currentHour = now.getHours();

    if (!commandHistory.has(nodeId)) {
        if (commandHistory.size >= MAX_TRACKED_NODES) {
            const oldest = commandHistory.keys().next().value;
            commandHistory.delete(oldest);
            console.warn("[SECOPS] Node history cap reached; evicted oldest tracked node.");
        }
        commandHistory.set(nodeId, { lastExecuted: 0, frequencyCounter: 0, trackingHour: currentHour });
    }

    const stats = commandHistory.get(nodeId);
    
    // 1. Velocity Checking (Defend against rapid command flooding)
    const timeDelta = Date.now() - stats.lastExecuted;
    if (timeDelta < 10000) { // Less than 10 seconds since last command execution
        console.error(`[BEHAVIORAL ANOMALY] Malicious velocity signature on node [${nodeId}]. Command spam blocked.`);
        return false;
    }
    
    // 2. Chronological Operational Envelope Boundary Check
    // Critical infrastructure valves should not actuate between 10 PM and 4 AM local time
    if (currentHour >= 22 || currentHour <= 4) {
        if (commandType === "VALVE_OPEN_CRITICAL") {
            console.error(`[BEHAVIORAL ANOMALY] High-risk command [${commandType}] attempted outside operational time boundary (${currentHour}:00).`);
            return false;
        }
    }

    // 3. Cadence Counter Validation
    if (stats.trackingHour !== currentHour) {
        stats.frequencyCounter = 0;
        stats.trackingHour = currentHour;
    }
    stats.frequencyCounter++;
    
    if (stats.frequencyCounter > 12) { // More than 12 structural adjustments per hour is highly atypical
        console.error(`[BEHAVIORAL ANOMALY] Hourly operational threshold exceeded for node [${nodeId}]. Suspending route privileges.`);
        return false;
    }

    // Capture state values for downstream delta analysis
    stats.lastExecuted = Date.now();
    console.log(`[SECURE] Behavioral analytics clear for command [${commandType}] targeting node [${nodeId}].`);
    return true;
}

module.exports = { analyzeActuatorBehavior };
