"""
Xero Integration Service

Connects to Xero accounting software to sync receivables data.
"""

from xero_python.api_client import ApiClient
from xero_python.api_client.configuration import Configuration
from xero_python.api_client.oauth2 import OAuth2Token
from xero_python.accounting import AccountingApi
from xero_python.identity import IdentityApi
from typing import List, Dict, Optional
from datetime import datetime, date
import logging

logger = logging.getLogger(__name__)


class XeroClient:
    """Integration with Xero accounting software"""

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: str = "http://localhost:8080/callback"
    ):
        """
        Initialize Xero client

        Args:
            client_id: Xero OAuth2 client ID
            client_secret: Xero OAuth2 client secret
            redirect_uri: OAuth2 redirect URI
        """

        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri

        # Configuration
        self.config = Configuration(
            oauth2_token=OAuth2Token(
                client_id=client_id,
                client_secret=client_secret
            )
        )

        self.api_client = None
        self.accounting_api = None
        self.tenant_id = None
        self.is_connected = False

    def get_authorization_url(self) -> str:
        """
        Get OAuth2 authorization URL for user to authenticate

        Returns:
            Authorization URL
        """

        api_client = ApiClient(
            self.config,
            pool_threads=1
        )

        # Scopes for accounting data
        scopes = [
            "offline_access",
            "accounting.transactions.read",
            "accounting.contacts.read",
            "accounting.reports.read"
        ]

        authorization_url = api_client.authorization_url(
            self.redirect_uri,
            scope=scopes
        )

        return authorization_url

    def connect_with_code(self, authorization_code: str) -> bool:
        """
        Complete OAuth2 flow with authorization code

        Args:
            authorization_code: Code from OAuth2 callback

        Returns:
            Success status
        """

        try:
            self.api_client = ApiClient(
                self.config,
                pool_threads=1
            )

            # Exchange code for token
            token = self.api_client.get_oauth2_token(
                authorization_code,
                self.redirect_uri
            )

            # Get tenant (organization) ID
            identity_api = IdentityApi(self.api_client)
            connections = identity_api.get_connections()

            if connections:
                self.tenant_id = connections[0].tenant_id
                self.accounting_api = AccountingApi(self.api_client)
                self.is_connected = True

                logger.info(f"Connected to Xero tenant: {self.tenant_id}")
                return True
            else:
                logger.error("No Xero connections found")
                return False

        except Exception as e:
            logger.error(f"Failed to connect to Xero: {e}")
            return False

    def sync_invoices(
        self,
        status: str = "AUTHORISED",
        where_clause: Optional[str] = None
    ) -> List[Dict]:
        """
        Sync invoices from Xero

        Args:
            status: Invoice status filter (DRAFT, SUBMITTED, AUTHORISED, PAID, VOIDED)
            where_clause: Custom where clause for filtering

        Returns:
            List of invoice data dicts
        """

        if not self.is_connected:
            logger.error("Not connected to Xero")
            return []

        try:
            # Default filter for unpaid invoices
            if not where_clause:
                where_clause = f'Status=="{status}" AND Type=="ACCREC" AND AmountDue>0'

            # Fetch invoices
            invoices = self.accounting_api.get_invoices(
                self.tenant_id,
                where=where_clause,
                order="DueDate ASC"
            )

            invoice_list = []

            for invoice in invoices.invoices:
                invoice_data = self._parse_invoice(invoice)
                invoice_list.append(invoice_data)

            logger.info(f"Synced {len(invoice_list)} invoices from Xero")

            return invoice_list

        except Exception as e:
            logger.error(f"Failed to sync invoices: {e}")
            return []

    def sync_contacts(self) -> List[Dict]:
        """
        Sync customer/contact data from Xero

        Returns:
            List of contact data dicts
        """

        if not self.is_connected:
            logger.error("Not connected to Xero")
            return []

        try:
            contacts = self.accounting_api.get_contacts(self.tenant_id)

            contact_list = []

            for contact in contacts.contacts:
                contact_data = self._parse_contact(contact)
                contact_list.append(contact_data)

            logger.info(f"Synced {len(contact_list)} contacts from Xero")

            return contact_list

        except Exception as e:
            logger.error(f"Failed to sync contacts: {e}")
            return []

    def get_aged_receivables_report(self) -> Dict:
        """
        Get aged receivables report from Xero

        Returns:
            Aged receivables data
        """

        if not self.is_connected:
            logger.error("Not connected to Xero")
            return {}

        try:
            # Get aged receivables by contact
            report = self.accounting_api.get_report_aged_receivables_by_contact(
                self.tenant_id,
                date=datetime.now().date(),
                from_date=None,
                to_date=None
            )

            # Parse report data
            aged_data = self._parse_aged_receivables_report(report)

            logger.info("Retrieved aged receivables report from Xero")

            return aged_data

        except Exception as e:
            logger.error(f"Failed to get aged receivables report: {e}")
            return {}

    def _parse_invoice(self, invoice) -> Dict:
        """Parse Xero invoice object to dict"""

        # Calculate days overdue
        due_date = invoice.due_date.date() if invoice.due_date else date.today()
        days_overdue = max(0, (date.today() - due_date).days)

        # Determine aging bucket
        if days_overdue == 0:
            aging_bucket = 'current'
        elif days_overdue <= 30:
            aging_bucket = '0-30'
        elif days_overdue <= 60:
            aging_bucket = '31-60'
        elif days_overdue <= 90:
            aging_bucket = '61-90'
        else:
            aging_bucket = '90+'

        return {
            'invoice_number': invoice.invoice_number,
            'invoice_id': invoice.invoice_id,
            'customer_id': invoice.contact.contact_id if invoice.contact else None,
            'customer_name': invoice.contact.name if invoice.contact else 'Unknown',
            'invoice_date': invoice.date.date() if invoice.date else None,
            'due_date': due_date,
            'original_amount': float(invoice.total or 0),
            'amount_paid': float(invoice.amount_paid or 0),
            'amount_outstanding': float(invoice.amount_due or 0),
            'status': invoice.status,
            'currency': invoice.currency_code,
            'days_overdue': days_overdue,
            'aging_bucket': aging_bucket,
            'reference': invoice.reference,
            'xero_invoice_id': invoice.invoice_id,
        }

    def _parse_contact(self, contact) -> Dict:
        """Parse Xero contact object to dict"""

        # Get primary email and phone
        email = None
        phone = None

        if contact.email_address:
            email = contact.email_address

        if contact.phones:
            for phone_obj in contact.phones:
                if phone_obj.phone_type == "DEFAULT":
                    phone = phone_obj.phone_number
                    break

        # Get primary contact person
        contact_name = None
        if contact.contact_persons:
            contact_name = f"{contact.contact_persons[0].first_name or ''} {contact.contact_persons[0].last_name or ''}".strip()

        return {
            'customer_id': contact.contact_id,
            'customer_name': contact.name,
            'email': email,
            'phone': phone,
            'contact_name': contact_name,
            'is_customer': contact.is_customer,
            'accounts_receivable_outstanding': float(contact.accounts_receivable_tax_inclusive or 0),
            'xero_contact_id': contact.contact_id,
        }

    def _parse_aged_receivables_report(self, report) -> Dict:
        """Parse aged receivables report"""

        # This is a simplified parser
        # Full implementation would parse the report structure

        try:
            aged_data = {
                'total_outstanding': 0.0,
                'current': 0.0,
                '0-30': 0.0,
                '31-60': 0.0,
                '61-90': 0.0,
                '90+': 0.0,
                'by_customer': []
            }

            # Parse report rows
            # Xero report structure is complex, this is a placeholder
            # Real implementation would iterate through report.rows

            return aged_data

        except Exception as e:
            logger.error(f"Failed to parse aged receivables report: {e}")
            return {}

    def get_invoice_pdf(self, invoice_id: str, file_path: str) -> bool:
        """
        Download invoice PDF from Xero

        Args:
            invoice_id: Xero invoice ID
            file_path: Path to save PDF

        Returns:
            Success status
        """

        if not self.is_connected:
            logger.error("Not connected to Xero")
            return False

        try:
            # Get invoice as PDF
            pdf_data = self.accounting_api.get_invoice_as_pdf(
                self.tenant_id,
                invoice_id
            )

            # Save to file
            with open(file_path, 'wb') as f:
                f.write(pdf_data)

            logger.info(f"Invoice PDF downloaded: {invoice_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to download invoice PDF: {e}")
            return False

    def create_payment(
        self,
        invoice_id: str,
        amount: float,
        date: date,
        reference: str = ""
    ) -> bool:
        """
        Record payment in Xero

        Args:
            invoice_id: Xero invoice ID
            amount: Payment amount
            date: Payment date
            reference: Payment reference

        Returns:
            Success status
        """

        if not self.is_connected:
            logger.error("Not connected to Xero")
            return False

        try:
            from xero_python.accounting import Payment, Invoice

            # Create payment object
            payment = Payment(
                invoice=Invoice(invoice_id=invoice_id),
                account=None,  # Will use default bank account
                date=datetime.combine(date, datetime.min.time()),
                amount=amount,
                reference=reference
            )

            # Create payment in Xero
            self.accounting_api.create_payment(
                self.tenant_id,
                payment
            )

            logger.info(f"Payment recorded in Xero: {invoice_id}, ${amount}")
            return True

        except Exception as e:
            logger.error(f"Failed to create payment in Xero: {e}")
            return False

    def disconnect(self):
        """Disconnect from Xero"""

        self.api_client = None
        self.accounting_api = None
        self.tenant_id = None
        self.is_connected = False

        logger.info("Disconnected from Xero")


# Factory function
def create_xero_client(client_id: str, client_secret: str) -> XeroClient:
    """Create and return XeroClient instance"""

    return XeroClient(client_id, client_secret)
