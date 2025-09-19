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