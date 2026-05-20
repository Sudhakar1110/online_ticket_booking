app_name           = "online_ticket_booking"
app_title          = "Online Ticket Booking"
app_publisher      = "Your Company"
app_description    = "Complete Online Ticket Booking System for ERPNext v15"
app_email          = "admin@yourcompany.com"
app_license        = "MIT"
app_version        = "1.0.0"

required_apps = ["frappe", "erpnext"]

app_include_css = ["/assets/online_ticket_booking/css/booking.css"]
app_include_js  = ["/assets/online_ticket_booking/js/booking.js"]

website_route_rules = [
    {"from_route": "/events",               "to_route": "events"},
    {"from_route": "/events/<event_id>",    "to_route": "event_detail"},
    {"from_route": "/booking/<booking_id>", "to_route": "booking_confirmation"},
    {"from_route": "/my-bookings",          "to_route": "my_bookings"},
]

doctype_js = {
    "Event"  : "public/js/event_form.js",
    "Booking": "public/js/booking_form.js",
}

scheduler_events = {
    "cron": {
        "*/10 * * * *": ["online_ticket_booking.tasks.auto_cancel_unpaid_bookings"],
        "0 * * * *"   : ["online_ticket_booking.tasks.send_upcoming_event_reminders"],
    }
}

permission_query_conditions = {
    "Booking": "online_ticket_booking.utils.permissions.get_booking_permission_query",
    "Payment" : "online_ticket_booking.utils.permissions.get_payment_permission_query",
}

fixtures = [
    {"dt": "Role",         "filters": [["name", "in", ["Booking Admin", "Event Organizer", "Ticket Customer"]]]},
    {"dt": "Custom Field", "filters": [["module", "=", "Online Ticket Booking"]]},
]
