"""
Import Wizard

Wizard for importing receivables data from various sources.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFileDialog, QTextEdit, QProgressBar, QMessageBox, QTableWidget,
    QTableWidgetItem, QHeaderView
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class ImportWorker(QThread):
    """Background worker for importing data"""

    progress = pyqtSignal(str)
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, file_path, import_type, db_manager):
        super().__init__()
        self.file_path = file_path
        self.import_type = import_type
        self.db_manager = db_manager

    def run(self):
        """Run import in background"""
        try:
            if self.import_type == 'pdf':
                self._import_pdf()
            elif self.import_type == 'csv':
                self._import_csv()
        except Exception as e:
            logger.exception("Import failed")
            self.error.emit(str(e))

    def _import_pdf(self):
        """Import from PDF"""
        from ..services.pdf_parser import pdf_parser
        from ..models.database import Customer, Invoice, InvoiceStatus, AgingBucket
        from datetime import date, datetime

        self.progress.emit("Parsing PDF file...")

        # Parse PDF
        data, errors = pdf_parser.parse_pdf(self.file_path)

        if not data:
            self.error.emit("No data extracted from PDF. " + ("\n".join(errors) if errors else ""))
            return

        self.progress.emit(f"Extracted {len(data)} records. Importing to database...")

        # Import to database
        session = self.db_manager.get_session()

        stats = {
            'customers_created': 0,
            'customers_updated': 0,
            'invoices_created': 0,
            'invoices_updated': 0,
            'total_amount': 0.0,
            'errors': errors,
        }

        try:
            for idx, record in enumerate(data, 1):
                self.progress.emit(f"Importing record {idx}/{len(data)}...")

                # Find or create customer
                customer = session.query(Customer).filter_by(
                    company_name=record['customer_name']
                ).first()

                if not customer:
                    customer = Customer(
                        customer_id=f"CUST{1000 + stats['customers_created']}",
                        company_name=record['customer_name'],
                        email=f"{record['customer_name'].lower().replace(' ', '.')}@example.com",  # Placeholder
                        current_balance=record['amount_outstanding'],
                    )
                    session.add(customer)
                    stats['customers_created'] += 1
                else:
                    stats['customers_updated'] += 1

                session.flush()  # Get customer ID

                # Find or create invoice
                invoice = session.query(Invoice).filter_by(
                    invoice_number=record['invoice_number']
                ).first()

                # Map aging bucket string to enum
                aging_map = {
                    'current': AgingBucket.CURRENT,
                    '0-30': AgingBucket.DAYS_0_30,
                    '31-60': AgingBucket.DAYS_31_60,
                    '61-90': AgingBucket.DAYS_61_90,
                    '90+': AgingBucket.DAYS_90_PLUS,
                    'unknown': AgingBucket.CURRENT,
                }

                if not invoice:
                    invoice = Invoice(
                        invoice_number=record['invoice_number'],
                        customer_id=customer.id,
                        invoice_date=record.get('invoice_date') or date.today(),
                        due_date=record.get('due_date') or date.today(),
                        original_amount=record['original_amount'],
                        amount_outstanding=record['amount_outstanding'],
                        amount_paid=0.0,
                        status=InvoiceStatus.OPEN if record['amount_outstanding'] > 0 else InvoiceStatus.PAID,
                        aging_bucket=aging_map.get(record.get('aging_bucket', 'current'), AgingBucket.CURRENT),
                        days_outstanding=record.get('days_overdue', 0),
                    )
                    session.add(invoice)
                    stats['invoices_created'] += 1
                else:
                    # Update existing
                    invoice.amount_outstanding = record['amount_outstanding']
                    invoice.original_amount = record['original_amount']
                    invoice.aging_bucket = aging_map.get(record.get('aging_bucket', 'current'), AgingBucket.CURRENT)
                    invoice.days_outstanding = record.get('days_overdue', 0)
                    stats['invoices_updated'] += 1

                stats['total_amount'] += record['amount_outstanding']

            session.commit()
            self.progress.emit("Import complete!")
            self.finished.emit(stats)

        except Exception as e:
            session.rollback()
            raise
        finally:
            session.close()

    def _import_csv(self):
        """Import from CSV"""
        from ..services.csv_import import csv_importer
        from ..models.database import Customer, Invoice, InvoiceStatus, AgingBucket
        from datetime import date

        self.progress.emit("Parsing CSV file...")

        # Parse CSV
        data, errors = csv_importer.import_csv(self.file_path)

        if not data:
            self.error.emit("No data extracted from CSV. " + ("\n".join(errors) if errors else ""))
            return

        self.progress.emit(f"Extracted {len(data)} records. Importing to database...")

        # Same logic as PDF import
        session = self.db_manager.get_session()

        stats = {
            'customers_created': 0,
            'customers_updated': 0,
            'invoices_created': 0,
            'invoices_updated': 0,
            'total_amount': 0.0,
            'errors': errors,
        }

        try:
            for idx, record in enumerate(data, 1):
                self.progress.emit(f"Importing record {idx}/{len(data)}...")

                # Find or create customer
                customer = session.query(Customer).filter_by(
                    company_name=record['customer_name']
                ).first()

                if not customer:
                    customer = Customer(
                        customer_id=f"CUST{1000 + stats['customers_created']}",
                        company_name=record['customer_name'],
                        email=record.get('email') or f"{record['customer_name'].lower().replace(' ', '.')}@example.com",
                        phone=record.get('phone'),
                        contact_name=record.get('contact_name'),
                        current_balance=record['amount_outstanding'],
                    )
                    session.add(customer)
                    stats['customers_created'] += 1
                else:
                    stats['customers_updated'] += 1
                    if record.get('email'):
                        customer.email = record['email']
                    if record.get('phone'):
                        customer.phone = record['phone']

                session.flush()

                # Create/update invoice
                invoice = session.query(Invoice).filter_by(
                    invoice_number=record['invoice_number']
                ).first()

                aging_map = {
                    'current': AgingBucket.CURRENT,
                    '0-30': AgingBucket.DAYS_0_30,
                    '31-60': AgingBucket.DAYS_31_60,
                    '61-90': AgingBucket.DAYS_61_90,
                    '90+': AgingBucket.DAYS_90_PLUS,
                }

                if not invoice:
                    invoice = Invoice(
                        invoice_number=record['invoice_number'],
                        customer_id=customer.id,
                        invoice_date=record.get('invoice_date') or date.today(),
                        due_date=record.get('due_date') or date.today(),
                        original_amount=record.get('original_amount', record['amount_outstanding']),
                        amount_outstanding=record['amount_outstanding'],
                        amount_paid=0.0,
                        status=InvoiceStatus.OPEN,
                        aging_bucket=aging_map.get(record.get('aging_bucket', 'current'), AgingBucket.CURRENT),
                        days_outstanding=record.get('days_overdue', 0),
                    )
                    session.add(invoice)
                    stats['invoices_created'] += 1
                else:
                    invoice.amount_outstanding = record['amount_outstanding']
                    stats['invoices_updated'] += 1

                stats['total_amount'] += record['amount_outstanding']

            session.commit()
            self.progress.emit("Import complete!")
            self.finished.emit(stats)

        except Exception as e:
            session.rollback()
            raise
        finally:
            session.close()


class ImportDialog(QDialog):
    """Dialog for importing data"""

    def __init__(self, import_type, db_manager, parent=None):
        super().__init__(parent)
        self.import_type = import_type
        self.db_manager = db_manager
        self.worker = None

        self.setWindowTitle(f"Import {import_type.upper()}")
        self.setMinimumSize(600, 400)
        self._setup_ui()

    def _setup_ui(self):
        """Setup UI"""
        layout = QVBoxLayout(self)

        # File selection
        file_layout = QHBoxLayout()
        file_layout.addWidget(QLabel("File:"))
        self.file_label = QLabel("No file selected")
        file_layout.addWidget(self.file_label, 1)

        self.browse_button = QPushButton("Browse...")
        self.browse_button.clicked.connect(self._browse_file)
        file_layout.addWidget(self.browse_button)

        layout.addLayout(file_layout)

        # Progress
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # Indeterminate
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # Status
        self.status_text = QTextEdit()
        self.status_text.setReadOnly(True)
        self.status_text.setMaximumHeight(100)
        layout.addWidget(QLabel("Status:"))
        layout.addWidget(self.status_text)

        # Preview table
        layout.addWidget(QLabel("Preview:"))
        self.preview_table = QTableWidget()
        self.preview_table.setVisible(False)
        layout.addWidget(self.preview_table)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.import_button = QPushButton("Import")
        self.import_button.setEnabled(False)
        self.import_button.clicked.connect(self._start_import)
        button_layout.addWidget(self.import_button)

        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.accept)
        button_layout.addWidget(self.close_button)

        layout.addLayout(button_layout)

    def _browse_file(self):
        """Browse for file"""
        if self.import_type == 'pdf':
            file_filter = "PDF Files (*.pdf)"
        else:
            file_filter = "CSV Files (*.csv)"

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            f"Select {self.import_type.upper()} File",
            "",
            file_filter
        )

        if file_path:
            self.file_path = file_path
            self.file_label.setText(Path(file_path).name)
            self.import_button.setEnabled(True)
            self.status_text.append(f"Selected: {file_path}")

    def _start_import(self):
        """Start import process"""
        if not hasattr(self, 'file_path'):
            return

        self.import_button.setEnabled(False)
        self.browse_button.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.status_text.clear()

        # Create worker thread
        self.worker = ImportWorker(self.file_path, self.import_type, self.db_manager)
        self.worker.progress.connect(self._on_progress)
        self.worker.finished.connect(self._on_finished)
        self.worker.error.connect(self._on_error)
        self.worker.start()

    def _on_progress(self, message):
        """Update progress"""
        self.status_text.append(message)

    def _on_finished(self, stats):
        """Import finished"""
        self.progress_bar.setVisible(False)
        self.import_button.setEnabled(True)
        self.browse_button.setEnabled(True)

        # Show summary
        summary = f"""
Import Complete!

Customers Created: {stats['customers_created']}
Customers Updated: {stats['customers_updated']}
Invoices Created: {stats['invoices_created']}
Invoices Updated: {stats['invoices_updated']}
Total Outstanding: ${stats['total_amount']:,.2f}
"""

        if stats.get('errors'):
            summary += f"\nWarnings/Errors: {len(stats['errors'])}"

        self.status_text.append(summary)

        QMessageBox.information(
            self,
            "Import Complete",
            f"Successfully imported {stats['invoices_created']} invoices!\n\n"
            f"Total Outstanding: ${stats['total_amount']:,.2f}"
        )

    def _on_error(self, error_msg):
        """Import error"""
        self.progress_bar.setVisible(False)
        self.import_button.setEnabled(True)
        self.browse_button.setEnabled(True)

        self.status_text.append(f"\nERROR: {error_msg}")

        QMessageBox.critical(
            self,
            "Import Failed",
            f"Failed to import data:\n\n{error_msg}"
        )
