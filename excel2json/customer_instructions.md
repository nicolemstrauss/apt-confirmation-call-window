# Practice Time Window Configuration — Instructions

Thank you for choosing to configure your practice time windows. Please follow the instructions below to complete the attached Excel template.

## Getting Started

1. Open the attached file: **[OrgName]Template.xlsx**
2. You will see a single sheet named **config** with column headers and one example row
3. Delete the example row and enter your practice information — one row per practice phone number

## Column Guide

| Column | What to Enter | Example |
|---|---|---|
| **phone** | Practice phone number with country code, starting with `+` | `+12143309221` |
| **tz** | Timezone — select from the dropdown | `America/Chicago` |
| **max_days** | Maximum number of days to attempt contact | `2` |
| **attempts_per_day** | Number of call attempts per day | `1` |
| **Monday – Sunday** | Call windows for each day (see below) | `08:00-12:00, 13:00-17:00` |
| **alternate_ivr_behavior** | Set to `TRUE` if alternate IVR handling is needed, otherwise `FALSE` | `TRUE` |
| **alternate_ivr_description** | If alternate IVR is TRUE, describe the desired behavior. Leave blank otherwise. | `Wait for a live agent.` |

## Entering Time Windows

Time windows tell us when we are allowed to call each practice. Use **24-hour (military) time** format.

**Format:** `HH:MM-HH:MM`

| What you want | What to enter |
|---|---|
| One window, morning only | `08:00-12:00` |
| Two windows, morning and afternoon | `08:00-12:00, 13:00-17:00` |
| No calls on this day | *(leave the cell blank)* |

**Rules:**
- Hours range from `00` to `23`, minutes from `00` to `59`
- Always use two digits for hours and minutes (e.g. `08:00`, not `8:00`)
- Separate multiple windows with a comma
- A prompt will appear when you click a day cell as a reminder

**Examples:**

| Time | 24-Hour Format |
|---|---|
| 8:00 AM | `08:00` |
| 12:30 PM | `12:30` |
| 1:00 PM | `13:00` |
| 5:00 PM | `17:00` |

## Available Timezones

Select from the dropdown in the **tz** column:

- `America/New_York` — Eastern
- `America/Chicago` — Central
- `America/Denver` — Mountain
- `America/Los_Angeles` — Pacific
- `America/Phoenix` — Arizona (no daylight saving)

## Before You Submit

- [ ] Every row has a phone number starting with `+`
- [ ] A timezone is selected for each row
- [ ] Time windows use 24-hour format (`HH:MM-HH:MM`)
- [ ] Days with no call windows are left blank (not `0` or `N/A`)
- [ ] `alternate_ivr_behavior` is set to `TRUE` or `FALSE` for each row

## Saving Your File

Please save the completed file using the following naming format:

```
YourOrganizationName_YYYY-MM-DD.xlsx
```

**Example:** `AcmeHealth_2026-05-01.xlsx`

Once complete, save the file and return it to us. If you have any questions, please reach out to your account representative.
