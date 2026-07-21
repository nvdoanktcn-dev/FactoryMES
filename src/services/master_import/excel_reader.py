from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd


@dataclass(slots=True)
class ExcelPreviewResult:
    file_path: str
    sheet_name: str
    sheet_names: list[str]
    headers: list[str]
    rows: list[dict[str, Any]]
    total_rows: int
    header_row: int


class ExcelReaderService:
    """
    Service đọc file Excel cho Master Import Center.

    Hỗ trợ:
    - .xlsx
    - .xls
    - Liệt kê sheet
    - Tự phát hiện dòng header
    - Preview giới hạn số dòng
    - Chuẩn hóa tên cột
    """

    SUPPORTED_EXTENSIONS = {
        ".xlsx",
        ".xls",
    }

    DEFAULT_PREVIEW_LIMIT = 100
    DEFAULT_HEADER_SCAN_LIMIT = 30

    def inspect_workbook(
        self,
        file_path: str,
    ) -> list[str]:
        """
        Trả danh sách sheet trong workbook.
        """

        path = self._validate_file(
            file_path
        )

        try:
            workbook = pd.ExcelFile(
                path
            )

            return list(
                workbook.sheet_names
            )

        except Exception as error:
            raise ValueError(
                f"Cannot open Excel workbook: {error}"
            ) from error

    def preview(
        self,
        file_path: str,
        sheet_name: str | None = None,
        limit: int = DEFAULT_PREVIEW_LIMIT,
        header_row: int | None = None,
    ) -> ExcelPreviewResult:
        """
        Đọc dữ liệu preview từ một sheet.

        header_row:
            Dùng index 0-based.

        Nếu không truyền header_row,
        service sẽ tự phát hiện.
        """

        path = self._validate_file(
            file_path
        )

        limit = self._normalize_limit(
            limit
        )

        sheet_names = self.inspect_workbook(
            str(path)
        )

        selected_sheet = (
            self._resolve_sheet_name(
                sheet_names=sheet_names,
                requested_sheet=sheet_name,
            )
        )

        if header_row is None:
            header_row = self.detect_header_row(
                file_path=str(path),
                sheet_name=selected_sheet,
            )

        dataframe = self._read_dataframe(
            file_path=str(path),
            sheet_name=selected_sheet,
            header_row=header_row,
        )

        dataframe = self._normalize_dataframe(
            dataframe
        )

        total_rows = len(
            dataframe
        )

        preview_frame = dataframe.head(
            limit
        )

        rows = (
            preview_frame
            .where(
                pd.notna(preview_frame),
                None,
            )
            .to_dict(
                orient="records"
            )
        )

        return ExcelPreviewResult(
            file_path=str(path),
            sheet_name=selected_sheet,
            sheet_names=sheet_names,
            headers=[
                str(column)
                for column in dataframe.columns
            ],
            rows=rows,
            total_rows=total_rows,
            header_row=header_row,
        )

    def detect_header_row(
        self,
        file_path: str,
        sheet_name: str | None = None,
        scan_limit: int = DEFAULT_HEADER_SCAN_LIMIT,
    ) -> int:
        """
        Tự phát hiện dòng header.

        Heuristic:
        - Bỏ dòng hoàn toàn rỗng.
        - Ưu tiên dòng có nhiều ô text.
        - Ưu tiên dòng có nhiều giá trị duy nhất.
        """

        path = self._validate_file(
            file_path
        )

        sheet_names = self.inspect_workbook(
            str(path)
        )

        selected_sheet = (
            self._resolve_sheet_name(
                sheet_names=sheet_names,
                requested_sheet=sheet_name,
            )
        )

        scan_limit = max(
            1,
            int(scan_limit),
        )

        try:
            raw_frame = pd.read_excel(
                path,
                sheet_name=selected_sheet,
                header=None,
                nrows=scan_limit,
                dtype=object,
            )

        except Exception as error:
            raise ValueError(
                f"Cannot read sheet '{selected_sheet}': {error}"
            ) from error

        if raw_frame.empty:
            raise ValueError(
                f"Sheet '{selected_sheet}' is empty."
            )

        best_row_index = None
        best_score = -1.0

        for row_index, row in (
            raw_frame.iterrows()
        ):
            values = [
                self._clean_cell(value)
                for value in row.tolist()
            ]

            non_empty = [
                value
                for value in values
                if value not in {
                    None,
                    "",
                }
            ]

            if not non_empty:
                continue

            text_count = sum(
                isinstance(value, str)
                for value in non_empty
            )

            unique_count = len(
                {
                    str(value).strip().lower()
                    for value in non_empty
                }
            )

            duplicate_count = (
                len(non_empty)
                - unique_count
            )

            score = (
                len(non_empty) * 3
                + text_count * 2
                + unique_count
                - duplicate_count * 2
            )

            if score > best_score:
                best_score = score
                best_row_index = int(
                    row_index
                )

        if best_row_index is None:
            raise ValueError(
                f"Cannot detect header row in sheet "
                f"'{selected_sheet}'."
            )

        return best_row_index

    def read_all(
        self,
        file_path: str,
        sheet_name: str | None = None,
        header_row: int | None = None,
    ) -> list[dict[str, Any]]:
        """
        Đọc toàn bộ dữ liệu của sheet.
        """

        result = self.preview(
            file_path=file_path,
            sheet_name=sheet_name,
            limit=2_147_483_647,
            header_row=header_row,
        )

        return result.rows

    def headers(
        self,
        file_path: str,
        sheet_name: str | None = None,
        header_row: int | None = None,
    ) -> list[str]:
        """
        Trả danh sách tên cột.
        """

        result = self.preview(
            file_path=file_path,
            sheet_name=sheet_name,
            limit=1,
            header_row=header_row,
        )

        return result.headers

    # ==========================================================
    # Internal read helpers
    # ==========================================================

    def _read_dataframe(
        self,
        file_path: str,
        sheet_name: str,
        header_row: int,
    ) -> pd.DataFrame:
        try:
            return pd.read_excel(
                file_path,
                sheet_name=sheet_name,
                header=header_row,
                dtype=object,
            )

        except Exception as error:
            raise ValueError(
                f"Cannot read Excel data: {error}"
            ) from error

    def _normalize_dataframe(
        self,
        dataframe: pd.DataFrame,
    ) -> pd.DataFrame:
        if dataframe is None:
            return pd.DataFrame()

        normalized = dataframe.copy()

        normalized = normalized.dropna(
            axis=0,
            how="all",
        )

        normalized = normalized.dropna(
            axis=1,
            how="all",
        )

        normalized.columns = (
            self._normalize_headers(
                normalized.columns.tolist()
            )
        )

        normalized = normalized.reset_index(
            drop=True
        )

        return normalized

    def _normalize_headers(
        self,
        headers,
    ) -> list[str]:
        result = []
        used_names: dict[str, int] = {}

        for index, header in enumerate(
            headers
        ):
            normalized = self._normalize_header(
                header,
                index,
            )

            count = used_names.get(
                normalized,
                0,
            )

            used_names[
                normalized
            ] = count + 1

            if count > 0:
                normalized = (
                    f"{normalized}_{count + 1}"
                )

            result.append(
                normalized
            )

        return result

    @staticmethod
    def _normalize_header(
        header,
        index,
    ) -> str:
        if header is None:
            return f"Column_{index + 1}"

        text = str(
            header
        )

        text = text.replace(
            "\n",
            " ",
        )

        text = " ".join(
            text.split()
        ).strip()

        if not text:
            return f"Column_{index + 1}"

        if text.lower().startswith(
            "unnamed:"
        ):
            return f"Column_{index + 1}"

        return text

    # ==========================================================
    # Validation helpers
    # ==========================================================

    def _validate_file(
        self,
        file_path: str,
    ) -> Path:
        path_text = str(
            file_path or ""
        ).strip()

        if not path_text:
            raise ValueError(
                "Excel file path is required."
            )

        path = Path(
            path_text
        )

        if not path.exists():
            raise FileNotFoundError(
                f"Excel file does not exist: {path}"
            )

        if not path.is_file():
            raise ValueError(
                f"Excel path is not a file: {path}"
            )

        extension = path.suffix.lower()

        if extension not in (
            self.SUPPORTED_EXTENSIONS
        ):
            raise ValueError(
                "Unsupported Excel format. "
                "Only .xlsx and .xls are allowed."
            )

        return path

    @staticmethod
    def _resolve_sheet_name(
        sheet_names: list[str],
        requested_sheet: str | None,
    ) -> str:
        if not sheet_names:
            raise ValueError(
                "Workbook does not contain any sheet."
            )

        if requested_sheet is None:
            return sheet_names[0]

        requested = str(
            requested_sheet
        ).strip()

        if not requested:
            return sheet_names[0]

        if requested not in sheet_names:
            raise ValueError(
                f"Sheet '{requested}' was not found. "
                f"Available sheets: {sheet_names}"
            )

        return requested

    @staticmethod
    def _normalize_limit(
        limit,
    ) -> int:
        try:
            value = int(
                limit
            )

        except (
            TypeError,
            ValueError,
        ):
            value = (
                ExcelReaderService
                .DEFAULT_PREVIEW_LIMIT
            )

        if value <= 0:
            raise ValueError(
                "Preview limit must be greater than zero."
            )

        return value

    @staticmethod
    def _clean_cell(value):
        if pd.isna(value):
            return None

        if isinstance(value, str):
            return value.strip()

        return value