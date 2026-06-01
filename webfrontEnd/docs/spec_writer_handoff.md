# Customer File Exchange Portal — Spec Writer Handoff

## Project Summary

A serverless web application for Bamboo Health that lets customers download an Excel template, fill in their practice time window configuration, and upload the completed file. Customers access the page via a unique, time-limited URL sent by email. Uploaded Excel files are automatically converted to JSON for downstream consumption.

---

## Business Context

- **Who uses it:** External customers (healthcare practices) who need to configure call scheduling windows
- **How they access it:** A unique URL emailed to them (e.g., `https://portal.bamboohealth.com?token=abc123...`)
- **What they do:** Download a pre-formatted Excel template → fill it out offline → upload the completed file
- **What happens after:** The system converts the Excel to per-practice JSON files automatically
- **Admin workflow:** Internal staff generate tokens via CLI script, email goes out via SendGrid

---

## Architecture

| Component | Service | Status |
|-----------|---------|--------|
| Static site | S3 + CloudFront | Terraform written, not deployed |
| API | API Gateway HTTP API + Lambda (Python 3.12) | Terraform written, not deployed |
| Token storage | DynamoDB (PAY_PER_REQUEST, TTL) | Terraform written, not deployed |
| File storage | S3 (AES-256, CORS, public access blocked) | Terraform written, not deployed |
| Email delivery | SendGrid | Not started (credentials pending) |
| Excel → JSON | Lambda (S3 trigger) | Not started |
| Infrastructure | Terraform (not SAM) | Partially written |

---

## What's Been Built

### Frontend — `index.html`
- Single-page customer-facing UI, Bamboo Health branded (dark navy/teal, Inter font)
- Download button → calls `GET /template?token=...` → redirects to presigned S3 URL
- Drag-and-drop upload → calls `GET /upload-url?token=...&filename=...` → PUTs file to presigned S3 URL
- Token validation on page load (currently commented out for local preview)
- Inline instructions: column guide, time window format, timezone list, pre-submit checklist
- No frameworks — vanilla HTML/CSS/JS

### Lambdas (Python 3.12)
All follow the same pattern: read `TOKENS_TABLE` env var, validate token in DynamoDB, return JSON with CORS headers.

| Function | Path | Behavior |
|----------|------|----------|
| `validate_token` | `lambdas/validate_token/handler.py` | Returns 200 `{valid, customer}` or 403 |
| `get_template` | `lambdas/get_template/handler.py` | Returns `{downloadUrl}` (5-min presigned GET) |
| `get_upload_url` | `lambdas/get_upload_url/handler.py` | Returns `{uploadUrl}` (5-min presigned PUT to `uploads/{token}/{filename}`) |

### Terraform — `terraform/`
| File | Resources |
|------|-----------|
| `main.tf` | AWS provider (us-east-1) |
| `variables.tf` | `aws_region`, `project_name` ("bamboo-file-exchange"), `template_key` |
| `dynamodb.tf` | Tokens table (PK: `token`, TTL on `ttl`) |
| `s3.tf` | Data bucket (AES-256, public access blocked, CORS for GET/PUT) |
| `api_gateway.tf` | IAM role, 3 Lambda functions, HTTP API, routes (`/validate`, `/template`, `/upload-url`), permissions, outputs |

### Scripts
| Script | Purpose |
|--------|---------|
| `scripts/generate_token.py` | CLI: generates 64-char token, stores in DynamoDB with customer name |

### Excel Template
- `practice_time_window_template.xlsx` — sheet-protected (no column insertion/deletion), data validation dropdowns for timezone, input prompts on day columns
- Created by `excel2json/create_template.py`

### Reference: Excel → JSON Conversion
- `excel2json/convert.py` — reads the "config" sheet, validates 24-hour time formats, outputs one JSON file per phone number
- JSON structure per practice:
```json
{
  "tz": "America/Chicago",
  "max_days": 2,
  "attempts_per_day": 1,
  "windows": [{"dow": 0, "start": "08:00", "end": "12:00"}, ...],
  "alternate_ivr_behavior": true,
  "alternate_ivr_description": "Wait for a live agent."
}
```

---

## What Remains (Ordered)

### 5. Lambda: `convert_excel` (S3-triggered)
- Trigger: S3 ObjectCreated on `uploads/` prefix in data bucket
- Downloads the uploaded .xlsx from S3
- Ports logic from `excel2json/convert.py` (uses openpyxl)
- Outputs JSON files to `json/{token}/{phone}.json` in the same bucket
- Needs a Lambda layer or bundled dependency for `openpyxl`
- Error handling: if conversion fails, write error details to `json/{token}/_errors.json`

### 6. Terraform: S3 event → Lambda trigger
- S3 bucket notification on `uploads/` prefix → invoke convert_excel Lambda
- Lambda permission for S3 to invoke

### 7. Terraform: Static site bucket + CloudFront
- Separate S3 bucket for `index.html` (or same bucket with different prefix)
- CloudFront distribution with:
  - `Referrer-Policy: no-referrer` response header
  - HTTPS only
  - Default root object: `index.html`
- Origin access control (OAC) for S3

### 8. Update `index.html`
- Set `API_BASE` to the deployed API Gateway endpoint URL
- Re-enable token validation (currently commented out)

### 9. SendGrid Integration
- Credentials pending from business team
- Email template with: customer name, unique URL, brief instructions
- Triggered by admin (extend `generate_token.py` or separate script)

### 10. End-to-End Testing
- Generate token → receive email → click link → validate → download → fill → upload → verify JSON output

---

## Security Model

| Control | Implementation |
|---------|---------------|
| Token entropy | 64-char URL-safe (`secrets.token_urlsafe(48)`) |
| Token expiry | 7-day TTL (DynamoDB auto-deletes) |
| Presigned URL expiry | 5 minutes |
| Transport | HTTPS via CloudFront |
| Encryption at rest | S3 AES-256 |
| Referrer leakage | `Referrer-Policy: no-referrer` |
| Public access | S3 public access blocked; CloudFront OAC |
| No auth beyond token | Intentional — customers don't have accounts |

---

## DynamoDB Schema

**Table:** `bamboo-file-exchange-tokens`

| Attribute | Type | Notes |
|-----------|------|-------|
| `token` | String | Partition key |
| `customer` | String | Organization name |
| `email` | String | Customer email |
| `created_at` | String | ISO 8601 |
| `ttl` | Number | Unix epoch (created_at + 7 days) |

---

## S3 Bucket Layout

```
bamboo-file-exchange-data/
├── templates/
│   └── practice_time_window_template.xlsx
├── uploads/
│   └── {token}/
│       └── {filename}.xlsx
└── json/
    └── {token}/
        └── {phone}.json
```

---

## Open Decisions (Need Stakeholder Input)

1. **Custom domain** — Will the portal have a vanity URL (e.g., `portal.bamboohealth.com`)?
2. **SendGrid sender** — What email address and display name?
3. **Upload notification** — Should admins be notified on successful upload? (SNS, Slack, email?)
4. **Re-upload behavior** — Overwrite previous JSON output, or version it?
5. **Error notification** — If Excel conversion fails, who gets notified?
6. **Rate limiting** — Any concern about token brute-forcing? (64-char token makes this impractical, but API Gateway throttling is cheap insurance)
7. **Multi-region** — Single region (us-east-1) acceptable?

---

## File Map

```
webfrontEnd/
├── index.html                          # Customer-facing page
├── practice_time_window_template.xlsx  # Local copy for preview
├── docs/
│   ├── design_summary.md              # Architecture doc
│   ├── next_steps.md                  # Ordered task list
│   └── spec_writer_handoff.md         # THIS FILE
├── lambdas/
│   ├── validate_token/handler.py      # GET /validate
│   ├── get_template/handler.py        # GET /template
│   └── get_upload_url/handler.py      # GET /upload-url
├── terraform/
│   ├── main.tf                        # Provider
│   ├── variables.tf                   # Config variables
│   ├── dynamodb.tf                    # Tokens table
│   ├── s3.tf                          # Data bucket
│   └── api_gateway.tf                 # API + Lambdas + routes
└── scripts/
    └── generate_token.py              # CLI token generator

excel2json/                            # Reference repo (separate)
├── convert.py                         # Conversion logic to port
├── create_template.py                 # Template generator
├── practice_time_window_template.xlsx # Source template
└── customer_instructions.md           # Customer-facing docs
```

---

## Conventions

- **Naming:** kebab-case for feature names, snake_case for Python
- **Lambda pattern:** env vars for config, `handler(event, context)` entry point, shared `response()` helper
- **Terraform:** one resource type per file, `var.project_name` prefix on all resource names
- **No frameworks:** vanilla JS frontend, no build step
- **Infrastructure:** Terraform only (no SAM, no CDK, no CloudFormation)
