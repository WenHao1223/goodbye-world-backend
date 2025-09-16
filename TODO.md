 # Text Extract
 - Documents must be fewer than 11 pages, smaller than 5 MB, and one of the following formats: JPEG, PNG, or PDF.

 ## Verify Identity
 1. Extract text from identity verification document (DONE)
 2. Return table-format JSON response (DONE)
 3. Filter only important info for identity verification
 4. Return true / false / not enough info to validate

 ## Gov SOPs
  1. Extract text from government-issued SOP document (DONE)s
  2. Return table-format JSON response (DONE)
  3. Filter only important info for SOP verification
  4. Return true / false / not enough info to validate

## Verify Payment
 1. Extract text from bank receipt (DONE)
 2. Return table-format JSON response (DONE)
 3. Check if correct:
    - bank account
    - bank name
    - beneficiary name
    - date is after date sending instruction WhatsApp message
 4. Check with transaction history
 5. Return true / fail to process payment

## Checklist
 1. Canonical Licence scheme + mapper from current JSON (/)
 2. Validation module (formats, confidence, expiry)
 3. Face match + (optional) liveness step in the chat flow.
 4. Case creation + summons lookup integration.
 5. Payment intent endpoint + WhatsApp pay CTA + webhook handler.
 6. Consent & audit logging, encryption, retention, masking.
 7. Fallback flows & manual review tooling.