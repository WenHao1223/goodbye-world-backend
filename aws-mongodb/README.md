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

## Using the MongoDB MCP Server (main.py)

The `main.py` script provides a natural language interface to interact with the MongoDB database using AWS Bedrock for intelligent parsing.

### Prerequisites

1. **Environment Setup**
   - Python 3.7+ installed
   - Required Python packages: `pymongo`, `python-dotenv`, `boto3`
   - AWS credentials configured for Bedrock access
   - MongoDB connection details in `.env` file

2. **Install Dependencies**
   ```bash
   pip install pymongo python-dotenv boto3
   ```

3. **Environment Configuration**
   Create a `.env` file in the project root:
   ```properties
   ATLAS_URI=mongodb+srv://username:password@cluster.mongodb.net/?retryWrites=true&w=majority
   ATLAS_DB_NAME=greataihackathon
   AWS_REGION=us-east-1
   AWS_PROFILE=your-aws-profile
   BEDROCK_MODEL_ID=anthropic.claude-3-haiku-20240307-v1:0
   ```

### Running the Server

#### Interactive Mode
```bash
python main.py
```

This starts an interactive session where you can enter natural language instructions:

```
Enter instruction (Ctrl+Z for multi-line, then Enter):
find account from tnb service
```

##### Multi-line Instructions
For complex instructions with JSON data, use Ctrl+Z (Windows) or Ctrl+D (Unix) to submit:

```
Enter instruction (Ctrl+Z for multi-line, then Enter):
Update TNB bill 220001234513 with transaction details:
{
  "beneficiary_name": "Tenaga Nasional Berhad",
  "reference_id": "OLB20250918003",
  "amount": "RM 60.00"
}
^Z
```

##### Exit Commands
- Type `exit`, `quit`, or `q` to quit
- Use Ctrl+C to interrupt

#### One-Line CLI Execution
Execute single commands directly from command line:

```bash
# Basic syntax
python main.py "your instruction here"

# Examples
python main.py "find account from tnb service"
python main.py "find licence with identity number of 041223070745"
python main.py "find latest unpaid TNB bills for account number 220001234513"
python main.py "extend 2 years licence 041223070745"
```

For complex instructions with JSON, use quotes carefully:
```bash
# Windows Command Prompt
python main.py "Update TNB bill 220001234513 paid RM 45.67 reference 837356732M"

# PowerShell (escape quotes)
python main.py 'Update TNB bill 220001234513 paid RM 45.67 reference 837356732M'

# For JSON instructions, save to file and use file input
echo "Update TNB bill 220001234513 with transaction details: {\"reference_id\": \"OLB20250918003\", \"amount\": \"RM 60.00\"}" > instruction.txt
python main.py < instruction.txt
```

### Supported Natural Language Commands

#### License Operations
```bash
# Find license records
Find licence with identity number of 041223070745
Find licence with license number of 0107011 mZyPs9aZ

# Extend license validity (1-10 years)
Extend 2 years licence 041223070745
Update licence of identity number of 041223070745, validity extend 3 years
```

#### TNB Bill Operations
```bash
# Find TNB bills
Find latest unpaid TNB bills for account number 220001234513
Find all TNB bills for account 220001234513

# Update TNB payment
Update TNB bill 220001234513 paid RM 45.67 reference 837356732M
Update TNB bill 220001234513 paid full today using Online Banking
```

#### Transaction Operations
```bash
# Create transaction records
Create DuitNow transaction: reference 837356732M, RM 40.00, Jabatan Pengangkutan Jalan Malaysia

# Process payments with bill updates
Create transaction and update TNB bill 220001234513 if applicable
```

#### Account Operations
```bash
# Find service accounts
Find account from TNB service
Find account from JPJ service
Find all accounts
```

### Advanced Usage Examples

#### Complete License Renewal Workflow
```bash
# 1. Check license status
Find licence with identity number of 041223070745

# 2. Find JPJ service account
Find account from JPJ service

# 3. Create transaction record
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

# 4. Extend license validity
Extend 2 years licence 041223070745
```

#### Complete TNB Bill Payment Workflow
```bash
# 1. Check outstanding bills
Find latest unpaid TNB bills for account number 220001234513

# 2. Get TNB account details
Find account from TNB service

# 3. Process payment with transaction
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

### Response Format

All operations return JSON responses with:
- **Success indicator**: `"success": true/false`
- **Operation message**: Description of the action performed
- **Affected documents**: Complete documents that were created/updated
- **Count/IDs**: For find operations, document count and IDs

Example response:
```json
{
  "success": true,
  "message": "TNB payment updated and transaction OLB20250918003 created",
  "documents": {
    "tnb": { /* Updated TNB bill document */ },
    "transactions": { /* Created transaction document */ }
  }
}
```

### Troubleshooting

#### Common Issues

1. **AWS Bedrock Access Denied**
   - Verify AWS credentials are configured
   - Check IAM permissions for Bedrock access
   - Ensure correct AWS region is set

2. **MongoDB Connection Failed**
   - Verify connection string in `.env` file
   - Check MongoDB Atlas IP whitelist
   - Ensure database name is correct

3. **Parsing Errors**
   - Use clear, descriptive natural language
   - Include all required details in instructions
   - Check examples for proper formatting

4. **Environment Variables Not Found**
   - Ensure `.env` file exists in project root
   - Check file permissions and format
   - Verify all required variables are set

### Performance Notes

- First request may take longer due to AWS Bedrock cold start
- Complex parsing operations may take 2-3 seconds
- Large JSON responses are automatically formatted for readability
- All database operations include proper error handling and validation


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