"""Generate a formatted Excel file for ServiceNow imports."""
from __future__ import annotations

import pandas as pd
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.formatting.rule import FormulaRule
import openpyxl
import re

from logging_utils import setup_logger, log_info, log_error
from custom_exceptions import ExcelGenerationError

logger = setup_logger("excel_generator")

ILLEGAL_CHARACTERS_RE = re.compile(r"[\000-\010\013\014\016-\037]")
MAX_EXCEL_CELL_LENGTH = 32767

NEEDS_REVIEW_FILL = PatternFill(
    start_color="FFC7CE", end_color="FFC7CE", fill_type="solid"
)
OCR_FILL = PatternFill(start_color="FFEB9C", end_color="FFEB9C", fill_type="solid")
FAILED_FILL = PatternFill(start_color="9C0006", end_color="9C0006", fill_type="solid")
SUCCESS_FILL = PatternFill(fill_type=None)



DEFAULT_TEMPLATE_HEADERS = [
    "Active",
    "Article type",
    "Author",
    "Category(category)",
    "Configuration item",
    "Confidence",
    "Description",
    "Attachment link",
    "Disable commenting",
    "Disable suggesting",
    "Display attachments",
    "Flagged",
    "Governance",
    "Category(kb_category)",
    "Knowledge base",
    "Meta",
    "Meta Description",
    "Ownership Group",
    "Published",
    "Scheduled publish date",
    "Short description",
    "Article body",
    "Topic",
    "Problem Code",
    "models",
    "Ticket#",
    "Valid to",
    "View as allowed",
    "Wiki",
    "Sys ID",
    "file_name",
    "Change Type",
    "Revision",
]




def sanitize_for_excel(value):
    if isinstance(value, str):
        cleaned = ILLEGAL_CHARACTERS_RE.sub("", value)
        if len(cleaned) > MAX_EXCEL_CELL_LENGTH:
            cleaned = cleaned[:MAX_EXCEL_CELL_LENGTH]
        return cleaned
    return value


def apply_excel_styles(worksheet, df):
    log_info(logger, "Applying formatting and conditional coloring...")
    header_font = Font(bold=True)
    status_colors = {
        "Needs Review": NEEDS_REVIEW_FILL,
        "OCR Required": OCR_FILL,
        "Failed": FAILED_FILL,
        "Success": SUCCESS_FILL,
    }

    for index, data_row in df.iterrows():
        status = data_row.get("processing_status", "Success")
        fill_color = status_colors.get(status, SUCCESS_FILL)
        if fill_color.fill_type:
            for cell in worksheet[index + 2]:
                cell.fill = fill_color

    for cell in worksheet[1]:
        cell.font = header_font

    for row in worksheet.iter_rows(min_row=2):
        for cell in row:
            cell.alignment = Alignment(
                wrap_text=True, vertical="top", horizontal="left"
            )

    for column_cells in worksheet.columns:
        try:
            max_length = max(
                len(str(cell.value)) for cell in column_cells if cell.value
            )
            worksheet.column_dimensions[column_cells[0].column_letter].width = min(
                (max_length + 2), 70
            )
        except (ValueError, TypeError):
            continue

    # Conditional formatting using the processing_status column if present
    if "processing_status" in df.columns:
        status_col_idx = df.columns.get_loc("processing_status") + 1
        last_row = worksheet.max_row
        worksheet.conditional_formatting.add(
            f"A2:{worksheet.cell(row=last_row, column=len(df.columns)).coordinate}",
            FormulaRule(
                formula=[f'INDIRECT(ADDRESS(ROW(),{status_col_idx}))="Failed"'],
                fill=FAILED_FILL,
            ),
        )


class ExcelWriter:
    """Write Excel files with status-based color coding."""

    def __init__(self, path: str, headers: list[str]):
        self.path = path
        self.headers = headers
        self.rows: list[dict] = []

    def add_row(self, data: dict) -> None:
        self.rows.append(data)

    def save(self) -> None:
        df = pd.DataFrame(self.rows, columns=self.headers)
        with pd.ExcelWriter(self.path, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="ServiceNow Import")
            apply_excel_styles(writer.sheets["ServiceNow Import"], df)


def generate_excel(all_results, output_path, template_path):
    try:
        if not all_results:
            raise ExcelGenerationError("No data to generate.")

        df = pd.DataFrame(all_results)
        df_sanitized = df.map(sanitize_for_excel)
        headers = DEFAULT_TEMPLATE_HEADERS

        final_df = pd.DataFrame(columns=headers)
        for col in headers:
            if col in df_sanitized.columns:
                final_df[col] = df_sanitized[col]

        internal_cols = ["needs_review", "processing_status"]
        df_to_save = final_df.drop(
            columns=[c for c in internal_cols if c in final_df.columns], errors="ignore"
        )

        with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
            df_to_save.to_excel(writer, index=False, sheet_name="ServiceNow Import")
            apply_excel_styles(writer.sheets["ServiceNow Import"], df_sanitized)

        log_info(logger, f"Successfully created formatted Excel file: {output_path}")
        return str(output_path)
    except Exception as e:  # pragma: no cover - log and raise
        log_error(logger, f"Excel generation failed: {e}")
        raise ExcelGenerationError(f"Failed to generate Excel file: {e}")



