# RecoveryAssistant - Quick Start Guide

Get up and running with RecoveryAssistant in 10 minutes!

## What You'll Need

Before starting, have these ready:

1. ✅ **OpenAI API Key** (Required)
   - Sign up: https://platform.openai.com
   - Go to: API Keys → Create new secret key
   - Copy and save the key

2. ✅ **Microsoft Outlook** (Required)
   - Must be installed on your PC
   - Must be configured with your email account

3. ⚪ **Xero Credentials** (Optional)
   - Only needed if you want automatic invoice sync
   - Get from: https://developer.xero.com

4. ⚪ **Stripe API Keys** (Optional)
   - Only needed if you want payment processing
   - Get from: https://stripe.com/dashboard

## Step 1: Install RecoveryAssistant

1. **Download** `RecoveryAssistant_Setup.exe`

2. **Double-click** the installer

3. **Follow the wizard:**
   - Click "Next"
   - Accept the license
   - Choose installation location (default is fine)
   - Select shortcuts (Desktop is recommended)
   - Click "Install"

4. **Launch** when installation completes

⏱️ **Installation time:** 2 minutes

---

## Step 2: Initial Setup Wizard

When you first launch RecoveryAssistant, the setup wizard appears.

### 2.1 Welcome Screen

Click **"Next"** to begin.

### 2.2 OpenAI Configuration

1. Paste your **OpenAI API Key**
2. Select model: **GPT-4 Turbo** (recommended)
3. Click **"Test Connection"** to verify
4. Click **"Next"**

✅ **Required for AI-powered collection messages**

### 2.3 Microsoft Outlook

1. Click **"Test Outlook Connection"**
2. If successful, you'll see: ✅ Connected
3. Click **"Next"**

✅ **Used for sending emails from your account**

### 2.4 Xero Integration (Optional)

**Option A: Connect to Xero**
1. Enter **Client ID** and **Client Secret**
2. Click **"Connect to Xero"**
3. Browser opens → Log in to Xero
4. Click **"Allow"** to authorize
5. Return to RecoveryAssistant

**Option B: Skip for now**
- Click **"Skip"** if you'll import CSV/PDF instead
- You can connect Xero later in Settings

### 2.5 Stripe Configuration (Optional)

**Option A: Enable Payments**
1. Enter **Stripe API Key**
2. Click **"Test Connection"**
3. Click **"Next"**

**Option B: Skip for now**
- Click **"Skip"** if you'll add payment links manually
- You can configure Stripe later in Settings

### 2.6 Workflow Settings

Review default settings:
- **0-30 days**: Reminder every 7 days
- **31-60 days**: Reminder every 3 days
- **61-90 days**: Daily reminders
- **90+ days**: Daily + Escalation

Click **"Finish"** to complete setup.

⏱️ **Setup time:** 5 minutes

---

## Step 3: Import Your Receivables Data

Choose ONE of these import methods:

### Option A: Import PDF (Recommended)

1. Click **📁 Import → Import PDF**
2. Select your aged receivables PDF
3. Wait for extraction (30 seconds - 2 minutes)
4. Review import summary
5. Click **"Confirm"**

**Supported formats:**
- Standard aging reports
- Scanned documents (OCR)
- Most accounting software exports

### Option B: Import CSV

1. Click **📁 Import → Download CSV Template**
2. Open template in Excel
3. Fill in your data:
   - Customer name ✅
   - Invoice number ✅
   - Amount outstanding ✅
   - Due date ✅
   - Email
   - Phone
4. Save as CSV
5. Click **📁 Import → Import CSV**
6. Select your CSV file
7. Map columns if needed
8. Click **"Import"**

### Option C: Sync with Xero

1. Click **🔄 Sync Xero**
2. Select date range
3. Click **"Start Sync"**
4. Wait for completion (1-3 minutes)
5. Review synced data

⏱️ **Import time:** 2-5 minutes

---

## Step 4: Review Your Data

### Dashboard

View your collection metrics:
- 💰 **Total Outstanding**: $XXX,XXX
- 📊 **Aging Distribution**: Chart showing buckets
- ⚠️ **High Priority**: Invoices needing attention
- 📈 **Collection Rate**: Your performance

### Invoices Tab

- See all imported invoices
- Sort by aging, amount, customer
- Click invoice for details
- View communication history

### Customers Tab

- See all customers
- Payment scores (0-100)
- Risk levels (Low/Medium/High/Critical)
- Outstanding balances

---

## Step 5: Activate Automation

### Enable Workflows

1. Go to **Workflows → Settings**
2. Check **"Enable Automated Workflows"**
3. Set schedule: **Every 30 minutes** (default)
4. Click **"Save"**

### What Happens Automatically:

✅ **Every 30 minutes:**
- Checks all invoices for reminders due
- Sends emails via Outlook
- Updates aging buckets
- Escalates 90+ day invoices
- Tracks payment promises

✅ **For each invoice:**
- Generates personalized AI message
- Sends from YOUR Outlook account
- Includes payment link (if Stripe configured)
- Logs communication
- Schedules next follow-up

---

## Step 6: Daily Usage (5-10 minutes)

### Morning Routine

1. **Launch RecoveryAssistant** (or let it auto-start)

2. **Check Dashboard:**
   - Any new payments?
   - Any customer responses?
   - Any high-priority issues?

3. **Review Alerts:**
   - Disputed invoices
   - Failed emails
   - Payment promises due

4. **Take Action:**
   - Handle disputes manually
   - Update customer preferences
   - Send custom messages if needed

### Check Outlook

- Customer replies appear in your Outlook Inbox
- Review and respond as needed
- RecoveryAssistant tracks responses automatically

### Weekly Tasks

- Import new invoices (PDF/CSV/Xero sync)
- Review collection metrics
- Generate reports for management
- Backup database (File → Backup)

---

## Tips for Success

### 🎯 High Collection Rates

1. **Keep data current**
   - Sync Xero daily, OR
   - Import new invoices weekly

2. **Monitor high-risk customers**
   - Review weekly
   - Consider manual outreach

3. **Respond to inquiries quickly**
   - Check Outlook regularly
   - Update payment promises

4. **Offer payment plans**
   - For large invoices (>$10K)
   - Reduces disputes

### 🚀 Automation Best Practices

1. **Let the system run**
   - Don't micromanage
   - Trust the AI messaging

2. **Review metrics weekly**
   - Collection rate
   - Days Sales Outstanding (DSO)
   - Response rates

3. **Adjust workflows as needed**
   - Some industries need different schedules
   - Customize in Settings

### 💡 Email Best Practices

1. **Professional tone**
   - AI generates appropriate messages
   - Edit templates if needed

2. **Payment links**
   - Configure Stripe for best results
   - Makes payment frictionless

3. **Outlook signature**
   - Your signature is automatically included
   - Looks professional

---

## Common First-Day Tasks

### Import More Data
```
File → Import CSV
File → Import PDF
Integrations → Sync Xero
```

### Send Manual Email
```
Right-click invoice → Send Reminder
OR
Invoices tab → Select invoice → Actions → Send Email
```

### Update Customer Info
```
Customers tab → Double-click customer → Edit
```

### Generate Report
```
Analytics tab → Select report type → Export to Excel
```

### Backup Database
```
File → Backup Database → Choose location → Save
```

---

## Troubleshooting

### Emails Not Sending

1. Check Outlook is running
2. Run: **Integrations → Test Outlook Connection**
3. Check customer has valid email
4. Check logs: `%AppData%\RecoveryAssistant\Logs`

### PDF Import Fails

1. Check file size < 10MB
2. Try CSV import instead
3. For scanned PDFs, OCR takes longer (wait 2-3 minutes)

### Xero Sync Issues

1. Re-authenticate: **Settings → Integrations → Xero → Reconnect**
2. Check internet connection
3. Verify Xero credentials

### App Won't Start

1. Check Windows 10/11 64-bit
2. Check Python 3.11+ installed (if running from source)
3. Run as Administrator
4. Check logs for errors

---

## Getting Help

### Resources

- **📖 User Guide**: Start Menu → RecoveryAssistant → User Guide
- **📋 Logs**: `%AppData%\RecoveryAssistant\Logs`
- **💾 Database**: `Documents\RecoveryAssistant\receivables.db`
- **⚙️ Config**: `%AppData%\RecoveryAssistant\config.json`

### Support

- **GitHub Issues**: Report bugs and request features
- **Email**: support@recoveryassistant.com
- **Documentation**: Check README and ARCHITECTURE docs

---

## Next Steps

✅ **You're all set!**

RecoveryAssistant is now:
- Monitoring your receivables
- Sending automated reminders
- Tracking payments
- Escalating overdue accounts

**Let it run for a week**, then review your:
- Collection rate (target: 99%)
- Days Sales Outstanding (should decrease)
- Customer responses

**Enjoy your automated collections!** 🎉

---

**Version:** 1.0.0
**Last Updated:** 2024
