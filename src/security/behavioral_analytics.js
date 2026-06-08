// Simple persistent memory matrix tracking command metrics
const commandHistory = {};

/**
 * Assesses the behavioral validity of an actuator command prior to execution.
 * @param {string} nodeId - Target hardware node.
 * @param {string} commandType - Action profile (e.g., "VALVE_OPEN").
 * @returns {boolean} True if command behavior aligns with secure historical metrics.
 */
function analyzeActuatorBehavior(nodeId, commandType) {
    const now = new Date();
    const currentHour = now.getHours();
    
    if (!commandHistory[nodeId]) {
        commandHistory[nodeId] = { lastExecuted: 0, frequencyCounter: 0, trackingHour: currentHour };
    }
    
    const stats = commandHistory[nodeId];
    
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
