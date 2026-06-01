# Feature Spec: `static-site-cloudfront`

## Summary

Terraform infrastructure for hosting the customer-facing `index.html` as a static site via an S3 bucket fronted by a CloudFront distribution. The distribution uses Origin Access Control (OAC) to keep the bucket private, enforces HTTPS-only access, serves `index.html` as the default root object, and attaches a `Referrer-Policy: no-referrer` response header to all responses to prevent token leakage via the Referer header.

---

## Requirements

1. A dedicated S3 bucket MUST be created for static site assets, named `${var.project_name}-site`.
2. The site bucket MUST block all public access (block public ACLs, block public policy, ignore public ACLs, restrict public buckets).
3. The site bucket MUST have a bucket policy granting `s3:GetObject` only to the CloudFront distribution via OAC.
4. A CloudFront Origin Access Control MUST be created with signing behavior `always` and origin type `s3`.
5. A CloudFront distribution MUST be created with the site bucket as its sole origin.
6. The distribution MUST set `default_root_object` to `index.html`.
7. The distribution MUST enforce HTTPS-only by setting the viewer protocol policy to `redirect-to-https`.
8. The distribution MUST attach a response headers policy that sets `Referrer-Policy: no-referrer` on all responses.
9. The distribution MUST use `PriceClass_100` (North America and Europe) to minimize cost.
10. Terraform MUST output the CloudFront distribution domain name and distribution ID.

---

## Constraints

- Infrastructure: Terraform only. AWS provider `~> 5.0`, region `us-east-1`.
- Resource naming: all resources prefixed with `var.project_name` where applicable.
- File location: `terraform/cloudfront.tf` (one resource type per file convention — this groups the tightly coupled static-site resources together).
- No custom domain or ACM certificate (pending stakeholder decision on vanity URL).
- No WAF or geo-restrictions at this stage.
- The S3 bucket does NOT enable static website hosting (CloudFront + OAC serves objects directly from S3 REST endpoint).
- `index.html` is deployed to the bucket root manually or via CI (deployment automation is out of scope).

---

## Out of Scope

- Custom domain name and ACM certificate (blocked on stakeholder decision).
- CI/CD pipeline for deploying `index.html` to the bucket.
- Cache invalidation automation.
- WAF, geo-restrictions, or rate limiting at the CloudFront layer.
- Any Lambda@Edge or CloudFront Functions.
- Changes to `index.html` content (covered by a separate spec).
- The existing data bucket (`bamboo-file-exchange-data`) — unchanged by this spec.

---

## Acceptance Criteria

1. **Bucket private:** Direct HTTP requests to the S3 bucket URL return 403 Forbidden.
2. **CloudFront serves content:** `curl -I https://{distribution_domain}/` returns HTTP 200 with `content-type: text/html`.
3. **Default root object:** Requesting `https://{distribution_domain}/` (no path) serves `index.html`.
4. **HTTPS enforced:** HTTP requests to the distribution are redirected to HTTPS (301/302).
5. **Referrer-Policy header:** Response headers include `referrer-policy: no-referrer`.
6. **OAC configured:** The CloudFront distribution's origin uses OAC (not OAI), and the S3 bucket policy references the distribution ARN.
7. **Terraform plan clean:** `terraform plan` shows no errors and creates the expected resources (bucket, public access block, bucket policy, OAC, response headers policy, distribution).
8. **Outputs present:** `terraform output` includes `cloudfront_domain_name` and `cloudfront_distribution_id`.

---

## Technical Notes

- **Terraform resource reference:**
  - `aws_s3_bucket.site`
  - `aws_s3_bucket_public_access_block.site`
  - `aws_s3_bucket_policy.site`
  - `aws_cloudfront_origin_access_control.site`
  - `aws_cloudfront_response_headers_policy.site`
  - `aws_cloudfront_distribution.site`
- **OAC bucket policy pattern:**
  ```json
  {
    "Effect": "Allow",
    "Principal": {"Service": "cloudfront.amazonaws.com"},
    "Action": "s3:GetObject",
    "Resource": "arn:aws:s3:::bamboo-file-exchange-site/*",
    "Condition": {
      "StringEquals": {
        "AWS:SourceArn": "<distribution ARN>"
      }
    }
  }
  ```
- **Response headers policy:** Use `aws_cloudfront_response_headers_policy` with a `security_headers_config` block containing `referrer_policy { override = true, referrer_policy = "no-referrer" }`.
- **Price class:** `PriceClass_100` is sufficient — customers are US-based healthcare practices.
- **Existing patterns:** Follow `terraform/s3.tf` for bucket + public access block style. Follow `terraform/variables.tf` for `var.project_name` usage.
- **Deployment:** After `terraform apply`, upload `index.html` with: `aws s3 cp index.html s3://bamboo-file-exchange-site/index.html --content-type text/html`.
