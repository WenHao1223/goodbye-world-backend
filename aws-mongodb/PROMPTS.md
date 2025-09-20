# Malaysian Government Services Database - Test Cases

> Test cases include both single line and multi-line input commands

## 1. Account Queries

### Test Case 1.1: Find TNB Account
**Input:**
```bash
Find account with service from TNB
```
**Expected:** Returns TNB service account details

### Test Case 1.2: Find JPJ Account
**Input:**
```bash
Find account with service from JPJ
```
**Expected:** Returns JPJ service account details

### Test Case 1.3: Alternative Account Query
**Input:**
```bash
Find account for JPJ
```
**Expected:** Returns JPJ service account using alternative phrasing

### Test Case 1.4: Find both JPJ and TNB Accounts
**Input:**
```bash
Find accounts from JPJ and TNB
```

## 2. License Queries

### Test Case 2.1: Find License by Identity Number
**Input:**
```bash
Find licence with identity number of 041223070745
```
**Expected:** Returns license details for identity 041223070745

### Test Case 2.2: Find License by License Number
**Input:** 
```bash
Find licence with license number of 0107011 mZyPs9aZ
```
**Expected:** Returns license details for license number 0107011 mZyPs9aZ

### Test Case 2.3: Alternative License Search by License Number
**Input:**
```bash
Search license for 0107011 mZyPs9aZ
```
**Expected:** Returns license details using alternative phrasing (searches by license_number)

### Test Case 2.4: Alternative License Search by Identity Number
**Input:**
```bash
Search license for 041223070745
```
**Expected:** Returns license details using alternative phrasing (searches by identity_no for 12-digit numbers)

### Test Case 2.5: Get License with IC
**Input:**
```bash
Get license for person 041223070745
```
**Expected:** Returns license details using different phrasing

## 3. TNB Bill Queries

### Test Case 3.1: Find TNB Bill
**Input:**
```bash
Find tnb bill with account number of 220001234513
```
**Expected:** Returns TNB bill details for account 220001234513

### Test Case 3.2: Alternative TNB Bill Search
**Input:**
```bash
Show me TNB bills of 220001234513
```
**Expected:** Returns TNB bill details using alternative phrasing

### Test Case 3.3: TNB Debt Query by Account Number
**Input:**
```bash
How much money does account 220001234513 owes tnb
```
**Expected:** Returns TNB bill details for account 220001234513 to check outstanding amounts

## 4. License Updates

### Test Case 4.1: Extend Active License
**Input:**
```bash
Update licence of identity number of 041223070745, validity extend 2 years
```
**Expected:** Extends license validity by 2 years from current expiry date

### Test Case 4.2: Extend Expired License
**Input:**
```bash
Update licence of identity number of 920308145678, validity extend 2 years
```
**Expected:** Sets new validity from today + 2 years, status changes to active

### Test Case 4.3: License Extension with Different Years
**Input:**
```bash
Update licence of identity number of 041223070745, validity extend 3 years
```
**Expected:** Extends license validity by 3 years

### Test Case 4.4: Alternative License Extension Syntax
**Input:**
```bash
Extend 3 years licence 041223070745
```
**Expected:** Extends license validity by 3 years using alternative syntax

### Test Case 4.5: License Extension by License Number
**Input:**
```bash
Extend 3 years licence 0107011 mZyPs9aZ
```
**Expected:** Extends license validity by 3 years using license number instead of identity number

### Test Case 4.6: License Renewal Request
**Input:**
```bash
040218070711 want to renew licence for 3 years
```
**Expected:** Extends license validity by 3 years using renewal terminology

## 5. TNB Bill Updates

### Test Case 5.1: Update TNB Bill Payment
**Input:**
```bash
Update TnB bill with account number of 220001234513 that it has paid full today using Online Banking with transaction reference number of OLB20250918003
```
**Expected:** Updates TNB bill status to paid with payment details

### Test Case 5.2: TNB Payment with Different Reference
**Input:**
```bash
Update TNB bill 220001234513 paid using Online Banking reference OLB20250918004
```
**Expected:** Updates TNB bill with different reference number

### Test Case 5.3: Update Already Paid TNB Bill
**Input:**
```bash
Update TNB bill 220001234513 paid using Online Banking reference OLB20250918005
```
**Expected:** Updates payment details even if bill is already paid, shows message indicating bill was already paid

### Test Case 5.4: Update Already Paid Bill
**Input:**
```bash
Update TNB bill 220001234513 paid using Online Banking reference OLB20250918005
```
**Expected:** Returns error "Bill is already paid. No further updates allowed."

### Test Case 5.5: TNB Payment Without Reference Number
**Input:**
```bash
Update TnB bill with account number of 220001234513 that it has paid rm100 today using Online Banking
```
**Expected:** Updates TNB bill with manual payment reference

### Test Case 5.6: Partial TNB Payment
**Input:**
```bash
Update TnB bill with account number of 220001234517 that it has paid rm50 today using Online Banking
```
**Expected:** Updates TNB bill with partial payment amount (RM50), status changes to "unpaid" instead of "partial"

### Test Case 5.7: Full TNB Payment
**Input:**
```bash
Update TnB bill with account number of 220001234517 that it has paid full today using Online Banking
```
**Expected:** Updates TNB bill with full payment amount, status changes to "unpaid" instead of "paid"

### Test Case 5.8: TNB Payment with Transaction Creation and Beneficiary Details
**Input:**
```bash
Update TNB bill 220001234513 paid to account number 3987654321098765 using Online Banking reference OLB20250918004 and record transaction
```
**Expected:** 
- Updates TNB bill status to "paid"
- Creates transaction record with beneficiary details from accounts.json:
  - beneficiary_name: "Tenaga Nasional Berhad"
  - beneficiary_account: "3987654321098765"
  - beneficiary_bank: "CIMB Bank"
  - service_type: "TNB"
  - reference_id: "OLB20250918004"

## 6. Transaction Processing

### Test Case 6.1: Create Transaction Record
**Input:**
```bash
Create transaction record reference 837356732M amount RM 100.00 beneficiary DELLAND PROPERTY MANAGEMENT SDN BHD
```
**Expected:** Creates new transaction record in transactions collection

### Test Case 6.2: Process Payment Receipt
**Input:**
```bash
Process payment receipt reference TNG20250925ABC124 amount RM 185.45 beneficiary Tenaga Nasional Berhad account 3987654321098765 date 25Sep2025 to paid for TNB account 220001234513
```
**Expected:** Creates transaction record with TNB payment details and updates relevant TNB bill if applicable (full payment)

### Test Case 6.3: Process Payment Receipt with Partial Amount
**Input:**
```bash
Process payment receipt reference TNG20250925ABC125 amount RM 100 beneficiary Tenaga Nasional Berhad account 3987654321098765 date 25Sep2025 to paid for TNB account 220001234513
```
**Expected:** Creates transaction record with TNB payment details and updates relevant TNB bill if applicable (partial payment)

### Test Case 6.4: Update TNB and Create Transaction
**Input:**
```bash
Update TNB bill 220001234513 paid RM 45.67 via DuitNow reference 837356732M and record transaction
```
**Expected:** Updates TNB bill status and creates corresponding transaction record

## 7. Error Handling

### Test Case 7.1: Find Suspended License
**Input:**
```bash
Find licence with identity number of 950625145432
```
**Expected:** Returns license with suspension warning message

### Test Case 7.2: Try to Update Suspended License
**Input:**
```bash
Update licence of identity number of 950625145432, validity extend 2 years
```
**Expected:** Returns error - license suspended, visit physical branch

### Test Case 7.3: Find Non-existent License
**Input:**
```bash
Find licence with identity number of 999999999999
```
**Expected:** Returns no results found

### Test Case 7.4: Find Non-existent Service
**Input:**
```bash
Find account with service from XYZ
```
**Expected:** Returns no results found

## 8. Complex Operations

### Test Case 8.1: Complex Payment Processing
**Input:**
```bash
Process DuitNow payment 837356732M of RM 100.00 to TNB account 220001234513 and create transaction record
```
**Expected:** Updates TNB bill, creates transaction, matches beneficiary from accounts

### Test Case 8.2: Complex Payment Processing
**Input:**
```bash
Process DuitNow payment 837356732M of RM 100.00 to JPJ account 220001234513 and create transaction record
```
**Expected:** Create transaction, matches beneficiary from accounts

## 9. Multi-line Input Test Cases

### Test Case 9.1: Process Payment Receipt (Multi-line)
**Input:** (Use Ctrl+Z after typing)
```bash
Process payment receipt:
Reference: 837356732M
Amount: RM 100.00
Beneficiary: DELLAND PROPERTY MANAGEMENT SDN BHD
Beneficiary Account: 8881013422383
Date: 15 Sep 2025
Update TNB bill 220001234513 and create transaction record
```
**Expected:** Creates transaction record and updates relevant TNB bill

### Test Case 9.2: Update Multiple Records (Multi-line)
**Input:** (Use Ctrl+Z after typing)
```bash
Update multiple records:
1. Mark TNB bill 220001234513 as paid
2. Create transaction record with reference OLB20250918003
3. Amount RM 50 via Online Banking
4. Update payment status to successful
```
**Expected:** 
- Checks if TNB bill 220001234513 has existing pembayaran record
- If pembayaran is null: Updates TNB bill status and creates corresponding transaction record
- If pembayaran exists: Returns error "Bill already has payment record. No further updates allowed."

### Test Case 9.3: Complex License Update (Multi-line)
**Input:** (Use Ctrl+Z after typing)
```bash
Update license for identity 920308145678:
- Extend validity by 2 years
- Change status from expired to active
- Set valid_from to today if currently expired
- Otherwise extend from current valid_to date
```
**Expected:** Extends license validity with proper date logic and status update

### Test Case 9.4: Batch Payment Processing (Multi-line)
**Input:** (Use Ctrl+Z after typing)
```bash
Process batch payment:
Reference: 837356732M
Type: DuitNow Transfer
Amount: RM 100.00
Beneficiary: DELLAND PROPERTY MANAGEMENT SDN BHD
Account: 8881013422383
Bank: AmBANK BERHAD
Date: 15 Sep 2025
Create transaction and update TNB bill 220001234513 if applicable
```
**Expected:** 
- Checks if TNB bill 220001234513 has existing pembayaran record
- If pembayaran is null: Creates transaction record and updates TNB bill
- If pembayaran exists: Returns error "TNB bill 220001234513 already has payment record. No further updates allowed."