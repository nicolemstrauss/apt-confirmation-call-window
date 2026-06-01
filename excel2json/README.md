# excel2json

Convert an Excel spreadsheet into per-practice JSON config files for the `practice-time-window` DynamoDB table.

## Quick Start

```bash
pip3 install -r requirements.txt
python3 create_template.py          # generates practice_time_window_template.xlsx
# fill in the template, then:
python3 convert.py <workbook.xlsx> -o json
```

## Excel Format

Single sheet named `config`. One row per practice.

| Column | Type | Description |
|---|---|---|
| `phone` | string | E.164 format (e.g. `+12143309221`) |
| `tz` | string | IANA timezone (e.g. `America/Chicago`) |
| `max_days` | int | Max days to attempt |
| `attempts_per_day` | int | Attempts per day |
| `Monday`–`Sunday` | string | Comma-separated `HH:MM-HH:MM` ranges. Blank = no windows. |
| `alternate_ivr_behavior` | bool | `TRUE` / `FALSE` |
| `alternate_ivr_description` | string | Free text. Omitted from JSON if blank. |

### Example day values

| Cell value | Meaning |
|---|---|
| `08:00-12:00, 13:00-17:00` | Two windows |
| `09:00-11:30` | One window |
| *(empty)* | No windows |

### Day-of-week mapping

Monday=0, Tuesday=1, Wednesday=2, Thursday=3, Friday=4, Saturday=5, Sunday=6

## Output

One JSON file per row, named `{phone_without_plus}.json`:

```json
{
  "tz": "America/Chicago",
  "max_days": 2,
  "attempts_per_day": 1,
  "windows": [
    { "dow": 0, "start": "08:00", "end": "12:00" },
    { "dow": 0, "start": "13:00", "end": "17:00" }
  ],
  "alternate_ivr_behavior": true,
  "alternate_ivr_description": "When encountering IVR, do not engage with the IVR system and instead wait for a human to answer."
}
```

## API Upload

Each JSON file is the body for:

```
PUT /config/practice-time-window/%2B{phone_number}
Content-Type: application/json
```

## Project Structure

```
├── create_template.py       # Generate blank Excel template
├── convert.py               # Convert populated Excel → JSON files
├── requirements.txt         # openpyxl==3.1.5
└── sample_3_practices.xlsx  # Example workbook with 3 practices
```
