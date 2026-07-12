# Compliance — NZ AI + SOC 2 Type II

This repository is governed by the **NZ AI Compliance + SOC 2 Type II** framework.  
**Classification:** Diamond (primary) | Platinum (secondary) | Gold (tertiary)

## Purpose

Coastal Alpine Core is the **field + edge SDK** for Sovereign Edge systems. Handles:
- Patient data collection (health appointments, measurements)
- Encrypted local-first processing
- Secure API gateway for health data
- Firmware updates + device posture verification

**Compliance Impact:** CRITICAL
- Direct health data processing (IPP4 encryption mandatory)
- Field device security (prevent tampering)
- Firmware integrity verification (constant-time comparison)

## Key Requirements

- **Encryption:** AES-256 at rest, TLS 1.3+ in transit
- **Health Data:** 7-year retention max, deletion on-demand
- **Audit Trail:** All data access logged (immutable, 18 months)
- **Device Security:** Firmware hash verification (constant-time)

## Compliance Contacts

- Compliance Officer: [ASSIGN]
- Privacy Officer: [ASSIGN]
- CISO / Security Lead: [ASSIGN]

## Compliance Milestones

- [ ] Phase 1: Governance (Week 1)
- [ ] Phase 2: Technical controls (Week 4)
- [ ] Phase 3: Privacy Act (Week 4)
- [ ] Phase 4: Te Mana Raraunga (Week 6)
- [ ] Phase 5: Incident response (Week 8)
- [ ] Phase 6: SOC 2 audit (Week 12)

## Monthly Checklist

- [ ] Audit logs reviewed
- [ ] Firmware integrity verification working
- [ ] Health data encrypted
- [ ] No hardcoded credentials
- [ ] Backup restore test passed

**Sign-Off:** _________________ Date: _________

**Related:** [NZ AI Compliance Skill](./.github/compliance/nz-ai-compliance-soc2/)  
**Last Updated:** 2026-07-12
