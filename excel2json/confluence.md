# excel2json — Practice Time Window Config Generator

## Purpose

This project converts a human-friendly Excel spreadsheet into per-practice JSON files that conform to the `practice-time-window` DynamoDB configuration schema. The generated JSON files are designed to be uploaded via the API:

```
PUT /config/practice-time-window/%2B{phone_number}
Content-Type: application/json
```

---

## Project Location

```
/Users/nstrauss/excel2json/
```

## Directory Structure

```
excel2json/
├── create_template.py              # Generates a blank Excel template with headers and one example row
├── convert.py                      # Reads a populated Excel workbook, outputs one JSON file per practice (with military time validation)
├── generate_instructions_pdf.py    # Generates customer_instructions.pdf
├── requirements.txt                # Python dependency: openpyxl==3.1.5
├── practice_time_window_template.xlsx  # Generated blank template (with tz dropdown + day column prompts)
├── sample_3_practices.xlsx         # Sample workbook with 3 example practices
├── customer_instructions.md        # Customer-facing instructions (markdown)
├── customer_instructions.pdf       # Customer-facing instructions (PDF)
└── json/                           # Output directory for generated JSON files
```

---

## Excel Format

Single sheet named `config`. One row per practice. Columns:

| Column | Type | Description |
|---|---|---|
| `phone` | string | Practice phone number in E.164 format (e.g. `+12143309221`) |
| `tz` | string | IANA timezone (e.g. `America/Chicago`) |
| `max_days` | integer | Maximum number of days to attempt |
| `attempts_per_day` | integer | Number of attempts per day |
| `Monday` through `Sunday` | string | Comma-separated time ranges in `HH:MM-HH:MM` format. Leave blank for no windows on that day. |
| `alternate_ivr_behavior` | boolean | `TRUE` or `FALSE`. Omitted from JSON if falsy. |
| `alternate_ivr_description` | string | Free text description of IVR behavior. Omitted from JSON if blank. |

### Day column examples

| Value | Meaning |
|---|---|
| `08:00-12:00, 13:00-17:00` | Two windows on that day |
| `09:00-11:30` | Single window |
| *(empty)* | No windows for that day |

### Day-to-dow mapping

Monday=0, Tuesday=1, Wednesday=2, Thursday=3, Friday=4, Saturday=5, Sunday=6

### Template features

- Timezone column has a dropdown with: America/New_York, America/Chicago, America/Denver, America/Los_Angeles, America/Phoenix
- Day columns (Monday–Sunday) show an input prompt reminding users to use 24-hour `HH:MM-HH:MM` format

### Validation

The converter (`convert.py`) validates all time values before generating JSON. Invalid entries (e.g. `8:00`, `1:00 PM`) produce a clear error with the phone number, day, and bad value. No files are written until all rows pass.

---

## Customer Deliverables

When sending a template to a customer, include:

1. The Excel template (renamed to `[OrgName]Template.xlsx`)
2. The instructions PDF (`customer_instructions.pdf`)

Customers should return the completed file named: `OrgName_YYYY-MM-DD.xlsx`

---

## Target JSON Structure

Each practice row produces a JSON file like:

```json
{
  "tz": "America/Chicago",
  "max_days": 2,
  "attempts_per_day": 1,
  "windows": [
    { "dow": 0, "start": "08:00", "end": "12:00" },
    { "dow": 0, "start": "13:00", "end": "17:00" },
    { "dow": 1, "start": "08:00", "end": "12:00" },
    { "dow": 1, "start": "13:00", "end": "17:00" }
  ],
  "alternate_ivr_behavior": true,
  "alternate_ivr_description": "When encountering IVR, do not engage with the IVR system and instead wait for a human to answer."
}
```

Output files are named `{phone_without_plus}.json` (e.g. `12143309221.json`).

---

## Usage

### 1. Install dependencies

```bash
pip3 install -r requirements.txt
```

### 2. Generate a blank template

```bash
python3 create_template.py
# Creates: practice_time_window_template.xlsx
```

### 3. Fill in the template

Open the Excel file, add one row per practice with phone number, timezone, config fields, and time windows in the day columns.

### 4. Convert to JSON

```bash
python3 convert.py <your_workbook.xlsx> -o json
# Outputs one .json file per practice row into the json/ directory
```

### 5. Upload to API

Each generated JSON file is the request body for:

```
PUT /config/practice-time-window/%2B{phone_number}
Content-Type: application/json
```

---

## Kiro Session Prompt

Use the following to resume work on this project in a new Kiro session:

> I have a Python project at `/Users/nstrauss/excel2json/` that converts Excel spreadsheets into JSON config files for the `practice-time-window` DynamoDB table. The Excel format uses a single sheet named `config` with one row per practice — columns for phone, tz (dropdown), max_days, attempts_per_day, day-of-week time windows (Monday–Sunday as comma-separated `HH:MM-HH:MM` ranges with input prompts), alternate_ivr_behavior, and alternate_ivr_description. The converter (`convert.py`) reads the workbook, validates all times are in 24-hour military format, and outputs one JSON file per practice. `create_template.py` generates a blank template with tz dropdown and day column prompts. `generate_instructions_pdf.py` creates a customer-facing PDF with instructions and file naming convention (`OrgName_YYYY-MM-DD.xlsx`). The JSON is uploaded via `PUT /config/practice-time-window/%2B{phone}`. The project uses `openpyxl==3.1.5` and `fpdf2==2.8.3`.
