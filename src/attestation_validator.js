// Coastal-Alpine-Core/src/attestation_validator.js
const crypto = require('crypto');

// The "Golden Baseline" - The exact expected SHA-256 hash digests of a clean, un-tampered Pi 5 boot sequence.
// Overridable via env so fleet re-baselining after a firmware update doesn't require a code release.
const GOLDEN_PCR_DIGEST = process.env.CAT_GOLDEN_PCR_DIGEST
 || "a3f5b7c890de1234567890abcdef1234567890abcdef1234567890abcdef1234"; // pragma: allowlist secret

// Minimum challenge entropy: 16 bytes (32 hex chars). Anything shorter makes
// the replay-defense substring check trivially satisfiable.
const MIN_NONCE_HEX_CHARS = 32;

/**
 * Strict hex validation. Buffer.from(str, 'hex') silently truncates at the
 * first invalid character and returns an EMPTY buffer for fully invalid
 * input - and an empty nonce buffer would make the replay check pass for
 * any quote. Every hex field must therefore be positively validated first.
 */
function isStrictHex(value, minChars = 2) {
 return typeof value === 'string'
 && value.length >= minChars
 && value.length % 2 === 0
 && /^[0-9a-f]+$/i.test(value);
}

/**
 * Validates a node's TPM 2.0 quote payload against the hardware Root of Trust.
 * @param {string} originalNonce - The challenge hex issued by the server.
 * @param {Object} attestationData - The payload packet returned from the edge node agent.
 * @param {string} aikPublicKeyPem - The registered public key of that specific device's AIK chip.
 * @returns {boolean} True if the node is pristine and validated.
 */
function verifyNodeAttestation(originalNonce, attestationData, aikPublicKeyPem) {
 try {
 if (!attestationData || typeof attestationData !== 'object') {
 console.error("[ATTESTATION DENIED] Missing or malformed attestation payload.");
 return false;
 }
 const { quote, signature, pcr_values } = attestationData;

 // 0. Fail-closed input validation before any buffer is built.
 if (!isStrictHex(originalNonce, MIN_NONCE_HEX_CHARS)) {
 console.error("[ATTESTATION DENIED] Challenge nonce missing, too short, or not valid hex.");
 return false;
 }
 if (!isStrictHex(quote) || !isStrictHex(signature) || !isStrictHex(pcr_values)) {
 console.error("[ATTESTATION DENIED] Quote, signature, or PCR values failed strict hex validation.");
 return false;
 }
 if (typeof aikPublicKeyPem !== 'string' || !aikPublicKeyPem.includes('BEGIN')) {
 console.error("[ATTESTATION DENIED] AIK public key missing or not PEM-encoded.");
 return false;
 }

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
 // Compute the digest of the incoming PCR matrix and match it against our Golden Baseline.
 // timingSafeEqual: the comparison must not leak matching-prefix length via timing.
 const incomingPCRHash = crypto.createHash('sha256').update(Buffer.from(pcr_values, 'hex')).digest();
 const goldenBuffer = Buffer.from(GOLDEN_PCR_DIGEST, 'hex');

 if (incomingPCRHash.length !== goldenBuffer.length
 || !crypto.timingSafeEqual(incomingPCRHash, goldenBuffer)) {
 console.error("[CRITICAL SECURITY FAILURE] Node configuration compromise detected!");
 // Do not echo the digests: attackers iterating on spoofed PCR
 // payloads should not be handed the expected baseline in logs.
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
