# Next Steps

## To build (in order):

1. **Terraform — DynamoDB table**
   - Tokens table with `token` as partition key, TTL enabled on `ttl` attribute

2. **Terraform — S3 bucket**
   - Data bucket (template + uploads + json output), encryption, CORS for presigned URLs

3. **Lambda: `validate_token`**
   - `GET /validate?token=...` → checks DynamoDB, returns 200 or 403
   - Update `index.html` to call this on page load

4. **Terraform — API Gateway**
   - HTTP API with three routes: `/validate`, `/template`, `/upload-url`
   - Wire to Lambda functions

5. **Lambda: `convert_excel`**
   - Triggered by S3 ObjectCreated on `uploads/` prefix
   - Port logic from `excel2json/convert.py`
   - Output JSON to `json/{token}/`

6. **Terraform — S3 event → Lambda trigger**

7. **Terraform — Static site bucket + CloudFront**
   - Host `index.html`
   - Set `Referrer-Policy: no-referrer` header

8. **Update `index.html`** — set `API_BASE` to deployed API Gateway URL

9. **SendGrid integration** — once credentials are available

10. **Deploy & test end-to-end**
