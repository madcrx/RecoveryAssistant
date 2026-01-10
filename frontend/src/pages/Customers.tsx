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

interface Customer {
  id: number
  customer_number: string
  company_name: string
  contact_name: string | null
  email: string | null
  phone: string | null
  current_balance: number
  risk_level: string
  payment_score: number
}

const getRiskColor = (level: string) => {
  switch (level) {
    case 'low':
      return 'success'
    case 'medium':
      return 'info'
    case 'high':
      return 'warning'
    case 'critical':
      return 'error'
    default:
      return 'default'
  }
}

export default function Customers() {
  const [customers, setCustomers] = useState<Customer[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchCustomers()
  }, [])

  const fetchCustomers = async () => {
    try {
      const response = await axios.get('/api/v1/customers/')
      setCustomers(response.data.customers)
    } catch (error) {
      console.error('Failed to fetch customers:', error)
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
        Customers
      </Typography>

      <TableContainer component={Paper} sx={{ mt: 3 }}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Customer #</TableCell>
              <TableCell>Company Name</TableCell>
              <TableCell>Contact</TableCell>
              <TableCell>Email</TableCell>
              <TableCell align="right">Balance</TableCell>
              <TableCell>Risk Level</TableCell>
              <TableCell align="right">Payment Score</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {customers.map((customer) => (
              <TableRow key={customer.id}>
                <TableCell>{customer.customer_number}</TableCell>
                <TableCell>{customer.company_name}</TableCell>
                <TableCell>{customer.contact_name || '-'}</TableCell>
                <TableCell>{customer.email || '-'}</TableCell>
                <TableCell align="right">
                  ${customer.current_balance.toLocaleString('en-US', { minimumFractionDigits: 2 })}
                </TableCell>
                <TableCell>
                  <Chip
                    label={customer.risk_level}
                    color={getRiskColor(customer.risk_level) as any}
                    size="small"
                  />
                </TableCell>
                <TableCell align="right">{customer.payment_score.toFixed(0)}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  )
}
