# Customer File Exchange Portal — Design Summary

## Overview

A serverless web application that allows customers to download an Excel template, fill it out with their practice time window configuration, and upload the completed file. Customers access the page via a unique, time-limited URL sent to them by email.

## Architecture

| Component | Service | Purpose |
|-----------|---------|---------|
| Static site hosting | S3 + CloudFront | Serves `index.html` to customers |
| API | API Gateway + Lambda | Token validation, presigned URL generation |
| Token storage | DynamoDB | Stores tokens with TTL (7-day expiry) |
| File storage | S3 | Template file + customer uploads |
| Email delivery | SendGrid | Sends unique URL to customers |
| Excel → JSON conversion | Lambda (S3 trigger) | Converts uploaded .xlsx to JSON |
| Infrastructure | Terraform | All resources defined as IaC |

## Customer Flow

1. Admin generates a token and sends an email (via SendGrid) containing a unique URL
2. Customer clicks the link → page loads from CloudFront/S3
3. Page validates the token on load (`GET /validate?token=...`)
   - Invalid/expired → error message, page disabled
   - Valid → page enabled
4. Customer clicks **Download Template** → `GET /template?token=...` → Lambda returns a presigned S3 GET URL (5-min expiry) → file downloads
5. Customer fills out the Excel template offline
6. Customer uploads completed file → `GET /upload-url?token=...&filename=...` → Lambda returns a presigned S3 PUT URL (5-min expiry) → browser PUTs file directly to S3
7. Page confirms successful upload
8. S3 event triggers conversion Lambda → Excel converted to JSON and saved to S3
9. Re-uploads are allowed as long as the token is still valid (within 7 days)

## Security

| Measure | Detail |
|---------|--------|
| Token format | 64-character URL-safe random string (`secrets.token_urlsafe(48)`) |
| Token expiry | 7 days (DynamoDB TTL auto-deletes) |
| Presigned URLs | 5-minute expiry |
| Transport | HTTPS via CloudFront |
| Encryption at rest | S3 AES-256 |
| Referrer leakage | `Referrer-Policy: no-referrer` header |

## Lambda Functions

| Function | Trigger | Input | Output |
|----------|---------|-------|--------|
| `validate_token` | API Gateway `GET /validate` | `?token=` | 200 (valid) or 403 (invalid/expired) |
| `get_template` | API Gateway `GET /template` | `?token=` | `{ downloadUrl }` |
| `get_upload_url` | API Gateway `GET /upload-url` | `?token=&filename=` | `{ uploadUrl }` |
| `convert_excel` | S3 ObjectCreated (`uploads/`) | S3 event | Writes JSON to `json/{token}/` |

## DynamoDB Schema — Tokens Table

| Attribute | Type | Description |
|-----------|------|-------------|
| `token` | String (PK) | 64-char random token |
| `customer_name` | String | Organization name |
| `email` | String | Customer email address |
| `created_at` | String | ISO 8601 timestamp |
| `ttl` | Number | Unix timestamp (created_at + 7 days) |

## S3 Bucket Structure

```
data-bucket/
├── template/
│   └── practice_time_window_template.xlsx
├── uploads/
│   └── {token}/
│       └── {filename}.xlsx
└── json/
    └── {token}/
        └── {filename}.json
```

## Frontend

- Single `index.html` page styled to match Bamboo Health branding
- Dark navy header, teal accents, Inter font, card-based layout
- Sections: Welcome (3-step process), Download/Upload card, Instructions (column guide, time windows, timezones, pre-submit checklist)
- Token read from URL query parameter (`?token=...`)
- Validates token on page load; disables UI if invalid/expired

## Status

| Item | Status |
|------|--------|
| Frontend (`index.html`) | ✅ Built |
| Lambda: `get_template` | ✅ Built |
| Lambda: `get_upload_url` | ✅ Built |
| Lambda: `validate_token` | 🔲 To do |
| Lambda: `convert_excel` | 🔲 To do (reference: `excel2json/convert.py`) |
| Terraform | 🔲 To do |
| Token generation script | ✅ Built (CLI, SendGrid integration pending) |
| SendGrid integration | 🔲 To do (credentials pending) |
| Admin dashboard | 🔲 Future |

## Open Decisions

- Custom domain for CloudFront distribution
- SendGrid sender address and email template design
- Notification to admin on successful upload (SNS? Slack?)
- CloudWatch alarms / monitoring
