import { useEffect, useState } from 'react'
import {
  Box,
  Card,
  CardContent,
  Typography,
  CircularProgress,
} from '@mui/material'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import axios from 'axios'
import { format } from 'date-fns'

interface TrendData {
  period_days: number
  daily_payments: Array<{
    date: string
    amount: number
  }>
}

export default function Analytics() {
  const [trends, setTrends] = useState<TrendData | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchTrends()
  }, [])

  const fetchTrends = async () => {
    try {
      const response = await axios.get('/api/v1/analytics/trends?days=30')
      setTrends(response.data)
    } catch (error) {
      console.error('Failed to fetch trends:', error)
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

  if (!trends) {
    return <Typography>Failed to load analytics</Typography>
  }

  const chartData = trends.daily_payments.map(item => ({
    date: format(new Date(item.date), 'MM/dd'),
    amount: item.amount,
  }))

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Collection Analytics
      </Typography>

      <Card sx={{ mt: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Payment Trends (Last 30 Days)
          </Typography>
          <ResponsiveContainer width="100%" height={400}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis />
              <Tooltip formatter={(value: number) => `$${value.toLocaleString()}`} />
              <Legend />
              <Line
                type="monotone"
                dataKey="amount"
                stroke="#1976d2"
                strokeWidth={2}
                name="Payments"
              />
            </LineChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>
    </Box>
  )
}
