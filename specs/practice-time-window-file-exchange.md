# Feature: Practice Time Window File Exchange

## Summary

A serverless workflow that enables healthcare practices to configure their appointment confirmation call windows via an Excel-based file exchange. An admin generates a unique token-based URL, the practice downloads a pre-formatted Excel template, fills in their phone numbers and calling windows, and uploads the completed file. The system validates and converts the Excel data into per-practice JSON configurations that are ingested into a DynamoDB-backed API controlling when automated scheduling calls can be placed.

## Requirements

1. Admin shall generate a unique 64-character token stored in DynamoDB with a 7-day TTL and email the corresponding URL to the practice via SendGrid.
2. The system shall validate the token on page load and disable all interactive elements if the token is missing, invalid, or expired.
3. The customer shall be able to download a pre-formatted Excel template (`practice_time_window_template.xlsx`) via a presigned S3 GET URL (5-minute expiry).
4. The Excel template shall include: bold headers, an example row, timezone dropdown validation (5 US timezones), and input prompts on day-of-week columns specifying `HH:MM-HH:MM` format.
5. The customer shall be able to upload a completed `.xlsx` file via drag-and-drop or file browser, using a presigned S3 PUT URL (5-minute expiry) to path `uploads/{token}/{filename}`.
6. The conversion process shall parse the uploaded Excel workbook (sheet named `config`) and produce one JSON file per row, named `{phone_without_plus}.json`.
7. The converter shall validate all time values against 24-hour `HH:MM` format and reject the entire file (writing zero output) if any value is invalid, reporting all errors.
8. The converter shall detect and reject duplicate phone numbers within a single upload.
9. Each JSON output shall conform to the practice-time-window schema: `tz`, `max_days` (int), `attempts_per_day` (int), `windows[]` (array of `{dow, start, end}`), `alternate_ivr_behavior` (bool), and optionally `alternate_ivr_description` (string, omitted if blank).
10. The JSON files shall be uploaded to the practice-time-window API via `PUT /config/practice-time-window/%2B{phone}` using direct Lambda invocation with IAM authentication.
11. The frontend shall display inline status messages for success and descriptive error messages for failures.
12. A companion PDF (`customer_instructions.pdf`) shall be generated with column guide, time format rules, timezone list, and pre-submission checklist.

## Non-Functional Requirements

- **Security**: Token-based access only (no user accounts). Presigned URLs expire after 5 minutes. Lambda invocations require IAM permissions (`lambda:InvokeFunction`). Tokens generated via `secrets.token_urlsafe(48)`. HTTPS enforced. S3 AES-256 encryption. Referrer-Policy: no-referrer.
- **Compliance**: System handles practice phone numbers and scheduling data — no PHI is stored in the file exchange layer.
- **Performance**: Presigned URL generation must complete within Lambda's default timeout. Conversion must handle workbooks with up to hundreds of rows.
- **Availability**: Serverless architecture (Lambda + S3 + DynamoDB + CloudFront) provides inherent high availability.
- **Usability**: Single-page interface requiring no login; 5–10 minute completion time for practices.

## Technical Notes

| Component | Technology |
|-----------|-----------|
| Frontend | Static HTML/CSS/JS (vanilla, Inter font, card layout), hosted on S3 + CloudFront |
| Backend | AWS Lambda (Python 3.12), API Gateway (HTTP API) |
| Storage | S3 (templates, uploads, converted JSON), DynamoDB (tokens table) |
| Excel I/O | openpyxl 3.1.5 |
| PDF generation | fpdf2 2.8.3 |
| AWS SDK | boto3 |
| Email | SendGrid (planned) |
| IaC | Terraform |
| Auth | Token validation via DynamoDB + IAM for Lambda invocations |

### API Routes

| Method | Path | Lambda | Purpose |
|--------|------|--------|---------|
| GET | `/validate?token=` | `validate_token` | Check token validity |
| GET | `/template?token=` | `get_template` | Return presigned download URL |
| GET | `/upload-url?token=&filename=` | `get_upload_url` | Return presigned upload URL |
| *(S3 trigger)* | `uploads/` prefix | `convert_excel` | Convert uploaded Excel to JSON |

### DynamoDB Schema (Tokens Table)

| Attribute | Type | Notes |
|-----------|------|-------|
| `token` | String (PK) | 64-char token via `secrets.token_urlsafe(48)` |
| `customer_name` | String | Practice/org name |
| `email` | String | Contact email |
| `created_at` | String | ISO timestamp |
| `ttl` | Number | Unix epoch + 7 days (DynamoDB TTL attribute) |

### S3 Bucket Structure

```
template/
  practice_time_window_template.xlsx
uploads/
  {token}/
    {filename}.xlsx
json/
  {token}/
    {phone}.json
```

### Data Flow

```
Admin generates token → DynamoDB
                              ↓
Customer visits URL → validate_token → enable/disable UI
                              ↓
Download template ← get_template ← S3 presigned GET
                              ↓
Customer fills template offline
                              ↓
Upload file → get_upload_url → S3 presigned PUT → S3 uploads/{token}/
                              ↓
S3 ObjectCreated trigger → convert_excel Lambda
                              ↓
Validated JSON files → PUT /config/practice-time-window/{phone} → DynamoDB
```

---

## Build Instructions (What Has Been Built)

### Project Structure

```
webfrontEnd/
├── index.html                          # Single-page customer portal
├── lambdas/
│   ├── get_template/handler.py         # Presigned S3 GET URL for template download
│   └── get_upload_url/handler.py       # Presigned S3 PUT URL for file upload
├── scripts/
│   └── generate_token.py              # CLI: generate token + store in DynamoDB
└── docs/
    ├── design_summary.md
    ├── next_steps.md
    └── resume_prompt.md

excel2json/
├── convert.py                          # Excel → JSON converter (core logic)
├── create_template.py                  # Generates blank Excel template
├── generate_instructions_pdf.py        # Generates customer instructions PDF
└── json/                               # Sample output JSON files

api_client/
└── practice_time_window_client.py      # boto3 Lambda client for PUT configs
```

### Step 1: Excel Template Generation

**File**: `excel2json/create_template.py`  
**Dependencies**: `openpyxl==3.1.5`

Creates `practice_time_window_template.xlsx` with:
- Sheet named `config` with 13 columns: `phone`, `tz`, `max_days`, `attempts_per_day`, `Monday`–`Sunday`, `alternate_ivr_behavior`, `alternate_ivr_description`
- Bold blue header row, one pre-filled example row
- Timezone dropdown validation on column B (America/New_York, Chicago, Denver, Los_Angeles, Phoenix)
- Input prompts on day columns (E–K) explaining `HH:MM-HH:MM` format
- Auto-sized column widths

Run: `python excel2json/create_template.py`

### Step 2: Customer Instructions PDF

**File**: `excel2json/generate_instructions_pdf.py`  
**Dependencies**: `fpdf2==2.8.3`

Generates `customer_instructions.pdf` with step-by-step guide for filling out the template.

Run: `python excel2json/generate_instructions_pdf.py`

### Step 3: Excel-to-JSON Conversion

**File**: `excel2json/convert.py`  
**Dependencies**: `openpyxl==3.1.5`

Conversion logic:
1. Opens workbook, reads sheet `config`, headers from row 1
2. Iterates rows starting at row 2
3. Validates all time values via regex `^([01]\d|2[0-3]):[0-5]\d$`
4. Checks for duplicate phone numbers
5. If validation passes: writes one `{phone}.json` per row to output directory
6. If validation fails: prints all errors, exits without writing any files

Day-of-week mapping: Monday=0, Tuesday=1, ..., Sunday=6  
Time windows: comma-separated `HH:MM-HH:MM` ranges per day cell

Run: `python excel2json/convert.py <input.xlsx> [output_dir]`

### Step 4: API Client (Batch Upload to Lambda)

**File**: `api_client/practice_time_window_client.py`  
**Dependencies**: `boto3`

- `PracticeTimeWindowClient(lambda_function_name)` — wraps boto3 Lambda invocation
- `put(practice_phone, body)` — constructs API Gateway proxy event, invokes Lambda synchronously
- `put_batch(entries)` — iterates dict of `{phone: body}` pairs, calls `put()` for each
- Target endpoint: `PUT /config/practice-time-window/%2B{phone}`
- Auth: IAM credentials via boto3 credential chain

### Step 5: Token Generation

**File**: `webfrontEnd/scripts/generate_token.py`  
**Dependencies**: `boto3`

CLI script that:
1. Generates a 64-char token via `secrets.token_urlsafe(48)`
2. Stores in DynamoDB with `customer_name`, `email`, `created_at`, and `ttl` (7 days)
3. Outputs the full customer URL

Run: `python webfrontEnd/scripts/generate_token.py`

### Step 6: Frontend (Customer Portal)

**File**: `webfrontEnd/index.html`

Single-page static site with:
- Token extraction from URL query param
- Welcome section with 4-step process overview
- Download Template button → calls `GET /template?token=` → presigned S3 URL → browser download
- Upload area (drag-and-drop + file browser) → calls `GET /upload-url?token=&filename=` → presigned S3 PUT URL → direct PUT to S3
- Inline success/error status messages
- Branding: dark navy (#0d2137) + teal (#3bbfa0), Inter font, card layout

### Step 7: Lambda — get_template

**File**: `webfrontEnd/lambdas/get_template/handler.py`  
**Runtime**: Python 3.12, boto3

1. Receives `GET /template?token=`
2. Validates token exists in DynamoDB
3. Generates presigned S3 GET URL (5-min expiry) for the template file
4. Returns URL in response body

### Step 8: Lambda — get_upload_url

**File**: `webfrontEnd/lambdas/get_upload_url/handler.py`  
**Runtime**: Python 3.12, boto3

1. Receives `GET /upload-url?token=&filename=`
2. Validates token exists in DynamoDB
3. Generates presigned S3 PUT URL (5-min expiry) for path `uploads/{token}/{filename}`
4. Returns URL in response body

---

## Next Steps (Remaining Work)

### 1. Terraform — DynamoDB Table
- Create tokens table with `token` as partition key (String)
- Enable TTL on `ttl` attribute
- On-demand billing

### 2. Terraform — S3 Bucket
- Single bucket with prefixes: `template/`, `uploads/`, `json/`
- AES-256 server-side encryption
- CORS configuration allowing GET/PUT from CloudFront domain
- Block public access (presigned URLs only)

### 3. Lambda — validate_token (NOT YET BUILT)
- `GET /validate?token=` → query DynamoDB → return 200 (valid) or 403 (invalid/expired)
- Update `index.html` to call this on page load and disable UI if invalid

### 4. Terraform — API Gateway HTTP API
- Routes: `/validate`, `/template`, `/upload-url`
- Lambda integrations for each route
- CORS headers

### 5. Lambda — convert_excel (NOT YET BUILT)
- Triggered by S3 ObjectCreated on `uploads/` prefix
- Port logic from `excel2json/convert.py` into Lambda handler
- Read uploaded file from S3, validate, convert
- Write JSON output to `json/{token}/` in S3
- Invoke practice-time-window API (or write directly to DynamoDB) for each valid config
- Handle errors: store error report in S3 or notify admin

### 6. Terraform — S3 Event → Lambda Trigger
- Configure S3 notification on `uploads/` prefix → invoke `convert_excel` Lambda

### 7. Terraform — Static Site Hosting
- S3 bucket for static assets (index.html)
- CloudFront distribution with Referrer-Policy: no-referrer
- Custom domain (if applicable)

### 8. Frontend — Set API_BASE URL
- Update `index.html` to point to deployed API Gateway endpoint

### 9. SendGrid Integration (CREDENTIALS PENDING)
- Integrate with token generation script
- Send branded email with unique URL to practice contact
- Include instructions PDF as attachment or inline link

### 10. End-to-End Testing
- Generate token → visit URL → download template → fill out → upload → verify JSON output in S3 → verify DynamoDB configs updated

---

## Out of Scope

- Patient-facing appointment views or confirmations (handled by separate outreach engine)
- Real-time status tracking of conversion progress
- Admin dashboard for managing tokens or viewing submissions
- Multi-file or multi-sheet uploads
- Editing previously submitted configurations through the portal
- SMS/voice outreach execution (downstream system)
- CareNav integration and journey document management

## Acceptance Criteria

1. Given a valid token URL, the page loads with download and upload controls enabled.
2. Given an invalid or expired token, the page displays an error banner and all controls are disabled.
3. Given a click on "Download Template", the browser downloads a valid `.xlsx` file with correct headers, example row, timezone dropdown, and input prompts.
4. Given a valid `.xlsx` upload with correct data, the file is stored at `uploads/{token}/{filename}` in S3 and a success message is displayed.
5. Given an uploaded Excel file with valid data, the converter produces one correctly-structured JSON file per row in the output directory.
6. Given an uploaded Excel file with invalid time values (e.g., `25:00`, `9:5`), the converter rejects the entire file and reports all errors without writing any JSON.
7. Given an uploaded Excel file with duplicate phone numbers, the converter rejects the file and reports the duplicates.
8. Given valid JSON output files, the API client successfully PUTs each configuration to the practice-time-window endpoint via Lambda invocation.
9. Given a presigned URL request, the URL expires after 5 minutes and returns 403 on subsequent use.
10. Given a token older than 7 days, DynamoDB TTL has removed it and the system treats it as invalid.
