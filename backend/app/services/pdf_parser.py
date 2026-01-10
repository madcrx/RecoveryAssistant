"""
PDF Parsing Service for Aged Receivables Reports

Supports multiple PDF formats and uses AI to intelligently extract structured data.
"""

import re
from datetime import datetime, date
from typing import List, Dict, Optional, Any
from decimal import Decimal
import io

import pdfplumber
import camelot
from PyPDF2 import PdfReader
from openai import AsyncOpenAI

from ..core.config import settings


class ReceivablesData:
    """Structured data extracted from aged receivables report"""

    def __init__(self):
        self.report_date: Optional[date] = None
        self.company_name: Optional[str] = None
        self.total_outstanding: float = 0.0
        self.invoices: List[Dict[str, Any]] = []
        self.aging_summary: Dict[str, float] = {
            "current": 0.0,
            "0-30": 0.0,
            "31-60": 0.0,
            "61-90": 0.0,
            "90+": 0.0,
        }


class PDFParser:
    """Intelligent PDF parser for aged receivables reports"""

    def __init__(self):
        self.openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

    async def parse_pdf(self, pdf_file: bytes, filename: str) -> ReceivablesData:
        """
        Main entry point for parsing PDF files

        Args:
            pdf_file: PDF file content as bytes
            filename: Original filename for context

        Returns:
            ReceivablesData object with extracted information
        """
        # Try multiple parsing methods in order of reliability
        data = ReceivablesData()

        # Method 1: Try structured table extraction with Camelot
        try:
            tables = await self._extract_with_camelot(pdf_file)
            if tables:
                data = await self._parse_structured_tables(tables)
                if data.invoices:
                    return data
        except Exception as e:
            print(f"Camelot extraction failed: {e}")

        # Method 2: Try pdfplumber for better text extraction
        try:
            text = await self._extract_with_pdfplumber(pdf_file)
            if text:
                data = await self._parse_with_ai(text)
                if data.invoices:
                    return data
        except Exception as e:
            print(f"pdfplumber extraction failed: {e}")

        # Method 3: Fallback to PyPDF2
        try:
            text = await self._extract_with_pypdf2(pdf_file)
            if text:
                data = await self._parse_with_ai(text)
        except Exception as e:
            print(f"PyPDF2 extraction failed: {e}")

        return data

    async def _extract_with_camelot(self, pdf_file: bytes) -> List[Any]:
        """Extract tables using Camelot (best for structured PDFs)"""
        # Save to temporary file for Camelot
        import tempfile
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
            tmp.write(pdf_file)
            tmp_path = tmp.name

        try:
            tables = camelot.read_pdf(tmp_path, pages='all', flavor='lattice')
            if not tables:
                tables = camelot.read_pdf(tmp_path, pages='all', flavor='stream')
            return tables
        finally:
            import os
            os.unlink(tmp_path)

    async def _extract_with_pdfplumber(self, pdf_file: bytes) -> str:
        """Extract text using pdfplumber (good balance)"""
        text_content = []
        with pdfplumber.open(io.BytesIO(pdf_file)) as pdf:
            for page in pdf.pages:
                # Try to extract tables first
                tables = page.extract_tables()
                if tables:
                    for table in tables:
                        text_content.append(self._table_to_text(table))

                # Also get regular text
                text = page.extract_text()
                if text:
                    text_content.append(text)

        return "\n\n".join(text_content)

    async def _extract_with_pypdf2(self, pdf_file: bytes) -> str:
        """Extract text using PyPDF2 (fallback method)"""
        reader = PdfReader(io.BytesIO(pdf_file))
        text_content = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                text_content.append(text)
        return "\n\n".join(text_content)

    def _table_to_text(self, table: List[List[str]]) -> str:
        """Convert table structure to formatted text"""
        return "\n".join([" | ".join([cell or "" for cell in row]) for row in table])

    async def _parse_structured_tables(self, tables: List[Any]) -> ReceivablesData:
        """Parse data from structured tables extracted by Camelot"""
        data = ReceivablesData()

        for table in tables:
            df = table.df

            # Try to identify columns by headers
            headers = df.iloc[0].str.lower().tolist()

            # Look for common column patterns
            customer_col = self._find_column(headers, ['customer', 'client', 'company', 'name'])
            invoice_col = self._find_column(headers, ['invoice', 'inv', 'number', 'ref'])
            date_col = self._find_column(headers, ['date', 'inv date', 'invoice date'])
            amount_col = self._find_column(headers, ['amount', 'balance', 'outstanding', 'total'])
            current_col = self._find_column(headers, ['current', '0'])
            days_30_col = self._find_column(headers, ['1-30', '0-30', '30'])
            days_60_col = self._find_column(headers, ['31-60', '60'])
            days_90_col = self._find_column(headers, ['61-90', '90'])
            days_90plus_col = self._find_column(headers, ['90+', 'over 90', '>90'])

            # Extract invoice data
            for idx, row in df.iterrows():
                if idx == 0:  # Skip header row
                    continue

                invoice = {}

                if customer_col is not None:
                    invoice['customer_name'] = str(row[customer_col]).strip()

                if invoice_col is not None:
                    invoice['invoice_number'] = str(row[invoice_col]).strip()

                if date_col is not None:
                    invoice['invoice_date'] = self._parse_date(row[date_col])

                if amount_col is not None:
                    invoice['amount'] = self._parse_amount(row[amount_col])

                # Extract aging buckets
                aging = {}
                if current_col is not None:
                    aging['current'] = self._parse_amount(row[current_col])
                if days_30_col is not None:
                    aging['0-30'] = self._parse_amount(row[days_30_col])
                if days_60_col is not None:
                    aging['31-60'] = self._parse_amount(row[days_60_col])
                if days_90_col is not None:
                    aging['61-90'] = self._parse_amount(row[days_90_col])
                if days_90plus_col is not None:
                    aging['90+'] = self._parse_amount(row[days_90plus_col])

                if aging:
                    invoice['aging'] = aging

                # Only add if we have minimum required data
                if invoice.get('customer_name') or invoice.get('invoice_number'):
                    data.invoices.append(invoice)

        return data

    def _find_column(self, headers: List[str], patterns: List[str]) -> Optional[int]:
        """Find column index matching any of the patterns"""
        for idx, header in enumerate(headers):
            for pattern in patterns:
                if pattern in header:
                    return idx
        return None

    def _parse_amount(self, value: Any) -> float:
        """Parse monetary amount from string"""
        if not value:
            return 0.0

        # Remove currency symbols and commas
        cleaned = re.sub(r'[,$£€¥]', '', str(value))
        cleaned = cleaned.strip()

        # Handle parentheses as negative
        if '(' in cleaned and ')' in cleaned:
            cleaned = '-' + cleaned.replace('(', '').replace(')', '')

        try:
            return float(cleaned)
        except (ValueError, TypeError):
            return 0.0

    def _parse_date(self, value: Any) -> Optional[date]:
        """Parse date from various formats"""
        if not value:
            return None

        date_string = str(value).strip()

        # Common date formats
        formats = [
            '%m/%d/%Y',
            '%d/%m/%Y',
            '%Y-%m-%d',
            '%m-%d-%Y',
            '%d-%m-%Y',
            '%m/%d/%y',
            '%d/%m/%y',
            '%b %d, %Y',
            '%B %d, %Y',
        ]

        for fmt in formats:
            try:
                return datetime.strptime(date_string, fmt).date()
            except ValueError:
                continue

        return None

    async def _parse_with_ai(self, text: str) -> ReceivablesData:
        """Use OpenAI to intelligently parse unstructured text"""

        system_prompt = """You are an expert at extracting structured data from aged receivables reports.
Extract the following information from the text:
1. List of invoices with: customer name, invoice number, invoice date, amount, aging bucket
2. Aging bucket totals (Current, 0-30, 31-60, 61-90, 90+)
3. Report date
4. Total outstanding amount

Return the data in this exact JSON format:
{
    "report_date": "YYYY-MM-DD",
    "total_outstanding": 123456.78,
    "aging_summary": {
        "current": 0.0,
        "0-30": 0.0,
        "31-60": 0.0,
        "61-90": 0.0,
        "90+": 0.0
    },
    "invoices": [
        {
            "customer_name": "Company Name",
            "invoice_number": "INV-12345",
            "invoice_date": "YYYY-MM-DD",
            "due_date": "YYYY-MM-DD",
            "amount": 1234.56,
            "aging_bucket": "31-60",
            "days_outstanding": 45
        }
    ]
}

If information is not available, use null or 0. Be thorough and extract all invoices found.
"""

        try:
            response = await self.openai_client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Extract data from this receivables report:\n\n{text[:8000]}"}
                ],
                temperature=0,
                response_format={"type": "json_object"}
            )

            import json
            result = json.loads(response.choices[0].message.content)

            # Convert to ReceivablesData object
            data = ReceivablesData()

            if result.get('report_date'):
                data.report_date = datetime.strptime(result['report_date'], '%Y-%m-%d').date()

            data.total_outstanding = float(result.get('total_outstanding', 0))
            data.aging_summary = result.get('aging_summary', {})
            data.invoices = result.get('invoices', [])

            return data

        except Exception as e:
            print(f"AI parsing failed: {e}")
            return ReceivablesData()


# Singleton instance
pdf_parser = PDFParser()
