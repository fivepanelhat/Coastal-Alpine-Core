// Regression tests for attestation_validator hardening (node --test).
// Pins the fail-closed paths: invalid hex must never satisfy the nonce
// replay check via Buffer.from()'s silent truncation behaviour.
const { test } = require('node:test');
const assert = require('node:assert');
const crypto = require('crypto');

// Build a self-consistent happy-path fixture, then point the golden
// baseline at it via env BEFORE the module is loaded.
const keyPair = crypto.generateKeyPairSync('rsa', { modulusLength: 2048 });
const aikPublicKeyPem = keyPair.publicKey.export({ type: 'spki', format: 'pem' });

const nonce = crypto.randomBytes(16).toString('hex');
const quote = nonce + crypto.randomBytes(32).toString('hex');
const quoteBuffer = Buffer.from(quote, 'hex');

const signer = crypto.createSign('SHA256');
signer.update(quoteBuffer);
const signature = signer.sign(keyPair.privateKey).toString('hex');

const pcrValues = crypto.randomBytes(64).toString('hex');
const goldenDigest = crypto.createHash('sha256')
    .update(Buffer.from(pcrValues, 'hex'))
    .digest('hex');

process.env.CAT_GOLDEN_PCR_DIGEST = goldenDigest;
const { verifyNodeAttestation } = require('../src/attestation_validator');

const validAttestation = { quote, signature, pcr_values: pcrValues };

test('valid attestation passes', () => {
    assert.strictEqual(
        verifyNodeAttestation(nonce, validAttestation, aikPublicKeyPem),
        true
    );
});

test('empty nonce is rejected (Buffer.from truncation bypass)', () => {
    assert.strictEqual(verifyNodeAttestation('', validAttestation, aikPublicKeyPem), false);
});

test('non-hex nonce is rejected', () => {
    assert.strictEqual(
        verifyNodeAttestation('zzzz-not-hex-zzzz-not-hex-zzzz!!', validAttestation, aikPublicKeyPem),
        false
    );
});

test('short nonce below entropy floor is rejected', () => {
    assert.strictEqual(verifyNodeAttestation('abcd', validAttestation, aikPublicKeyPem), false);
});

test('wrong nonce is rejected (replay defense)', () => {
    const otherNonce = crypto.randomBytes(16).toString('hex');
    assert.strictEqual(verifyNodeAttestation(otherNonce, validAttestation, aikPublicKeyPem), false);
});

test('tampered signature is rejected', () => {
    const tampered = { ...validAttestation, signature: crypto.randomBytes(256).toString('hex') };
    assert.strictEqual(verifyNodeAttestation(nonce, tampered, aikPublicKeyPem), false);
});

test('mutated PCR values are rejected', () => {
    const mutated = { ...validAttestation, pcr_values: crypto.randomBytes(64).toString('hex') };
    assert.strictEqual(verifyNodeAttestation(nonce, mutated, aikPublicKeyPem), false);
});

test('missing payload and malformed key fail closed', () => {
    assert.strictEqual(verifyNodeAttestation(nonce, null, aikPublicKeyPem), false);
    assert.strictEqual(verifyNodeAttestation(nonce, validAttestation, 'not-a-pem'), false);
});
