"""
Analytics View Widget
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QGridLayout, QPushButton, QFileDialog, QMessageBox, QTableWidget,
    QTableWidgetItem, QHeaderView
)
from PyQt6.QtCore import Qt
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class ReportCard(QFrame):
    """Card widget for displaying a report metric"""

    def __init__(self, title, value, subtitle="", trend=None):
        super().__init__()
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 8px;
                padding: 15px;
            }
        """)

        layout = QVBoxLayout(self)

        title_label = QLabel(title)
        title_label.setStyleSheet("color: #666; font-size: 12px;")
        layout.addWidget(title_label)

        value_label = QLabel(value)
        value_label.setStyleSheet("color: #333; font-size: 24px; font-weight: bold;")
        layout.addWidget(value_label)

        if subtitle:
            subtitle_label = QLabel(subtitle)
            subtitle_label.setStyleSheet("color: #999; font-size: 11px;")
            layout.addWidget(subtitle_label)

        if trend:
            trend_label = QLabel(trend)
            if "↑" in trend:
                trend_label.setStyleSheet("color: green; font-size: 12px; font-weight: bold;")
            elif "↓" in trend:
                trend_label.setStyleSheet("color: red; font-size: 12px; font-weight: bold;")
            layout.addWidget(trend_label)


class AnalyticsWidget(QWidget):
    """Analytics and reporting view"""

    def __init__(self, db_manager):
        super().__init__()
        self.db_manager = db_manager
        self._setup_ui()

    def _setup_ui(self):
        """Setup analytics view UI"""
        main_layout = QVBoxLayout(self)

        # Title and export button
        header = QHBoxLayout()

        title = QLabel("📈 Analytics & Reports")
        title.setStyleSheet("font-size: 24px; font-weight: bold;")
        header.addWidget(title)

        header.addStretch()

        export_btn = QPushButton("📊 Export to Excel")
        export_btn.clicked.connect(self._export_to_excel)
        header.addWidget(export_btn)

        main_layout.addLayout(header)

        # Key metrics grid
        self.metrics_grid = QGridLayout()
        self.metrics_grid.setSpacing(15)
        main_layout.addLayout(self.metrics_grid)

        # Aging analysis section
        aging_label = QLabel("Aging Analysis")
        aging_label.setStyleSheet("font-size: 18px; font-weight: bold; margin-top: 20px;")
        main_layout.addWidget(aging_label)

        self.aging_table = QTableWidget()
        self.aging_table.setMaximumHeight(200)
        main_layout.addWidget(self.aging_table)

        # Customer risk analysis section
        risk_label = QLabel("High-Risk Customers")
        risk_label.setStyleSheet("font-size: 18px; font-weight: bold; margin-top: 20px;")
        main_layout.addWidget(risk_label)

        self.risk_table = QTableWidget()
        self.risk_table.setMaximumHeight(250)
        main_layout.addWidget(self.risk_table)

        main_layout.addStretch()

    def refresh(self):
        """Refresh analytics data"""
        try:
            from ..models.database import Invoice, Customer, InvoiceStatus, AgingBucket, CommunicationLog
            from datetime import date

            session = self.db_manager.get_session()

            # Calculate key metrics

            # 1. Days Sales Outstanding (DSO)
            open_invoices = session.query(Invoice).filter(
                Invoice.status.in_([InvoiceStatus.OPEN, InvoiceStatus.OVERDUE, InvoiceStatus.PARTIALLY_PAID])
            ).all()

            if open_invoices:
                total_ar = sum(inv.amount_outstanding for inv in open_invoices)
                avg_days = sum(inv.days_outstanding for inv in open_invoices) / len(open_invoices)
                dso = avg_days
            else:
                total_ar = 0
                dso = 0

            # 2. Collection Effectiveness Index (CEI)
            # This is a simplified version
            total_invoices = session.query(Invoice).count()
            paid_invoices = session.query(Invoice).filter(Invoice.status == InvoiceStatus.PAID).count()
            collection_rate = (paid_invoices / total_invoices * 100) if total_invoices > 0 else 0

            # 3. Average Days to Pay
            paid_invoices_list = session.query(Invoice).filter(
                Invoice.status == InvoiceStatus.PAID
            ).limit(100).all()

            if paid_invoices_list:
                avg_days_to_pay = sum(
                    (inv.invoice_date - inv.due_date).days if inv.invoice_date and inv.due_date else 0
                    for inv in paid_invoices_list
                ) / len(paid_invoices_list)
            else:
                avg_days_to_pay = 0

            # 4. Overdue percentage
            overdue_count = session.query(Invoice).filter(
                Invoice.status == InvoiceStatus.OVERDUE
            ).count()
            overdue_percentage = (overdue_count / total_invoices * 100) if total_invoices > 0 else 0

            # 5. Total receivables
            total_receivables = sum(inv.amount_outstanding for inv in open_invoices)

            # 6. Average invoice value
            if open_invoices:
                avg_invoice = total_receivables / len(open_invoices)
            else:
                avg_invoice = 0

            # Clear and populate metrics grid
            for i in reversed(range(self.metrics_grid.count())):
                widget = self.metrics_grid.itemAt(i).widget()
                if widget:
                    widget.setParent(None)

            self.metrics_grid.addWidget(
                ReportCard("Days Sales Outstanding", f"{dso:.0f} days", "Average aging"),
                0, 0
            )

            self.metrics_grid.addWidget(
                ReportCard("Collection Rate", f"{collection_rate:.1f}%", f"{paid_invoices} of {total_invoices} paid"),
                0, 1
            )

            self.metrics_grid.addWidget(
                ReportCard("Total Receivables", f"${total_receivables:,.2f}", f"{len(open_invoices)} open invoices"),
                0, 2
            )

            self.metrics_grid.addWidget(
                ReportCard("Overdue Rate", f"{overdue_percentage:.1f}%", f"{overdue_count} overdue"),
                1, 0
            )

            self.metrics_grid.addWidget(
                ReportCard("Avg Invoice Value", f"${avg_invoice:,.2f}", "Per invoice"),
                1, 1
            )

            customers_with_balance = session.query(Customer).filter(Customer.current_balance > 0).count()
            self.metrics_grid.addWidget(
                ReportCard("Active Customers", str(customers_with_balance), "With outstanding balance"),
                1, 2
            )

            # Populate aging analysis table
            self.aging_table.setColumnCount(5)
            self.aging_table.setHorizontalHeaderLabels([
                "Aging Bucket", "# Invoices", "Amount", "% of Total", "Avg Days"
            ])
            self.aging_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

            aging_data = []
            for bucket in AgingBucket:
                invoices = session.query(Invoice).filter(
                    Invoice.aging_bucket == bucket,
                    Invoice.status.in_([InvoiceStatus.OPEN, InvoiceStatus.OVERDUE, InvoiceStatus.PARTIALLY_PAID])
                ).all()

                count = len(invoices)
                amount = sum(inv.amount_outstanding for inv in invoices)
                percentage = (amount / total_receivables * 100) if total_receivables > 0 else 0
                avg_days = sum(inv.days_outstanding for inv in invoices) / count if count > 0 else 0

                aging_data.append({
                    'bucket': bucket.value,
                    'count': count,
                    'amount': amount,
                    'percentage': percentage,
                    'avg_days': avg_days
                })

            self.aging_table.setRowCount(len(aging_data))
            for row, data in enumerate(aging_data):
                self.aging_table.setItem(row, 0, QTableWidgetItem(data['bucket']))
                self.aging_table.setItem(row, 1, QTableWidgetItem(str(data['count'])))

                amount_item = QTableWidgetItem(f"${data['amount']:,.2f}")
                amount_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.aging_table.setItem(row, 2, amount_item)

                pct_item = QTableWidgetItem(f"{data['percentage']:.1f}%")
                pct_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.aging_table.setItem(row, 3, pct_item)

                self.aging_table.setItem(row, 4, QTableWidgetItem(f"{data['avg_days']:.0f}"))

            # Populate high-risk customers table
            self.risk_table.setColumnCount(5)
            self.risk_table.setHorizontalHeaderLabels([
                "Customer", "Balance", "# Overdue", "Oldest Invoice", "Risk Score"
            ])
            self.risk_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

            # Find high-risk customers (high balance + overdue invoices)
            customers = session.query(Customer).filter(
                Customer.current_balance > 0
            ).order_by(Customer.current_balance.desc()).limit(20).all()

            risk_customers = []
            for customer in customers:
                overdue_invoices = session.query(Invoice).filter(
                    Invoice.customer_id == customer.id,
                    Invoice.status == InvoiceStatus.OVERDUE
                ).all()

                if overdue_invoices:
                    oldest_days = max(inv.days_outstanding for inv in overdue_invoices)
                    # Simple risk score: balance weight + overdue weight + age weight
                    risk_score = (
                        min(customer.current_balance / 10000 * 30, 30) +  # Up to 30 points
                        min(len(overdue_invoices) * 10, 40) +  # Up to 40 points
                        min(oldest_days / 10, 30)  # Up to 30 points
                    )

                    risk_customers.append({
                        'name': customer.company_name,
                        'balance': customer.current_balance,
                        'overdue_count': len(overdue_invoices),
                        'oldest_days': oldest_days,
                        'risk_score': risk_score
                    })

            # Sort by risk score
            risk_customers.sort(key=lambda x: x['risk_score'], reverse=True)

            self.risk_table.setRowCount(len(risk_customers))
            for row, cust in enumerate(risk_customers):
                self.risk_table.setItem(row, 0, QTableWidgetItem(cust['name']))

                balance_item = QTableWidgetItem(f"${cust['balance']:,.2f}")
                balance_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.risk_table.setItem(row, 1, balance_item)

                self.risk_table.setItem(row, 2, QTableWidgetItem(str(cust['overdue_count'])))
                self.risk_table.setItem(row, 3, QTableWidgetItem(f"{cust['oldest_days']} days"))

                risk_item = QTableWidgetItem(f"{cust['risk_score']:.0f}")
                risk_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

                # Color code risk
                if cust['risk_score'] >= 70:
                    risk_item.setBackground(Qt.GlobalColor.red)
                    risk_item.setForeground(Qt.GlobalColor.white)
                elif cust['risk_score'] >= 50:
                    risk_item.setBackground(Qt.GlobalColor.yellow)

                self.risk_table.setItem(row, 4, risk_item)

            session.close()
            logger.info("Analytics refreshed successfully")

        except Exception as e:
            logger.error(f"Failed to refresh analytics: {e}")

    def _export_to_excel(self):
        """Export analytics to Excel file"""
        try:
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Export Analytics Report",
                f"analytics_report_{datetime.now().strftime('%Y%m%d')}.csv",
                "CSV Files (*.csv)"
            )

            if not file_path:
                return

            from ..models.database import Invoice, Customer, InvoiceStatus, AgingBucket

            session = self.db_manager.get_session()

            # Create CSV content
            lines = []
            lines.append("RECEIVABLES ANALYTICS REPORT")
            lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            lines.append("")

            # Aging Analysis
            lines.append("AGING ANALYSIS")
            lines.append("Bucket,Count,Amount,Percentage")

            total_receivables = session.query(Invoice).filter(
                Invoice.status.in_([InvoiceStatus.OPEN, InvoiceStatus.OVERDUE, InvoiceStatus.PARTIALLY_PAID])
            ).with_entities(Invoice.amount_outstanding).all()
            total = sum(inv.amount_outstanding for inv in total_receivables)

            for bucket in AgingBucket:
                invoices = session.query(Invoice).filter(
                    Invoice.aging_bucket == bucket,
                    Invoice.status.in_([InvoiceStatus.OPEN, InvoiceStatus.OVERDUE, InvoiceStatus.PARTIALLY_PAID])
                ).all()

                count = len(invoices)
                amount = sum(inv.amount_outstanding for inv in invoices)
                percentage = (amount / total * 100) if total > 0 else 0

                lines.append(f"{bucket.value},{count},${amount:.2f},{percentage:.1f}%")

            lines.append("")
            lines.append("CUSTOMER DETAILS")
            lines.append("Customer,Balance,Open Invoices,Oldest Days")

            customers = session.query(Customer).filter(Customer.current_balance > 0).all()
            for customer in customers:
                open_invoices = session.query(Invoice).filter(
                    Invoice.customer_id == customer.id,
                    Invoice.status.in_([InvoiceStatus.OPEN, InvoiceStatus.OVERDUE, InvoiceStatus.PARTIALLY_PAID])
                ).all()

                oldest_days = max((inv.days_outstanding for inv in open_invoices), default=0)

                lines.append(
                    f"{customer.company_name},${customer.current_balance:.2f},"
                    f"{len(open_invoices)},{oldest_days}"
                )

            # Write to file
            with open(file_path, 'w') as f:
                f.write('\n'.join(lines))

            session.close()

            QMessageBox.information(
                self,
                "Export Successful",
                f"Analytics report exported to:\n{file_path}"
            )

            logger.info(f"Analytics exported to {file_path}")

        except Exception as e:
            logger.error(f"Failed to export analytics: {e}")
            QMessageBox.critical(
                self,
                "Export Failed",
                f"Failed to export analytics:\n{str(e)}"
            )
