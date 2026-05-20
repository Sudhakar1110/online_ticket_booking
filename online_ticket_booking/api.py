"""
Public/internal API endpoints for Online Ticket Booking.
All methods are whitelisted and callable via
  /api/method/online_ticket_booking.api.<method_name>
"""
import frappe
import json
from frappe import _
from frappe.utils import flt, cint


# ═══════════════════════════  EVENTS  ═══════════════════════════════════════

@frappe.whitelist(allow_guest=True)
def get_events(category=None, city=None, from_date=None, to_date=None,
               search=None, featured_only=0, page=1, page_size=12):
    """Paginated, filterable list of active events."""
    filters = {"is_active": 1}
    if category:      filters["event_category"] = category
    if city:          filters["city"]            = city
    if from_date:     filters["event_date"]      = [">=", from_date]
    if to_date:       filters["event_date"]      = ["<=", to_date]
    if cint(featured_only): filters["is_featured"] = 1

    or_filters = None
    if search:
        or_filters = [
            ["event_name", "like", f"%{search}%"],
            ["venue",       "like", f"%{search}%"],
        ]

    events = frappe.get_all(
        "Event",
        filters=filters,
        or_filters=or_filters,
        fields=["name","event_name","event_category","event_date","event_end_date",
                "start_time","venue","city","state","total_capacity",
                "available_seats","event_image","is_featured"],
        order_by="event_date asc",
        start=(cint(page) - 1) * cint(page_size),
        page_length=cint(page_size),
    )

    total = frappe.db.count("Event", filters=filters)
    return {"events": events, "total": total, "page": cint(page), "page_size": cint(page_size)}


@frappe.whitelist(allow_guest=True)
def get_event_detail(event):
    """Full event detail with ticket type availability."""
    doc = frappe.get_doc("Event", event)
    data = doc.as_dict()
    data["ticket_availability"] = doc.get_ticket_availability()
    return data


# ═══════════════════════════  BOOKING  ══════════════════════════════════════

@frappe.whitelist()
def create_booking(event, customer_name, customer_email, customer_phone, items):
    """
    Create a new booking.
    items: JSON list of {ticket_type, quantity, passenger_name, passenger_age}
    """
    if isinstance(items, str):
        items = json.loads(items)

    # Lookup ticket prices from the event
    event_doc = frappe.get_doc("Event", event)
    price_map = {t.ticket_type_name: t.price for t in event_doc.ticket_types}

    doc = frappe.new_doc("Booking")
    doc.event          = event
    doc.customer_name  = customer_name
    doc.customer_email = customer_email
    doc.customer_phone = customer_phone
    doc.status         = "Draft"

    for item in items:
        tt    = item.get("ticket_type")
        price = price_map.get(tt)
        if not price:
            frappe.throw(_(f"Ticket type '{tt}' not found in event '{event}'."))
        doc.append("items", {
            "ticket_type":    tt,
            "price":          price,
            "quantity":       cint(item.get("quantity", 1)),
            "passenger_name": item.get("passenger_name", ""),
            "passenger_age":  cint(item.get("passenger_age") or 0),
        })

    doc.insert(ignore_permissions=True)
    frappe.db.commit()
    return {"booking": doc.name, "total_amount": doc.total_amount, "status": doc.status}


@frappe.whitelist()
def confirm_booking(booking):
    """Confirm a Draft booking (before payment)."""
    doc = frappe.get_doc("Booking", booking)
    _assert_booking_owner(doc)
    if doc.status != "Draft":
        frappe.throw(_(f"Booking already {doc.status}."))
    doc.status = "Confirmed"
    doc.submit()
    frappe.db.commit()
    return {"booking": doc.name, "status": doc.status, "qr_code": doc.qr_code}


@frappe.whitelist()
def cancel_booking(booking, reason=None):
    """Cancel a booking."""
    doc = frappe.get_doc("Booking", booking)
    _assert_booking_owner(doc)
    if doc.status in ("Cancelled", "Expired"):
        frappe.throw(_("Booking is already cancelled/expired."))
    doc.cancellation_reason = reason or ""
    doc.cancel()
    frappe.db.commit()
    return {"booking": doc.name, "status": "Cancelled"}


@frappe.whitelist()
def get_booking_detail(booking):
    """Return full booking detail."""
    doc = frappe.get_doc("Booking", booking)
    _assert_booking_owner(doc)
    return doc.as_dict()


@frappe.whitelist()
def get_my_bookings(page=1, page_size=10):
    """Return all bookings for the logged-in user."""
    bookings = frappe.get_all(
        "Booking",
        filters={"booked_by": frappe.session.user},
        fields=["name","event","event_date","venue","customer_name",
                "status","total_amount","payment_status","booking_date"],
        order_by="booking_date desc",
        start=(cint(page) - 1) * cint(page_size),
        page_length=cint(page_size),
    )
    total = frappe.db.count("Booking", {"booked_by": frappe.session.user})
    return {"bookings": bookings, "total": total}


# ═══════════════════════════  PAYMENT  ══════════════════════════════════════

@frappe.whitelist()
def initiate_payment(booking, payment_method):
    """Create a Payment record and return payment details."""
    booking_doc = frappe.get_doc("Booking", booking)
    _assert_booking_owner(booking_doc)

    if booking_doc.payment_status == "Paid":
        frappe.throw(_("Booking is already paid."))

    pay = frappe.new_doc("Payment")
    pay.booking        = booking
    pay.amount         = booking_doc.outstanding_amount
    pay.payment_method = payment_method
    pay.payment_status = "Initiated"
    pay.insert(ignore_permissions=True)
    frappe.db.commit()

    return {
        "payment": pay.name,
        "amount":  pay.amount,
        "booking": booking,
        "event":   booking_doc.event,
    }


@frappe.whitelist()
def record_payment_success(payment, transaction_id, gateway_response=None):
    """Mark a payment as successful (Razorpay / other gateway callback)."""
    pay = frappe.get_doc("Payment", payment)
    pay.transaction_id    = transaction_id
    pay.gateway_response  = gateway_response or ""
    pay.payment_status    = "Success"
    pay.save(ignore_permissions=True)
    pay.submit()
    frappe.db.commit()
    return {"payment": pay.name, "status": "Success"}


# ═══════════════════════════  ADMIN  ════════════════════════════════════════

@frappe.whitelist()
def get_event_analytics(event):
    """Booking analytics for an event (Booking Admin only)."""
    if "Booking Admin" not in frappe.get_roles():
        frappe.throw(_("Insufficient permissions."))

    rows = frappe.db.sql("""
        SELECT b.status, COUNT(b.name) AS bookings, SUM(b.total_amount) AS revenue
        FROM `tabBooking` b
        WHERE b.event = %s
        GROUP BY b.status
    """, event, as_dict=True)

    ticket_rows = frappe.db.sql("""
        SELECT bi.ticket_type, SUM(bi.quantity) AS qty_sold, SUM(bi.subtotal) AS revenue
        FROM `tabBooking Item` bi
        JOIN `tabBooking` b ON b.name = bi.parent
        WHERE b.event = %s AND b.status IN ('Confirmed','Paid')
        GROUP BY bi.ticket_type
    """, event, as_dict=True)

    return {"status_summary": rows, "ticket_summary": ticket_rows}


# ═══════════════════════════  HELPERS  ══════════════════════════════════════

def _assert_booking_owner(booking_doc):
    if frappe.session.user == "Administrator":
        return
    if "Booking Admin" in frappe.get_roles():
        return
    if booking_doc.booked_by != frappe.session.user:
        frappe.throw(_("You are not authorised to access this booking."))
