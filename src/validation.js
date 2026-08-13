// Coastal-Alpine-Core/src/validation.js

/**
 * Safely parses and validates incoming data payloads without crashing the node process.
 * Designed to handle chaos engineering and malicious injection vectors gracefully.
 * * @param {string} rawPayload - The raw JSON string intercepted from the edge network.
 * @returns {Object|null} Validated data packet, or null if execution was hazardous.
 */
function safeParseTelemetry(rawPayload) {
    try {
        if (!rawPayload || typeof rawPayload !== 'string') {
            console.warn("[SECOPS WARNING] Blank or non-string payload rejected.");
            return null;
        }

        // 1. Defend the JSON parse boundary
        const parsedData = JSON.parse(rawPayload);

        // 2. Structural Integrity Guard Rails (Schema verification)
        if (!parsedData.nodeId || typeof parsedData.nodeId !== 'string') {
            console.warn("[VALIDATION FAILED] Packet dropped: Missing structural identifier 'nodeId'.");
            return null;
        }

        // nodeId is echoed into logs and stored in the local DB: constrain it
        // to a strict allowlist so a hostile packet can't inject log lines
        // (newlines / ANSI) or oversized identifiers downstream.
        if (!/^[A-Za-z0-9._-]{1,64}$/.test(parsedData.nodeId)) {
            console.warn("[VALIDATION FAILED] Packet dropped: nodeId failed strict identifier allowlist.");
            return null;
        }

        if (parsedData.reading === undefined || typeof parsedData.reading !== 'number') {
            console.warn(`[VALIDATION FAILED] Packet dropped from node [${parsedData.nodeId}]: Missing or invalid numeric metric.`);
            return null;
        }

        // 3. Physical Boundary Verification (Sanity bounds check)
        // Stops a bad actor from sending a soil moisture reading of 9999% or a negative value
        if (parsedData.reading < 0 || parsedData.reading > 100) {
            console.warn(`[CHAOS ALERT] Physical boundary violation on node [${parsedData.nodeId}]. Reading: ${parsedData.reading}. Clamping value.`);
            parsedData.reading = Math.max(0, Math.min(100, parsedData.reading));
        }

        // Return the cleansed, safe schema structure
        return {
            nodeId: parsedData.nodeId,
            reading: parsedData.reading,
            timestamp: parsedData.ts || Date.now()
        };

    } catch (parseError) {
        // Catches syntax malformations (broken arrays, toxic strings) without popping the heap
        console.error(`[CRITICAL PARSE FAULT] Trapped toxic payload exception: ${parseError.message}`);
        return null;
    }
}

module.exports = { safeParseTelemetry };
