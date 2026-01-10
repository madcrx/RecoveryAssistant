import { useEffect, useState } from 'react'
import {
  Box,
  Card,
  CardContent,
  Grid,
  Typography,
  CircularProgress,
} from '@mui/material'
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts'
import axios from 'axios'

interface DashboardMetrics {
  total_outstanding: number
  aging_distribution: {
    amounts: Record<string, number>
    counts: Record<string, number>
  }
  payments_this_month: number
  average_days_to_pay: number
  collection_rate_30_days: number
  high_risk_customers: number
}

const COLORS = ['#4caf50', '#2196f3', '#ff9800', '#f44336', '#9c27b0']

export default function Dashboard() {
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchMetrics()
  }, [])

  const fetchMetrics = async () => {
    try {
      const response = await axios.get('/api/v1/analytics/dashboard')
      setMetrics(response.data)
    } catch (error) {
      console.error('Failed to fetch metrics:', error)
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

  if (!metrics) {
    return <Typography>Failed to load dashboard metrics</Typography>
  }

  const agingData = Object.entries(metrics.aging_distribution.amounts).map(
    ([bucket, amount]) => ({
      name: bucket,
      value: amount,
    })
  )

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Collection Dashboard
      </Typography>

      <Grid container spacing={3}>
        {/* Key Metrics Cards */}
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Total Outstanding
              </Typography>
              <Typography variant="h5">
                ${metrics.total_outstanding.toLocaleString('en-US', { minimumFractionDigits: 2 })}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Collection Rate (30d)
              </Typography>
              <Typography variant="h5" color={metrics.collection_rate_30_days >= 99 ? 'success.main' : 'warning.main'}>
                {metrics.collection_rate_30_days.toFixed(1)}%
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Payments This Month
              </Typography>
              <Typography variant="h5">
                ${metrics.payments_this_month.toLocaleString('en-US', { minimumFractionDigits: 2 })}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Avg Days to Pay
              </Typography>
              <Typography variant="h5">
                {metrics.average_days_to_pay.toFixed(0)} days
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        {/* Aging Distribution Chart */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Aging Distribution
              </Typography>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={agingData}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, value }) =>
                      `${name}: $${value.toLocaleString()}`
                    }
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {agingData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>

        {/* Additional Metrics */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Risk Summary
              </Typography>
              <Box mt={2}>
                <Typography>
                  High Risk Customers: {metrics.high_risk_customers}
                </Typography>
                <Typography mt={1}>
                  DSO (Days Sales Outstanding): {metrics.average_days_to_pay.toFixed(0)} days
                </Typography>
                <Typography mt={1}>
                  CEI (Collection Effectiveness Index): {metrics.collection_rate_30_days.toFixed(1)}%
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  )
}
