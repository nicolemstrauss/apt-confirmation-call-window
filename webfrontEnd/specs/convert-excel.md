# Feature Spec: `convert-excel`

## Summary

An S3-triggered AWS Lambda function that automatically converts uploaded Excel workbooks into per-practice JSON configuration files. When a customer uploads a completed `.xlsx` file to the `uploads/` prefix of the data bucket, this function downloads the file, parses the "config" sheet using openpyxl, validates time-window data, and writes one JSON file per phone number to `json/{token}/{phone}.json` in the same bucket. If conversion fails, it writes error details to `json/{token}/_errors.json`.

---

## Requirements

1. The Lambda MUST trigger on S3 `ObjectCreated` events for objects matching the prefix `uploads/` in the `bamboo-file-exchange-data` bucket.
2. The Lambda MUST download the uploaded `.xlsx` file from S3 into `/tmp` for processing.
3. The Lambda MUST read the "config" sheet from the workbook and extract rows with columns: `phone`, `tz`, `max_days`, `attempts_per_day`, day-of-week time windows (Monday–Sunday), `alternate_ivr_behavior`, and `alternate_ivr_description`.
4. The Lambda MUST validate all time values against 24-hour military format (`HH:MM`, range `00:00`–`23:59`).
5. The Lambda MUST validate time-range format as `HH:MM-HH:MM`, supporting comma-separated multiple ranges per day cell.
6. The Lambda MUST detect and report duplicate phone numbers as errors.
7. On successful conversion, the Lambda MUST write one JSON file per phone number to `json/{token}/{phone}.json` in the same bucket, where `{token}` is extracted from the S3 key path (`uploads/{token}/{filename}`).
8. Each JSON output file MUST conform to this structure:
   ```json
   {
     "tz": "string",
     "max_days": integer,
     "attempts_per_day": integer,
     "windows": [{"dow": integer, "start": "HH:MM", "end": "HH:MM"}],
     "alternate_ivr_behavior": boolean,
     "alternate_ivr_description": "string (optional)"
   }
   ```
9. If any validation errors occur, the Lambda MUST NOT write individual JSON files and MUST instead write all errors to `json/{token}/_errors.json`.
10. The `_errors.json` file MUST contain a JSON object with at minimum: `{"source_key": "string", "errors": ["string", ...], "timestamp": "ISO 8601"}`.
11. The Lambda MUST use Python 3.12 runtime.
12. The Lambda MUST have `openpyxl` available via a Lambda layer or bundled in the deployment package.
13. The Lambda MUST log the S3 key being processed and the outcome (success with file count, or failure) to CloudWatch.

---

## Constraints

- Runtime: Python 3.12, consistent with existing Lambdas in this project.
- Dependency: `openpyxl` (pinned version) provided via Lambda layer or bundled zip.
- Memory: allocate sufficient memory for workbook parsing (minimum 256 MB recommended for openpyxl).
- Timeout: 60 seconds maximum (workbooks are small, single-sheet).
- IAM permissions: `s3:GetObject` on `uploads/*`, `s3:PutObject` on `json/*`, CloudWatch Logs write.
- Infrastructure: Terraform only (no SAM/CDK). Resource names prefixed with `var.project_name`.
- Entry point: `handler(event, context)` following existing Lambda conventions.
- Environment variable: `DATA_BUCKET` for the bucket name (or derive from the event record).
- The phone number in the output filename MUST have the leading `+` stripped (e.g., `12125551234.json`).
- `/tmp` storage limit: 512 MB (default Lambda ephemeral storage; sufficient for this use case).

---

## Out of Scope

- Terraform for the S3 event notification and Lambda resource (covered by a separate infra spec).
- Notification to admins on success or failure (pending stakeholder decision).
- Re-upload/versioning behavior (pending stakeholder decision).
- Processing non-`.xlsx` files or files outside the `uploads/` prefix.
- Retry logic beyond Lambda's built-in retry behavior for async invocations.
- SendGrid integration or any email sending.
- Frontend changes.

---

## Acceptance Criteria

1. **Happy path:** Upload a valid `.xlsx` with 3 practice rows → Lambda produces exactly 3 JSON files at `json/{token}/{phone}.json` with correct content matching the reference `convert.py` output.
2. **Invalid time format:** Upload a workbook with `25:00` in a time cell → Lambda writes `_errors.json` containing the validation error message and does NOT write any per-practice JSON files.
3. **Invalid range format:** Upload a workbook with `08:00-` (incomplete range) → `_errors.json` is written with the appropriate error.
4. **Duplicate phone:** Upload a workbook with two rows sharing the same phone number → `_errors.json` reports the duplicate.
5. **Empty workbook:** Upload a workbook with only headers (no data rows) → `_errors.json` is written indicating no practice rows found.
6. **Output path correctness:** For an upload at `uploads/abc123/file.xlsx` with phone `+12125551234`, the output lands at `json/abc123/12125551234.json`.
7. **Idempotency:** Re-uploading the same file overwrites previous JSON output without leaving orphan files from a prior run (note: orphan cleanup is best-effort; new output overwrites matching keys).
8. **CloudWatch logging:** Each invocation produces at least one log entry with the source S3 key and the result (success + count, or error).

---

## Technical Notes

- **Reference implementation:** `excel2json/convert.py` contains the parsing and validation logic to port. Key functions: `read_excel()`, `parse_windows()`, `validate_time()`.
- **openpyxl version:** Pin to `3.1.x` (latest stable as of project start). Bundle via `pip install openpyxl -t ./package` into the deployment zip, or create a shared Lambda layer.
- **S3 event structure:** The token is extracted from the object key: `event['Records'][0]['s3']['object']['key']` → split on `/` → index 1 is the token.
- **Existing Lambda pattern:** See `lambdas/validate_token/handler.py` for the project's conventions (env vars, response helpers, handler signature).
- **Day-of-week mapping:** Monday=0 through Sunday=6 (matching `convert.py`'s `DAY_COLUMNS`).
- **JSON serialization:** Use `json.dumps(body, indent=2)` for readability, matching reference output.
- **Deployment location:** `lambdas/convert_excel/handler.py` following existing directory structure.
