# MongoDB Import Guide

This guide helps you import the JSON data files into MongoDB using `mongoimport`.

## Prerequisites

- MongoDB installed and running
- MongoDB command line tools (`mongoimport`) available
- Database connection access

## File Structure

```
databases/
├── accounts.json      # Government service accounts (JPJ, TNB)
├── license.json       # Malaysian driving license records
├── tnb.json          # TNB electricity bill records  
└── transactions.json  # Payment transaction records
```

## Data Format

All JSON files use **JSONL format** (JSON Lines) where each line contains one JSON document. This is the recommended format for MongoDB import.

## Import Commands

### 1. Import Accounts Data
```bash
mongoimport --db greataihackathon --collection accounts --file databases/accounts.json
```

### 2. Import License Data
```bash
mongoimport --db greataihackathon --collection licenses --file databases/license.json
```

### 3. Import TNB Bills Data
```bash
mongoimport --db greataihackathon --collection tnb --file databases/tnb.json
```

### 4. Import Transactions Data
```bash
mongoimport --db greataihackathon --collection transactions --file databases/transactions.json
```

### Import All Collections (Batch)
```bash
# Windows Command Prompt
mongoimport --db greataihackathon --collection accounts --file databases\accounts.json
mongoimport --db greataihackathon --collection licenses --file databases\license.json
mongoimport --db greataihackathon --collection tnb --file databases\tnb.json
mongoimport --db greataihackathon --collection transactions --file databases\transactions.json
```

```bash
# Unix/Linux/MacOS
mongoimport --uri "mongodb+srv://wenhao1223:1223@greataihackathon.npyt0oz.mongodb.net/" --db greataihackathon --collection accounts --file databases\accounts.json
mongoimport --uri "mongodb+srv://wenhao1223:1223@greataihackathon.npyt0oz.mongodb.net/" --db greataihackathon --collection licenses --file databases\license.json
mongoimport --uri "mongodb+srv://wenhao1223:1223@greataihackathon.npyt0oz.mongodb.net/" --db greataihackathon --collection tnb --file databases\tnb.json
mongoimport --uri "mongodb+srv://wenhao1223:1223@greataihackathon.npyt0oz.mongodb.net/" --db greataihackathon --collection transactions --file databases\transactions.json
```

## Connection Options

### Local MongoDB
```bash
mongoimport --host localhost:27017 --db greataihackathon --collection accounts --file databases/accounts.json
```

### MongoDB with Authentication
```bash
mongoimport --host localhost:27017 --db greataihackathon --username your_username --password your_password --authenticationDatabase admin --collection accounts --file databases/accounts.json
```

### MongoDB Atlas (Cloud)
```bash
mongoimport --uri "mongodb+srv://username:password@cluster.mongodb.net/ greataihackathon" --collection accounts --file databases/accounts.json
```

## Data Relationships

The collections are related as follows:

### TNB Bills → Transactions
- `tnb.bill.akaun.no_invois` links to `transactions.bill_reference`
- `tnb.pembayaran.rujukan` matches `transactions.reference_id`

### Accounts → Transactions
- `accounts.beneficiary_name` matches `transactions.beneficiary_name`
- `accounts.beneficiary_account` matches `transactions.beneficiary_account`

### License → Accounts (JPJ Service)
- License holders can make payments to JPJ accounts for renewals

## Sample Queries

### Find All TNB Bills
```javascript
db.tnb.find({"bill.tarif.jenis": "A: Kediaman"})
```

### Find Successful Transactions
```javascript
db.transactions.find({"status": "Successful"})
```

### Find Unpaid TNB Bills
```javascript
db.tnb.find({"status": "unpaid"})
```

### Link Transaction to TNB Bill
```javascript
db.transactions.aggregate([
  {
    $lookup: {
      from: "tnb",
      localField: "bill_reference",
      foreignField: "bill.akaun.no_invois",
      as: "bill_details"
    }
  }
])
```

### Find Transactions for Specific Beneficiary
```javascript
db.transactions.find({"beneficiary_name": "Tenaga Nasional Berhad"})
```

## Data Validation

After import, verify data count:

```javascript
// Check collection counts
db.accounts.countDocuments()      // Should return 3
db.licenses.countDocuments()      // Should return 7  
db.tnb.countDocuments()     // Should return 7
db.transactions.countDocuments()  // Should return 6
```

## Troubleshooting

### Common Issues

1. **File Path Issues (Windows)**
   - Use backslashes `\` for Windows paths
   - Use forward slashes `/` for Unix/Linux paths
   - Ensure you're in the correct directory

2. **Permission Denied**
   - Check file permissions
   - Run command prompt as administrator if needed

3. **Connection Refused**
   - Ensure MongoDB service is running
   - Check connection string and credentials

4. **Invalid JSON Format**
   - Files use JSONL format (one JSON object per line)
   - Each line must be valid JSON
   - No trailing commas allowed

### Verification Commands

```bash
# Check if MongoDB is running
mongo --eval "db.runCommand('ping')"

# List all databases
mongo --eval "show dbs"

# List collections in  greataihackathon database
mongo  greataihackathon --eval "show collections"
```

## Collection Schemas

### Accounts Collection
```javascript
{
  beneficiary_name: "String",
  beneficiary_account: "String", 
  beneficiary_bank: "String",
  service: "String", // JPJ or TNB
  qr_link: "String",
  active: Boolean
}
```

### License Collection
```javascript
{
  full_name: "String",
  identity_no: "String",
  date_of_birth: "String",
  nationality: "String", 
  license_number: "String",
  license_classes: ["Array of Strings"],
  valid_from: "String",
  valid_to: "String",
  address: "String",
  status: "String"
}
```

### TNB Bills Collection
```javascript
{
  bill: {
    akaun: { /* Account details */ },
    meta: { /* Bill metadata */ },
    tarif: { /* Tariff structure */ },
    caj: { /* Charges */ },
    meter: { /* Meter readings */ }
  },
  status: "String", // paid, unpaid, overdue
  pembayaran: { /* Payment details */ }
}
```

### Transactions Collection
```javascript
{
  transaction_id: "String",
  reference_id: "String",
  transaction_date: "ISODate",
  transaction_type: "String",
  amount: Number,
  currency: "String",
  status: "String",
  beneficiary_name: "String",
  beneficiary_account: "String",
  service_type: "String",
  bill_reference: "String"
}
```

## Notes

- All monetary amounts are in Malaysian Ringgit (MYR)
- Dates follow ISO 8601 format where applicable
- All collections contain realistic Malaysian government service data
- Data includes relationships for testing joins and aggregations

---

**Database Name**: ` greataihackathon`  
**Total Collections**: 4  
**Total Documents**: ~23 records  
**Data Type**: Malaysian Government Services (TNB, JPJ)


## Key Prompts
### License Renewal
1. Check for license record
    ```bash
    Find licence with identity number of 041223070745
    ```
    ```bash
    Find licence with license number of 0107011 mZyPs9aZ
    ```
2. Find JPJ service account
    ```bash
    Find account with service from JPJ
    ```
3. Create transaction record
    ```bash
    Create transaction record via DuitNow with these transaction details:
    {
      "beneficiary_name": "Jabatan Pengangkutan Jalan Malaysia",
      "beneficiary_account_number": "5123456789012345",
      "receiving_bank": "Maybank",
      "recipient_reference": "0488-MB-MAYBANK22/43",
      "reference_id": "837356732M",
      "payment_details": "license renewal",
      "amount": "RM 40.00",
      "successful_timestamp": "15 Sep 2025, 3:13 PM"
    }
    ```
4. Extend validity (1-10 years only)
    ```bash
    Update licence of identity number of 041223070745, validity extend 2 years
    ```
    ```bash
    Update licence of license number of 0107011 mZyPs9aZ, validity extend 2 years
    ```
    ```bash
    Extend 2 years licence 041223070745
    ```
    ```bash
    Extend 2 years licence 0107011 mZyPs9aZ
    ```
    **Note**: Validity extension must be between 1-10 years (integer values only)

### TNB Bill Payment
1. Check for unpaid TNB bills
    ```bash
    Find latest unpaid TNB bills for account number 220001234513
    ```
2. Show TnB service account details
    ```bash
    Find account with service from TNB
    ```
3. Make payment and create transaction record
    ```bash
    Update TNB bill 220001234513 sent via Maybank Online Banking with these transaction details:
    {
      "beneficiary_name": "Tenaga Nasional Berhad",
      "beneficiary_account_number": "3987654321098765",
      "receiving_bank": "CIMB Bank",
      "recipient_reference": "OLB20250918003",
      "reference_id": "OLB20250918003",
      "payment_details": "TNB bill payment",
      "amount": "RM 60.00",
      "successful_timestamp": "15 Sep 2025, 3:13 PM"
    }
    ```