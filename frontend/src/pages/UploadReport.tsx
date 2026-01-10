import { useState } from 'react'
import {
  Box,
  Button,
  Card,
  CardContent,
  Typography,
  Alert,
  CircularProgress,
  Paper,
  List,
  ListItem,
  ListItemText,
} from '@mui/material'
import { CloudUpload as CloudUploadIcon } from '@mui/icons-material'
import axios from 'axios'

interface UploadResult {
  success: boolean
  filename: string
  report_date: string | null
  total_outstanding: number
  aging_summary: Record<string, number>
  statistics: {
    invoices_created: number
    invoices_updated: number
    customers_created: number
    total_invoices: number
  }
}

export default function UploadReport() {
  const [file, setFile] = useState<File | null>(null)
  const [uploading, setUploading] = useState(false)
  const [result, setResult] = useState<UploadResult | null>(null)
  const [error, setError] = useState<string | null>(null)

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.files && event.target.files[0]) {
      setFile(event.target.files[0])
      setResult(null)
      setError(null)
    }
  }

  const handleUpload = async () => {
    if (!file) return

    setUploading(true)
    setError(null)

    const formData = new FormData()
    formData.append('file', file)

    try {
      const response = await axios.post<UploadResult>(
        '/api/v1/receivables/upload',
        formData,
        {
          headers: { 'Content-Type': 'multipart/form-data' },
        }
      )

      setResult(response.data)
      setFile(null)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Upload failed. Please try again.')
    } finally {
      setUploading(false)
    }
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Upload Aged Receivables Report
      </Typography>

      <Card sx={{ mt: 3, maxWidth: 800 }}>
        <CardContent>
          <Typography variant="body1" gutterBottom>
            Upload a PDF aged receivables report to automatically extract customer and
            invoice data, then trigger AI-powered collection workflows.
          </Typography>

          <Box mt={3}>
            <input
              accept=".pdf"
              style={{ display: 'none' }}
              id="raised-button-file"
              type="file"
              onChange={handleFileChange}
            />
            <label htmlFor="raised-button-file">
              <Button
                variant="outlined"
                component="span"
                startIcon={<CloudUploadIcon />}
                fullWidth
              >
                Select PDF File
              </Button>
            </label>

            {file && (
              <Box mt={2}>
                <Typography variant="body2">Selected: {file.name}</Typography>
                <Button
                  variant="contained"
                  onClick={handleUpload}
                  disabled={uploading}
                  fullWidth
                  sx={{ mt: 2 }}
                >
                  {uploading ? <CircularProgress size={24} /> : 'Upload and Process'}
                </Button>
              </Box>
            )}
          </Box>

          {error && (
            <Alert severity="error" sx={{ mt: 2 }}>
              {error}
            </Alert>
          )}

          {result && (
            <Paper sx={{ mt: 3, p: 2, bgcolor: 'success.light' }}>
              <Typography variant="h6" gutterBottom>
                Upload Successful!
              </Typography>

              <List>
                <ListItem>
                  <ListItemText
                    primary="Total Outstanding"
                    secondary={`$${result.total_outstanding.toLocaleString()}`}
                  />
                </ListItem>
                <ListItem>
                  <ListItemText
                    primary="Invoices Processed"
                    secondary={`${result.statistics.total_invoices} (${result.statistics.invoices_created} new, ${result.statistics.invoices_updated} updated)`}
                  />
                </ListItem>
                <ListItem>
                  <ListItemText
                    primary="New Customers"
                    secondary={result.statistics.customers_created}
                  />
                </ListItem>
              </List>

              <Typography variant="body2" sx={{ mt: 2 }}>
                Automated collection workflows have been triggered in the background.
              </Typography>
            </Paper>
          )}
        </CardContent>
      </Card>
    </Box>
  )
}
