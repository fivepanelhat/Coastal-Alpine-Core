// Coastal-Alpine-Core/src/index.js
// Public JS entry point for @fivepanelhat/coastal-alpine-core.
// Referenced by package.json "main". Keep exports explicit — this file
// defines the supported JS API surface of the Core SDK.
'use strict';

const { verifyNodeAttestation } = require('./attestation_validator');

module.exports = {
    verifyNodeAttestation
};
