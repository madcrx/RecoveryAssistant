"""
PDF Parser Service

Extracts aged receivables data from PDF files.
"""

import PyPDF2
import pdfplumber
import re
from typing import List, Dict, Tuple
from datetime import datetime, date
import logging

logger = logging.getLogger(__name__)


class PDFParser:
    """Parse aged receivables PDF reports"""

    def __init__(self):
        self.data = []
        self.errors = []

    def parse_pdf(self, pdf_path: str) -> Tuple[List[Dict], List[str]]:
        """
        Parse PDF and extract receivables data

        Args:
            pdf_path: Path to PDF file

        Returns:
            Tuple of (data_list, errors_list)
        """
        self.data = []
        self.errors = []

        try:
            # Try pdfplumber first (better for tables)
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages, 1):
                    try:
                        # Extract tables
                        tables = page.extract_tables()

                        if tables:
                            for table in tables:
                                self._process_table(table, page_num)
                        else:
                            # Try text extraction if no tables
                            text = page.extract_text()
                            if text:
                                self._process_text(text, page_num)

                    except Exception as e:
                        logger.warning(f"Error processing page {page_num}: {e}")
                        self.errors.append(f"Page {page_num}: {str(e)}")

            logger.info(f"Extracted {len(self.data)} records from PDF")
            return self.data, self.errors

        except Exception as e:
            logger.error(f"Failed to parse PDF: {e}")
            self.errors.append(f"Failed to open PDF: {str(e)}")
            return [], self.errors

    def _process_table(self, table: List[List[str]], page_num: int):
        """Process a table extracted from PDF"""

        if not table or len(table) < 2:
            return

        # Try to identify header row
        header_row = table[0]

        # Map common column names
        column_map = self._identify_columns(header_row)

        if not column_map:
            logger.warning(f"Could not identify columns on page {page_num}")
            return

        # Process data rows
        for row_num, row in enumerate(table[1:], 2):
            try:
                if not row or all(cell is None or str(cell).strip() == '' for cell in row):
                    continue

                # Skip total/subtotal rows
                first_cell = str(row[0] or '').strip().lower() if row else ''
                if any(keyword in first_cell for keyword in ['total', 'subtotal', 'percentage', 'grand total']):
                    continue

                record = self._extract_record_from_row(row, column_map)
                if record:
                    self.data.append(record)

            except Exception as e:
                logger.warning(f"Error processing row {row_num} on page {page_num}: {e}")

    def _identify_columns(self, header_row: List[str]) -> Dict[str, int]:
        """Identify column indices from header row"""

        column_map = {}

        # Normalize headers
        headers = [str(h).lower().strip() if h else '' for h in header_row]

        # Common column patterns
        patterns = {
            'customer': ['customer', 'company', 'name', 'debtor', 'client', 'contact'],
            'invoice': ['invoice', 'inv', 'number', 'inv#', 'invoice#'],
            'date': ['date', 'inv date', 'invoice date'],
            'due_date': ['due', 'due date', 'payment due'],
            'amount': ['amount', 'balance', 'total', 'outstanding'],
            'current': ['current', '0 days', 'not due'],
            '0-30': ['0-30', '1-30', '30', '30 days', '<1 month', '< 1 month'],
            '31-60': ['31-60', '60', '60 days', '1 month'],
            '61-90': ['61-90', '90', '90 days', '2 months'],
            '90+': ['90+', '90 plus', 'over 90', '>90', '3 months', 'older'],
        }

        for col_idx, header in enumerate(headers):
            for field, keywords in patterns.items():
                if any(keyword in header for keyword in keywords):
                    column_map[field] = col_idx
                    break

        return column_map

    def _extract_record_from_row(self, row: List[str], column_map: Dict[str, int]) -> Dict:
        """Extract record from table row"""

        record = {}

        # Customer name (required) - may span multiple cells
        if 'customer' in column_map:
            customer_idx = column_map['customer']

            # Collect all name parts starting from customer column
            name_parts = []

            # Get known numeric column indices to avoid including them in the name
            numeric_columns = set()
            for key in ['current', '0-30', '31-60', '61-90', '90+', 'amount', 'invoice']:
                if key in column_map:
                    numeric_columns.add(column_map[key])

            # Start from customer column and look ahead
            for idx in range(customer_idx, min(len(row), customer_idx + 6)):  # Look ahead up to 5 cells
                cell = str(row[idx] or '').strip()

                # Skip empty cells
                if not cell:
                    continue

                # Stop if we hit a numeric column
                if idx in numeric_columns and idx != customer_idx:
                    break

                # Check if this looks like a number or date
                is_number = bool(re.match(r'^[\d,.$()%-]+$', cell))
                is_date = bool(re.match(r'^\d{1,2}[/-]\d{1,2}[/-]\d{2,4}$', cell))

                if is_number or is_date:
                    # If we already have some name parts, stop here
                    if name_parts:
                        break
                    # If this is the first cell and it's a number, skip this row
                    if idx == customer_idx:
                        return None
                    continue

                # Check if it looks like a header (all caps, short, known column name)
                if cell.upper() == cell and len(cell) < 8 and cell in ['MONTH', 'MONTHS', 'TOTAL', 'OLDER', 'CURRENT']:
                    # This is likely a column header, skip this row
                    if idx == customer_idx:
                        return None
                    break

                # Add this as part of the name
                name_parts.append(cell)

            # Join all parts with spaces
            customer_name = ' '.join(name_parts)

            # Clean up the company name
            customer_name = re.sub(r'\s+', ' ', customer_name).strip()

            if customer_name and len(customer_name) > 1:
                record['customer_name'] = customer_name
            else:
                return None  # Skip if no valid customer name
        else:
            return None

        # Invoice number (optional for customer summaries)
        if 'invoice' in column_map:
            invoice = row[column_map['invoice']]
            if invoice and str(invoice).strip():
                record['invoice_number'] = str(invoice).strip()
            else:
                # Generate invoice number from customer + amount
                record['invoice_number'] = f"SUMMARY-{record['customer_name'][:10].upper().replace(' ', '')}-{len(self.data)+1}"
        else:
            # No invoice column - this is a customer aging summary
            record['invoice_number'] = f"SUMMARY-{record['customer_name'][:10].upper().replace(' ', '')}"
            record['is_summary'] = True  # Mark as summary record

        # Dates
        if 'date' in column_map:
            record['invoice_date'] = self._parse_date(row[column_map['date']])

        if 'due_date' in column_map:
            record['due_date'] = self._parse_date(row[column_map['due_date']])

        # Amount - check aging columns first, then total
        total_amount = 0.0
        aging_buckets = {}

        for bucket in ['current', '0-30', '31-60', '61-90', '90+']:
            if bucket in column_map:
                amount = self._parse_amount(row[column_map[bucket]])
                aging_buckets[bucket] = amount
                total_amount += amount

        if total_amount == 0 and 'amount' in column_map:
            total_amount = self._parse_amount(row[column_map['amount']])

        record['amount_outstanding'] = total_amount
        record['original_amount'] = total_amount
        record['aging_buckets'] = aging_buckets

        # Calculate aging bucket if due date available
        if record.get('due_date'):
            days_overdue = (date.today() - record['due_date']).days
            record['days_overdue'] = max(0, days_overdue)
            record['aging_bucket'] = self._calculate_aging_bucket(days_overdue)
        else:
            record['days_overdue'] = 0
            record['aging_bucket'] = 'current'

        return record if total_amount > 0 else None

    def _process_text(self, text: str, page_num: int):
        """Process plain text extraction (fallback)"""

        # Try to extract line-by-line
        lines = text.split('\n')

        for line in lines:
            # Look for patterns like: CustomerName  INV-123  $1,234.56
            # This is a very basic fallback
            match = re.search(r'([A-Za-z\s&.]+)\s+([A-Z0-9-]+)\s+\$?([\d,]+\.?\d*)', line)
            if match:
                customer, invoice, amount = match.groups()

                record = {
                    'customer_name': customer.strip(),
                    'invoice_number': invoice.strip(),
                    'amount_outstanding': self._parse_amount(amount),
                    'original_amount': self._parse_amount(amount),
                    'aging_bucket': 'unknown',
                    'days_overdue': 0,
                }

                if record['amount_outstanding'] > 0:
                    self.data.append(record)

    def _parse_amount(self, value: any) -> float:
        """Parse amount from string"""

        if value is None:
            return 0.0

        try:
            # Convert to string and clean
            cleaned = str(value).replace('$', '').replace(',', '').replace('£', '').replace('€', '').strip()

            # Handle parentheses for negative
            if cleaned.startswith('(') and cleaned.endswith(')'):
                cleaned = '-' + cleaned[1:-1]

            # Handle empty
            if not cleaned or cleaned == '-':
                return 0.0

            return float(cleaned)

        except (ValueError, TypeError):
            return 0.0

    def _parse_date(self, value: any) -> date:
        """Parse date from string"""

        if not value:
            return None

        date_str = str(value).strip()

        # Common date formats
        formats = [
            '%Y-%m-%d',
            '%m/%d/%Y',
            '%d/%m/%Y',
            '%Y/%m/%d',
            '%m-%d-%Y',
            '%d-%m-%Y',
            '%b %d, %Y',
            '%d %b %Y',
        ]

        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt).date()
            except (ValueError, TypeError):
                continue

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


# Singleton instance
pdf_parser = PDFParser()
