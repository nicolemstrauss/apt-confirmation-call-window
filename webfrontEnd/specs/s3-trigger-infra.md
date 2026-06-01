# Feature Spec: `s3-trigger-infra`

## Summary

Terraform infrastructure to deploy the `convert_excel` Lambda function and wire it to the existing S3 data bucket via an event notification. When an object is created under the `uploads/` prefix, S3 invokes the Lambda to convert the Excel file to JSON. This spec covers the Lambda resource definition (with openpyxl bundled), the S3 bucket notification configuration, the Lambda permission granting S3 invoke access, and any IAM policy additions required.

---

## Requirements

1. A Terraform `aws_lambda_function` resource MUST be defined for `convert_excel` using Python 3.12 runtime, with function name `${var.project_name}-convert-excel`.
2. The Lambda deployment package MUST include `openpyxl` and its dependencies bundled alongside `handler.py` (built via `archive_file` data source from `lambdas/convert_excel/`).
3. The Lambda MUST be configured with at least 256 MB memory and 60-second timeout.
4. The Lambda MUST use the existing `aws_iam_role.lambda` IAM role defined in `api_gateway.tf`.
5. The Lambda MUST have environment variable `DATA_BUCKET` set to the data bucket name (`aws_s3_bucket.data.id`).
6. An `aws_s3_bucket_notification` resource MUST be defined on the data bucket that triggers the `convert_excel` Lambda on `s3:ObjectCreated:*` events filtered to the `uploads/` prefix.
7. An `aws_lambda_permission` resource MUST grant the S3 service principal (`s3.amazonaws.com`) permission to invoke the `convert_excel` Lambda, scoped to the data bucket ARN as `source_arn`.
8. The existing IAM role policy MUST already permit `s3:GetObject` and `s3:PutObject` on `${aws_s3_bucket.data.arn}/*` and CloudWatch Logs write — no new IAM statements are required unless the existing policy is insufficient.
9. All resource names MUST be prefixed with `var.project_name` consistent with existing conventions.
10. The Terraform MUST be placed in a new file `terraform/convert_excel.tf` following the project convention of one resource type per file.

---

## Constraints

- Infrastructure tool: Terraform only (no SAM, CDK, or CloudFormation).
- Region: `us-east-1` (inherited from `main.tf` provider).
- The Lambda deployment zip MUST be built from the `lambdas/convert_excel/` directory, which contains `handler.py` and a pre-installed `openpyxl` package directory (developer runs `pip install openpyxl -t lambdas/convert_excel/` before `terraform apply`).
- The `archive_file` data source MUST use `type = "zip"` with `source_dir` (not `source_file`) since the package includes dependencies.
- The S3 bucket notification MUST NOT interfere with any future notifications on other prefixes.
- The Lambda permission `source_arn` MUST be the bucket ARN (not `/*`) per AWS requirements for S3→Lambda permissions.

---

## Out of Scope

- The `convert_excel` Lambda application code (covered by the `convert-excel` spec).
- Creating a shared Lambda layer for openpyxl (bundling in the zip is the chosen approach).
- Dead-letter queue or failure notifications (pending stakeholder decision).
- CloudFront, static site, or any frontend infrastructure.
- Additional S3 event notifications for other prefixes.
- SNS/SQS fan-out patterns.

---

## Acceptance Criteria

1. **Terraform validates:** `terraform validate` passes with no errors after adding `terraform/convert_excel.tf`.
2. **Terraform plans cleanly:** `terraform plan` shows exactly 3 new resources: `aws_lambda_function.convert_excel`, `aws_s3_bucket_notification.uploads`, `aws_lambda_permission.convert_excel_s3`.
3. **Lambda config correct:** The planned Lambda has runtime `python3.12`, memory 256 MB, timeout 60s, handler `handler.handler`, and environment variable `DATA_BUCKET`.
4. **S3 notification scoped:** The bucket notification filters to prefix `uploads/` and event type `s3:ObjectCreated:*`.
5. **Permission scoped:** The Lambda permission grants `lambda:InvokeFunction` to principal `s3.amazonaws.com` with `source_arn` equal to the data bucket ARN.
6. **No IAM drift:** `terraform plan` shows no changes to the existing `aws_iam_role_policy.lambda` resource (existing policy already covers required S3 and logs permissions).
7. **Integration test:** After `terraform apply`, uploading a `.xlsx` to `uploads/{token}/test.xlsx` in the data bucket triggers the `convert_excel` Lambda (visible in CloudWatch Logs).

---

## Technical Notes

- **Existing IAM coverage:** The current `aws_iam_role_policy.lambda` already grants `s3:GetObject` and `s3:PutObject` on `${aws_s3_bucket.data.arn}/*` plus CloudWatch Logs. No additions needed.
- **Deployment package build:** Before running Terraform, the developer must install dependencies into the Lambda directory:
  ```bash
  pip install openpyxl==3.1.5 -t lambdas/convert_excel/
  ```
- **archive_file with source_dir:** Unlike the existing Lambdas (which use `source_file` for single-file zips), this Lambda uses `source_dir` to capture `handler.py` plus the `openpyxl` package tree.
- **S3 notification dependency:** Terraform requires the `aws_lambda_permission` to exist before the `aws_s3_bucket_notification` can successfully invoke the function. Use `depends_on` if Terraform doesn't infer the dependency.
- **File location:** `terraform/convert_excel.tf` — contains the Lambda function, Lambda permission, and S3 bucket notification resources together since they form a single logical unit.
- **Reference:** Existing Lambda pattern in `terraform/api_gateway.tf` for naming, role reference, and `archive_file` usage.
