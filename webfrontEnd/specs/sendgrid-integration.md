# Feature Spec: SendGrid Email Integration

## Summary

Extend the existing `generate_token.py` CLI script to send customers their unique portal URL via SendGrid immediately after token creation. When an admin generates a token, the script stores it in DynamoDB (existing behavior), then sends a branded email containing the customer's name, unique URL, and brief instructions. This depends on SendGrid API credentials that are pending from the business team.

---

## Requirements

1. The script SHALL accept a `--email` argument specifying the customer's email address.
2. The script SHALL store the customer email in the DynamoDB token record (attribute: `email`).
3. The script SHALL send an email to the customer via the SendGrid v3 API after successful token creation.
4. The script SHALL use a SendGrid API key provided via the `SENDGRID_API_KEY` environment variable.
5. The script SHALL accept a `--send-email` flag (default: true) to allow token creation without sending email (e.g., `--no-send-email` for testing).
6. The script SHALL exit with a non-zero code and print a descriptive error if email delivery fails (non-2xx response from SendGrid).
7. The script SHALL NOT delete or roll back the DynamoDB token record if email delivery fails; instead it SHALL print the generated URL to stdout so the admin can manually share it.
8. The script SHALL log the SendGrid response status code and message ID on success.
9. The email SHALL be sent from a configurable sender address via `--from-email` argument (default read from `SENDGRID_FROM_EMAIL` environment variable).
10. The email SHALL use a SendGrid dynamic template identified by a template ID provided via `SENDGRID_TEMPLATE_ID` environment variable.

---

## Email Template Requirements

The SendGrid dynamic template SHALL include the following content and structure:

| Element | Details |
|---------|---------|
| Subject line | "Your Bamboo Health File Exchange Portal Link" |
| Greeting | "Hello {{customer_name}}," |
| Body | Brief explanation: they've been given access to upload their practice time window configuration |
| CTA button | "Access Your Portal" linking to the unique URL |
| URL fallback | Plain-text URL below the button for email clients that don't render buttons |
| Expiry notice | "This link expires in 7 days." |
| Instructions | 1) Click link 2) Download the Excel template 3) Fill it out 4) Upload the completed file |
| Footer | Bamboo Health branding, "Do not share this link" notice |

Template dynamic variables passed from the script:

- `customer_name` — from `--customer` argument
- `portal_url` — the full unique URL (`{base_url}?token={token}`)
- `expiry_days` — hardcoded to `7`

---

## Error Handling

| Scenario | Behavior |
|----------|----------|
| `SENDGRID_API_KEY` not set and `--send-email` is active | Exit with error before token creation |
| `SENDGRID_TEMPLATE_ID` not set and `--send-email` is active | Exit with error before token creation |
| `--email` not provided and `--send-email` is active | Exit with error (argparse validation) |
| DynamoDB `put_item` fails | Exit with error, no email sent |
| SendGrid returns 4xx/5xx | Print error details, print the URL to stdout, exit code 1 |
| Network timeout to SendGrid | Retry once after 3 seconds; if still failing, treat as delivery failure (above) |

---

## Out of Scope

- SendGrid account setup and credential provisioning (owned by business team)
- Designing the visual HTML template in the SendGrid UI (design team)
- Bounce/unsubscribe webhook handling
- Admin notification on successful customer upload
- Batch token generation / bulk email sends
- Custom domain DNS configuration for SendGrid sender authentication

---

## Dependencies

| Dependency | Status | Notes |
|------------|--------|-------|
| SendGrid API key | **Pending** — awaiting business team | Required before any integration testing |
| SendGrid dynamic template | **Not created** | Must be built in SendGrid UI matching template requirements above |
| Sender email address | **Pending** — open decision | Needs stakeholder decision on from address and display name |
| `sendgrid` Python package | Available (`pip install sendgrid`) | Pin to exact version in requirements |
| Portal base URL | **Pending** — depends on CloudFront deployment and custom domain decision | Use `--base-url` argument (already exists) |

---

## Technical Notes

- **Existing script:** `scripts/generate_token.py` — currently generates token, stores in DynamoDB, prints URL. Extend in-place.
- **Python SDK:** Use the official `sendgrid` Python library (wraps the v3 Mail Send API).
- **DynamoDB schema:** The `email` attribute already exists in the table schema per the handoff doc; the current script just doesn't populate it.
- **Lambda alternative:** If the team later wants automated email on token creation (e.g., via a DynamoDB Stream trigger), this can be extracted into a Lambda. For now, the CLI script is the admin workflow.
- **Conventions:** snake_case Python, `argparse` for CLI, environment variables for secrets.

---

## Acceptance Criteria

1. Running `python generate_token.py --table <table> --customer "Acme Health" --email customer@example.com --base-url https://portal.bamboohealth.com` creates a DynamoDB record with `token`, `customer`, `email`, `created_at`, and `ttl` attributes, and sends an email via SendGrid.
2. The sent email contains the correct unique URL (`https://portal.bamboohealth.com?token=<generated_token>`).
3. Running with `--no-send-email` creates the token and prints the URL without calling SendGrid.
4. When `SENDGRID_API_KEY` is unset and `--send-email` is active, the script exits with a clear error message before writing to DynamoDB.
5. When SendGrid returns a non-2xx response, the script prints the error, prints the generated URL, and exits with code 1.
6. The DynamoDB record persists even if email delivery fails.
7. The script prints the SendGrid message ID on successful delivery.
