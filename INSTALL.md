# Installation Guide

## Prerequisites
- Ubuntu 20.04 / 22.04
- Python 3.10+
- Node.js 18+
- MariaDB 10.6+
- Redis
- frappe-bench CLI
- ERPNext v15 installed site

## Steps

### 1. Get the app
```bash
cd /path/to/frappe-bench
bench get-app online_ticket_booking https://github.com/yourorg/online_ticket_booking
# OR for local development:
# bench get-app online_ticket_booking /path/to/local/online_ticket_booking
```

### 2. Install on your site
```bash
bench --site your-site-name install-app online_ticket_booking
```

### 3. Migrate database
```bash
bench --site your-site-name migrate
```

### 4. Build frontend assets
```bash
bench build --app online_ticket_booking
```

### 5. Restart
```bash
bench restart
# Or in production:
# sudo supervisorctl restart all
```

## Post-Installation Setup

1. **Assign Roles**: Go to `Settings > Role List` and assign:
   - `Booking Admin` – staff who manage events and bookings
   - `Event Organizer` – staff who create/manage events only
   - `Ticket Customer` – end customers (website users)

2. **Create your first Event**: Go to `Online Ticket Booking > Event > New`

3. **Test the portal**: Visit `https://your-site/events`

## Configuration

### Payment Gateway (Razorpay)
Set in `frappe.conf` or Site Config:
```json
{
  "razorpay_key": "rzp_live_xxx",
  "razorpay_secret": "xxx"
}
```

### Auto-cancel TTL
Default is 30 minutes. Edit `tasks.py` → `auto_cancel_unpaid_bookings()` to change.

## Uninstall
```bash
bench --site your-site-name uninstall-app online_ticket_booking
bench --site your-site-name migrate
```
