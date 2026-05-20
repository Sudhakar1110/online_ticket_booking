"""Scheduled background tasks."""
import frappe
from frappe.utils import now_datetime, add_days, today, get_datetime


def auto_cancel_unpaid_bookings():
    """
    Runs every 10 minutes.
    Cancel Draft/Confirmed bookings that haven't been paid within 30 minutes.
    """
    threshold = frappe.utils.add_to_date(now_datetime(), minutes=-30)
    stale = frappe.get_all(
        "Booking",
        filters={
            "status":         ["in", ["Draft", "Confirmed"]],
            "payment_status": ["in", ["", "Unpaid"]],
            "booking_date":   ["<", threshold],
        },
        fields=["name"],
    )
    for b in stale:
        try:
            doc = frappe.get_doc("Booking", b.name)
            doc.cancellation_reason = "Auto-cancelled: payment timeout (30 min)"
            if doc.docstatus == 1:
                doc.cancel()
            else:
                doc.status = "Expired"
                doc.save(ignore_permissions=True)
            frappe.db.commit()
            frappe.logger().info(f"Auto-cancelled booking: {b.name}")
        except Exception as e:
            frappe.log_error(f"Auto-cancel failed for {b.name}: {e}", "Auto Cancel Booking")


def send_upcoming_event_reminders():
    """
    Runs every hour.
    Send reminder email 24 hours before the event.
    """
    tomorrow = add_days(today(), 1)
    bookings = frappe.get_all(
        "Booking",
        filters={
            "event_date": tomorrow,
            "status":     ["in", ["Confirmed", "Paid"]],
        },
        fields=["name", "customer_email", "customer_name", "event", "event_date", "venue"],
    )
    for b in bookings:
        try:
            frappe.sendmail(
                recipients=[b.customer_email],
                subject=f"Reminder: {b.event} is tomorrow!",
                message=f"""
                <h3>Event Reminder</h3>
                <p>Dear {b.customer_name},</p>
                <p>Your event <strong>{b.event}</strong> is tomorrow on
                   <strong>{b.event_date}</strong> at <strong>{b.venue}</strong>.</p>
                <p>Please carry your booking confirmation / QR code.</p>
                <p>Booking ID: <strong>{b.name}</strong></p>
                """,
            )
        except Exception as e:
            frappe.log_error(f"Reminder email failed for {b.name}: {e}", "Event Reminder")
