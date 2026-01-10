import { Routes, Route } from 'react-router-dom'
import { Box } from '@mui/material'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import UploadReport from './pages/UploadReport'
import Invoices from './pages/Invoices'
import Customers from './pages/Customers'
import Analytics from './pages/Analytics'

function App() {
  return (
    <Box sx={{ display: 'flex' }}>
      <Layout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/upload" element={<UploadReport />} />
          <Route path="/invoices" element={<Invoices />} />
          <Route path="/customers" element={<Customers />} />
          <Route path="/analytics" element={<Analytics />} />
        </Routes>
      </Layout>
    </Box>
  )
}

export default App
