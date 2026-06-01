Resume prompt for Kiro CLI — Customer File Exchange Project
=============================================================

Use this to resume work. Paste it as your first message in a new session.

---

I'm resuming work on a customer file exchange web application in /Users/nstrauss/webfrontEnd.

**What it does:** Customers receive a unique URL via email. The URL takes them to a webpage where they can download an Excel template (practice time window configuration), fill it out, and upload the completed file.

**What's been built:**
- `index.html` — Customer-facing page (Bamboo Health branded). Has download button, drag-and-drop upload, inline instructions, token validation on page load. Styled with dark navy/teal theme.
- `lambdas/get_template/handler.py` — Lambda that validates token in DynamoDB, returns a 5-min presigned S3 download URL.
- `lambdas/get_upload_url/handler.py` — Lambda that validates token in DynamoDB, returns a 5-min presigned S3 PUT URL. Uploads go to `uploads/{token}/{filename}`.
- `scripts/generate_token.py` — CLI script to generate 64-char random tokens and store in DynamoDB with customer_name, email, created_at, and 7-day TTL.
- `docs/design_summary.md` — Full architecture doc (Confluence-ready).
- `docs/next_steps.md` — Ordered list of remaining work.

**Architecture:** S3 (static site + data), CloudFront, API Gateway, Lambda (Python), DynamoDB (tokens table with TTL), SendGrid (email, credentials pending). All infrastructure will be Terraform (not SAM).

**Security:** 64-char URL-safe tokens, 7-day TTL, 5-minute presigned URLs, HTTPS via CloudFront, S3 AES-256 encryption.

**What's next (in order):**
1. Terraform — DynamoDB tokens table (partition key: `token`, TTL on `ttl` attribute)
2. Terraform — S3 data bucket (template + uploads + json output, encryption, CORS)
3. Lambda: `validate_token` (GET /validate?token=...) + update index.html to call it on page load
4. Terraform — API Gateway HTTP API with routes: /validate, /template, /upload-url
5. Lambda: `convert_excel` (S3 trigger on uploads/ prefix, ports logic from /Users/nstrauss/excel2json/convert.py, outputs JSON to json/{token}/)
6. Terraform — S3 event trigger for convert Lambda
7. Terraform — Static site bucket + CloudFront with Referrer-Policy: no-referrer
8. Update index.html API_BASE with deployed API Gateway URL
9. SendGrid integration (credentials pending)
10. End-to-end test

**Reference:** The Excel template and conversion logic live in /Users/nstrauss/excel2json/ (convert.py, practice_time_window_template.xlsx).

Please read `docs/next_steps.md` and pick up where we left off.
