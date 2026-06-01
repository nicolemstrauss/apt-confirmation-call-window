#!/usr/bin/env python3
"""Generate customer instructions PDF."""

from fpdf import FPDF


class PDF(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 16)
        self.cell(0, 10, "Practice Time Window Configuration", align="C", new_x="LMARGIN", new_y="NEXT")
        self.set_font("Helvetica", "", 11)
        self.cell(0, 8, "Instructions", align="C", new_x="LMARGIN", new_y="NEXT")
        self.ln(4)

    def section(self, title):
        self.set_font("Helvetica", "B", 13)
        self.cell(0, 10, title, new_x="LMARGIN", new_y="NEXT")
        self.ln(1)

    def body_text(self, text):
        self.set_font("Helvetica", "", 10)
        self.multi_cell(0, 5, text)
        self.ln(2)

    def bullet(self, text):
        self.set_font("Helvetica", "", 10)
        x = self.get_x()
        self.cell(8, 5, "  -  ", new_x="END")
        self.multi_cell(self.epw - 8, 5, text)
        self.set_x(x)

    def table(self, headers, rows, col_widths=None):
        if not col_widths:
            col_widths = [self.epw / len(headers)] * len(headers)
        self.set_font("Helvetica", "B", 9)
        for i, h in enumerate(headers):
            self.cell(col_widths[i], 7, h, border=1, align="C")
        self.ln()
        self.set_font("Helvetica", "", 9)
        for row in rows:
            max_h = 7
            for i, val in enumerate(row):
                lines = self.multi_cell(col_widths[i], 7, val, border=0, dry_run=True, output="LINES")
                max_h = max(max_h, len(lines) * 7)
            for i, val in enumerate(row):
                x, y = self.get_x(), self.get_y()
                self.rect(x, y, col_widths[i], max_h)
                self.multi_cell(col_widths[i], 7, val)
                self.set_xy(x + col_widths[i], y)
            self.ln(max_h)
        self.ln(3)


def build_pdf(output="customer_instructions.pdf"):
    pdf = PDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # Getting Started
    pdf.section("Getting Started")
    pdf.body_text(
        "1. Open the attached Excel template file.\n"
        "2. You will see a sheet named \"config\" with column headers and one example row.\n"
        "3. Delete the example row and enter your practice information - one row per practice phone number."
    )

    # Column Guide
    pdf.section("Column Guide")
    pdf.table(
        ["Column", "What to Enter", "Example"],
        [
            ["phone", "Phone number with country code, starting with +", "+12143309221"],
            ["tz", "Timezone (select from dropdown)", "America/Chicago"],
            ["max_days", "Max days to attempt contact", "2"],
            ["attempts_per_day", "Call attempts per day", "1"],
            ["Monday - Sunday", "Call windows for each day (see below)", "08:00-12:00, 13:00-17:00"],
            ["alternate_ivr_behavior", "TRUE if alternate IVR handling needed, otherwise FALSE", "TRUE"],
            ["alternate_ivr_description", "Describe desired IVR behavior (blank if FALSE)", "Wait for a live agent."],
        ],
        col_widths=[40, 75, 55],
    )

    # Time Windows
    pdf.section("Entering Time Windows")
    pdf.body_text(
        "Time windows define when calls are allowed for each practice. "
        "Use 24-hour (military) time format: HH:MM-HH:MM"
    )
    pdf.table(
        ["What you want", "What to enter"],
        [
            ["One window, morning only", "08:00-12:00"],
            ["Two windows, morning and afternoon", "08:00-12:00, 13:00-17:00"],
            ["No calls on this day", "(leave the cell blank)"],
        ],
        col_widths=[85, 85],
    )

    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 7, "Rules:", new_x="LMARGIN", new_y="NEXT")
    for rule in [
        "Always use two digits for hours and minutes (e.g. 08:00, not 8:00)",
        "Hours range from 00 to 23, minutes from 00 to 59",
        "Separate multiple windows with a comma",
        "A prompt will appear when you click a day cell as a reminder",
    ]:
        pdf.bullet(rule)
    pdf.ln(3)

    # 24-hour conversion
    pdf.section("24-Hour Time Reference")
    pdf.table(
        ["Standard Time", "24-Hour Format"],
        [
            ["8:00 AM", "08:00"],
            ["12:00 PM", "12:00"],
            ["12:30 PM", "12:30"],
            ["1:00 PM", "13:00"],
            ["5:00 PM", "17:00"],
        ],
        col_widths=[50, 50],
    )

    # Timezones
    pdf.section("Available Timezones")
    for tz in [
        "America/New_York - Eastern",
        "America/Chicago - Central",
        "America/Denver - Mountain",
        "America/Los_Angeles - Pacific",
        "America/Phoenix - Arizona (no daylight saving)",
    ]:
        pdf.bullet(tz)
    pdf.ln(3)

    # Checklist
    pdf.section("Before You Submit")
    for item in [
        "Every row has a phone number starting with +",
        "A timezone is selected for each row",
        "Time windows use 24-hour format (HH:MM-HH:MM)",
        "Days with no call windows are left blank (not 0 or N/A)",
        "alternate_ivr_behavior is set to TRUE or FALSE for each row",
    ]:
        pdf.bullet(item)
    pdf.ln(5)

    pdf.section("Saving Your File")
    pdf.body_text(
        "Please save the completed file using the following naming format:\n\n"
        "    YourOrganizationName_YYYY-MM-DD.xlsx\n\n"
        "For example:  AcmeHealth_2026-05-01.xlsx"
    )

    pdf.set_font("Helvetica", "I", 10)
    pdf.multi_cell(0, 5, "Once complete, save the file and return it to us. If you have any questions, please reach out to your account representative.")

    pdf.output(output)
    print(f"PDF saved to {output}")


if __name__ == "__main__":
    build_pdf()
