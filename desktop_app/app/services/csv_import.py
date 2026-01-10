"""
CSV Import Service

Imports aged receivables data from CSV files.
"""

import pandas as pd
from typing import Dict, List, Optional, Tuple
from datetime import datetime, date
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class CSVImporter:
    """Import receivables data from CSV files"""

    # Standard column mappings
    COLUMN_MAPPINGS = {
        # Customer fields
        'customer_name': ['customer', 'customer_name', 'company', 'company_name', 'client', 'debtor'],
        'customer_id': ['customer_id', 'customer_number', 'account_number', 'customer_code'],
        'email': ['email', 'customer_email', 'contact_email', 'e-mail'],
        'phone': ['phone', 'telephone', 'contact_phone', 'mobile'],
        'contact_name': ['contact', 'contact_name', 'contact_person', 'attn'],

        # Invoice fields
        'invoice_number': ['invoice', 'invoice_number', 'invoice_no', 'inv_no', 'reference'],
        'invoice_date': ['invoice_date', 'inv_date', 'date', 'transaction_date'],
        'due_date': ['due_date', 'payment_due', 'due'],
        'original_amount': ['amount', 'invoice_amount', 'total', 'original_amount', 'balance'],
        'amount_outstanding': ['outstanding', 'amount_outstanding', 'balance_due', 'open_balance'],

        # Aging fields
        'current': ['current', '0_days', 'not_due'],
        'days_0_30': ['0-30', '1-30', '30_days', '0_30'],
        'days_31_60': ['31-60', '60_days', '31_60'],
        'days_61_90': ['61-90', '90_days', '61_90'],
        'days_90_plus': ['90+', '90plus', '90_plus', 'over_90'],
    }

    def __init__(self):
        self.column_map = {}

    def detect_columns(self, df: pd.DataFrame) -> Dict[str, str]:
        """
        Auto-detect column mappings from DataFrame

        Args:
            df: pandas DataFrame

        Returns:
            Dict mapping standard field names to actual column names
        """

        column_map = {}
        df_columns_lower = [col.lower().strip() for col in df.columns]

        for standard_field, possible_names in self.COLUMN_MAPPINGS.items():
            for possible_name in possible_names:
                if possible_name.lower() in df_columns_lower:
                    idx = df_columns_lower.index(possible_name.lower())
                    column_map[standard_field] = df.columns[idx]
                    break

        logger.info(f"Detected columns: {column_map}")
        return column_map

    def import_csv(
        self,
        file_path: str,
        column_map: Optional[Dict[str, str]] = None,
        skip_rows: int = 0,
        date_format: str = "%Y-%m-%d"
    ) -> Tuple[List[Dict], List[str]]:
        """
        Import receivables data from CSV file

        Args:
            file_path: Path to CSV file
            column_map: Custom column mapping (if None, will auto-detect)
            skip_rows: Number of rows to skip at start
            date_format: Date format string

        Returns:
            Tuple of (data_list, errors_list)
        """

        try:
            # Read CSV
            df = pd.read_csv(
                file_path,
                skiprows=skip_rows,
                encoding='utf-8-sig'  # Handle BOM
            )

            logger.info(f"CSV loaded: {len(df)} rows, {len(df.columns)} columns")

            # Auto-detect columns if not provided
            if not column_map:
                column_map = self.detect_columns(df)

            self.column_map = column_map

            # Validate required fields
            required_fields = ['customer_name', 'invoice_number', 'amount_outstanding']
            missing_fields = [f for f in required_fields if f not in column_map]

            if missing_fields:
                error_msg = f"Missing required fields: {', '.join(missing_fields)}"
                logger.error(error_msg)
                return [], [error_msg]

            # Process rows
            data_list = []
            errors = []

            for idx, row in df.iterrows():
                try:
                    record = self._process_row(row, column_map, date_format)
                    if record:
                        data_list.append(record)
                except Exception as e:
                    error = f"Row {idx + 1}: {str(e)}"
                    errors.append(error)
                    logger.warning(error)

            logger.info(f"Import complete: {len(data_list)} records, {len(errors)} errors")

            return data_list, errors

        except Exception as e:
            logger.error(f"Failed to import CSV: {e}")
            return [], [f"Failed to read CSV file: {str(e)}"]

    def _process_row(
        self,
        row: pd.Series,
        column_map: Dict[str, str],
        date_format: str
    ) -> Optional[Dict]:
        """Process a single CSV row"""

        # Skip empty rows
        if row.isna().all():
            return None

        record = {}

        # Extract customer information
        record['customer_name'] = self._get_value(row, column_map, 'customer_name')
        record['customer_id'] = self._get_value(row, column_map, 'customer_id', required=False)
        record['email'] = self._get_value(row, column_map, 'email', required=False)
        record['phone'] = self._get_value(row, column_map, 'phone', required=False)
        record['contact_name'] = self._get_value(row, column_map, 'contact_name', required=False)

        # Extract invoice information
        record['invoice_number'] = self._get_value(row, column_map, 'invoice_number')
        record['invoice_date'] = self._parse_date(
            self._get_value(row, column_map, 'invoice_date', required=False),
            date_format
        )
        record['due_date'] = self._parse_date(
            self._get_value(row, column_map, 'due_date', required=False),
            date_format
        )

        # Extract amounts
        record['original_amount'] = self._parse_amount(
            self._get_value(row, column_map, 'original_amount', required=False)
        )
        record['amount_outstanding'] = self._parse_amount(
            self._get_value(row, column_map, 'amount_outstanding')
        )

        # Extract aging buckets (if available)
        record['aging_buckets'] = {
            'current': self._parse_amount(self._get_value(row, column_map, 'current', required=False)),
            '0-30': self._parse_amount(self._get_value(row, column_map, 'days_0_30', required=False)),
            '31-60': self._parse_amount(self._get_value(row, column_map, 'days_31_60', required=False)),
            '61-90': self._parse_amount(self._get_value(row, column_map, 'days_61_90', required=False)),
            '90+': self._parse_amount(self._get_value(row, column_map, 'days_90_plus', required=False)),
        }

        # Calculate aging bucket if due date provided
        if record['due_date']:
            days_overdue = (date.today() - record['due_date']).days
            record['days_overdue'] = days_overdue
            record['aging_bucket'] = self._calculate_aging_bucket(days_overdue)
        else:
            record['days_overdue'] = 0
            record['aging_bucket'] = 'current'

        return record

    def _get_value(
        self,
        row: pd.Series,
        column_map: Dict[str, str],
        field: str,
        required: bool = True
    ) -> Optional[any]:
        """Get value from row using column mapping"""

        if field in column_map:
            column_name = column_map[field]
            value = row[column_name]

            # Return None for NaN values
            if pd.isna(value):
                if required:
                    raise ValueError(f"Required field '{field}' is empty")
                return None

            # Convert to string and strip whitespace
            return str(value).strip()

        if required:
            raise ValueError(f"Required field '{field}' not found in mapping")

        return None

    def _parse_amount(self, value: Optional[str]) -> float:
        """Parse amount string to float"""

        if not value or pd.isna(value):
            return 0.0

        try:
            # Remove currency symbols and commas
            cleaned = str(value).replace('$', '').replace(',', '').replace('£', '').replace('€', '').strip()

            # Handle parentheses for negative numbers
            if cleaned.startswith('(') and cleaned.endswith(')'):
                cleaned = '-' + cleaned[1:-1]

            return float(cleaned)

        except (ValueError, TypeError):
            logger.warning(f"Could not parse amount: {value}")
            return 0.0

    def _parse_date(self, value: Optional[str], date_format: str) -> Optional[date]:
        """Parse date string to date object"""

        if not value or pd.isna(value):
            return None

        try:
            # Try specified format first
            return datetime.strptime(str(value), date_format).date()
        except (ValueError, TypeError):
            # Try common date formats
            common_formats = [
                "%Y-%m-%d",
                "%m/%d/%Y",
                "%d/%m/%Y",
                "%Y/%m/%d",
                "%m-%d-%Y",
                "%d-%m-%Y",
            ]

            for fmt in common_formats:
                try:
                    return datetime.strptime(str(value), fmt).date()
                except (ValueError, TypeError):
                    continue

            logger.warning(f"Could not parse date: {value}")
            return None

    def _calculate_aging_bucket(self, days_overdue: int) -> str:
        """Calculate aging bucket from days overdue"""

        if days_overdue < 0:
            return 'current'
        elif days_overdue <= 30:
            return '0-30'
        elif days_overdue <= 60:
            return '31-60'
        elif days_overdue <= 90:
            return '61-90'
        else:
            return '90+'

    def get_csv_template(self) -> str:
        """
        Generate CSV template with expected columns

        Returns:
            CSV string
        """

        template = """customer_name,customer_id,email,phone,contact_name,invoice_number,invoice_date,due_date,original_amount,amount_outstanding,current,0-30,31-60,61-90,90+
ABC Company,CUST001,billing@abc.com,555-0100,John Smith,INV-001,2024-01-15,2024-02-14,5000.00,5000.00,0,5000.00,0,0,0
XYZ Corp,CUST002,ap@xyz.com,555-0200,Jane Doe,INV-002,2024-02-01,2024-03-02,10000.00,10000.00,10000.00,0,0,0,0"""

        return template

    def export_template(self, file_path: str) -> bool:
        """
        Export CSV template to file

        Args:
            file_path: Path to save template

        Returns:
            Success status
        """

        try:
            template = self.get_csv_template()
            Path(file_path).write_text(template, encoding='utf-8')
            logger.info(f"Template exported to {file_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to export template: {e}")
            return False


# Singleton instance
csv_importer = CSVImporter()
