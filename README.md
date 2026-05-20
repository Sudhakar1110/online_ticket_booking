# Online Ticket Booking – Frappe / ERPNext v15

A full-featured **Online Ticket Booking** custom Frappe app that integrates seamlessly with ERPNext v15.

## Features
| Feature | Details |
|---|---|
| Event Management | Create events with venue, date, capacity, image |
| Ticket Types | Multiple tiers (VIP, General, Student…) per event |
| Seat Inventory | Real-time available seat tracking |
| Booking Flow | Multi-passenger booking with QR-code tickets |
| Payment Integration | ERPNext Payment Entry / Razorpay webhook ready |
| Auto-cancellation | Unpaid bookings cancelled after configurable TTL |
| Email Notifications | Confirmation, reminder, cancellation emails |
| Customer Portal | `/events`, `/my-bookings`, `/booking/<id>` |
| Reports | Booking Summary report with charts |
| Role-based Access | Booking Admin / Event Organizer / Ticket Customer |

## Installation

```bash
# Inside your frappe-bench directory
bench get-app online_ticket_booking https://github.com/yourorg/online_ticket_booking
bench --site your-site install-app online_ticket_booking
bench migrate
bench build --app online_ticket_booking
bench restart
```

## DocTypes
- **Event** – Master event record
- **Ticket Type** – Child / standalone tier per event
- **Booking** – Customer booking header
- **Booking Item** – Passenger + ticket line
- **Passenger** – Individual traveller / attendee details
- **Payment** – Payment record linked to Booking

## Folder Structure
```
online_ticket_booking/
├── online_ticket_booking/
│   ├── event/
│   ├── ticket_type/
│   ├── booking/
│   ├── passenger/
│   ├── payment/
│   ├── public/
│   │   ├── css/
│   │   └── js/
│   ├── templates/pages/
│   ├── reports/booking_summary/
│   ├── api.py
│   ├── tasks.py
│   ├── hooks.py
│   └── utils/
├── setup.py
├── requirements.txt
└── README.md
```

## License
MIT
