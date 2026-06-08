// Coastal-Alpine-Core/src/attestation_validator.js
const crypto = require('crypto');

// The "Golden Baseline" - The exact expected SHA-256 hash digests of a clean, un-tampered Pi 5 boot sequence
const GOLDEN_PCR_DIGEST = "a3f5b7c890de1234567890abcdef1234567890abcdef1234567890abcdef1234"; // pragma: allowlist secret

/**
 * Validates a node's TPM 2.0 quote payload against the hardware Root of Trust.
 * @param {string} originalNonce - The challenge hex issued by the server.
 * @param {Object} attestationData - The payload packet returned from the edge node agent.
 * @param {string} aikPublicKeyPem - The registered public key of that specific device's AIK chip.
 * @returns {boolean} True if the node is pristine and validated.
 */
function verifyNodeAttestation(originalNonce, attestationData, aikPublicKeyPem) {
    try {
        const { quote, signature, pcr_values } = attestationData;

        // 1. Defend against replay attacks: Verify the quote contains the exact nonce we issued
        const quoteBuffer = Buffer.from(quote, 'hex');
        const nonceBuffer = Buffer.from(originalNonce, 'hex');
        
        if (!quoteBuffer.includes(nonceBuffer)) {
            console.error("[ATTESTATION DENIED] Nonce mismatch! Possible replay attack detected.");
            return false;
        }

        // 2. Cryptographic Signature Validation
        // Verify that the quote payload was genuinely signed by the hardware TPM's AIK private boundary
        const verifier = crypto.createVerify('SHA256');
        verifier.update(quoteBuffer);
        
        const isSignatureValid = verifier.verify(
            aikPublicKeyPem, 
            Buffer.from(signature, 'hex')
        );

        if (!isSignatureValid) {
            console.error("[ATTESTATION DENIED] Cryptographic signature validation failed. Spoofed hardware.");
            return false;
        }

        // 3. Firmware Configuration Integrity Check
        // Compute the digest of the incoming PCR matrix and match it against our Golden Baseline
        const incomingPCRHash = crypto.createHash('sha256').update(Buffer.from(pcr_values, 'hex')).digest('hex');
        
        if (incomingPCRHash !== GOLDEN_PCR_DIGEST) {
            console.error("[CRITICAL SECURITY FAILURE] Node configuration compromise detected!");
            console.error(`Expected Baseline: ${GOLDEN_PCR_DIGEST}`);
            console.error(`Received Baseline: ${incomingPCRHash}`);
            // This means the bootloader, kernel, or critical parameters were altered locally
            return false;
        }

        console.log("[SUCCESS] Node remote attestation successful. Integrity state validated.");
        return true;

    } catch (error) {
        console.error(`[SECOPS ERROR] Attestation verification engine exception: ${error.message}`);
        return false;
    }
}

module.exports = { verifyNodeAttestation };
