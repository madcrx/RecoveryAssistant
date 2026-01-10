import { useEffect, useState } from 'react'
import {
  Box,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
  Chip,
  CircularProgress,
} from '@mui/material'
import axios from 'axios'
import { format } from 'date-fns'

interface Invoice {
  id: number
  invoice_number: string
  customer_id: number
  invoice_date: string
  due_date: string
  amount_outstanding: number
  status: string
  aging_bucket: string
  days_outstanding: number
}

const getStatusColor = (status: string) => {
  switch (status) {
    case 'paid':
      return 'success'
    case 'open':
      return 'info'
    case 'overdue':
      return 'error'
    case 'disputed':
      return 'warning'
    default:
      return 'default'
  }
}

const getAgingColor = (bucket: string) => {
  switch (bucket) {
    case 'current':
      return 'success'
    case '0-30':
      return 'info'
    case '31-60':
      return 'warning'
    case '61-90':
    case '90+':
      return 'error'
    default:
      return 'default'
  }
}

export default function Invoices() {
  const [invoices, setInvoices] = useState<Invoice[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchInvoices()
  }, [])

  const fetchInvoices = async () => {
    try {
      const response = await axios.get('/api/v1/receivables/')
      setInvoices(response.data.invoices)
    } catch (error) {
      console.error('Failed to fetch invoices:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    )
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Invoices
      </Typography>

      <TableContainer component={Paper} sx={{ mt: 3 }}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Invoice #</TableCell>
              <TableCell>Invoice Date</TableCell>
              <TableCell>Due Date</TableCell>
              <TableCell align="right">Amount</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Aging</TableCell>
              <TableCell align="right">Days Out</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {invoices.map((invoice) => (
              <TableRow key={invoice.id}>
                <TableCell>{invoice.invoice_number}</TableCell>
                <TableCell>{format(new Date(invoice.invoice_date), 'MM/dd/yyyy')}</TableCell>
                <TableCell>{format(new Date(invoice.due_date), 'MM/dd/yyyy')}</TableCell>
                <TableCell align="right">
                  ${invoice.amount_outstanding.toLocaleString('en-US', { minimumFractionDigits: 2 })}
                </TableCell>
                <TableCell>
                  <Chip
                    label={invoice.status}
                    color={getStatusColor(invoice.status) as any}
                    size="small"
                  />
                </TableCell>
                <TableCell>
                  <Chip
                    label={invoice.aging_bucket}
                    color={getAgingColor(invoice.aging_bucket) as any}
                    size="small"
                  />
                </TableCell>
                <TableCell align="right">{invoice.days_outstanding}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  )
}
