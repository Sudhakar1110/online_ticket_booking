import frappe
from frappe.utils import flt


def execute(filters=None):
    filters = filters or {}

    columns = [
        {"label": "Event",         "fieldname": "event",          "fieldtype": "Link",     "options": "Event", "width": 180},
        {"label": "Event Date",    "fieldname": "event_date",     "fieldtype": "Date",     "width": 110},
        {"label": "Ticket Type",   "fieldname": "ticket_type",    "fieldtype": "Data",     "width": 140},
        {"label": "Qty Sold",      "fieldname": "qty_sold",       "fieldtype": "Int",      "width": 90},
        {"label": "Revenue (₹)",   "fieldname": "revenue",        "fieldtype": "Currency", "width": 130},
        {"label": "Bookings",      "fieldname": "booking_count",  "fieldtype": "Int",      "width": 90},
        {"label": "Avg Ticket ₹",  "fieldname": "avg_price",      "fieldtype": "Currency", "width": 120},
    ]

    conditions = "b.status IN ('Confirmed','Paid')"
    params     = []

    if filters.get("event"):
        conditions += " AND b.event = %s"
        params.append(filters["event"])
    if filters.get("from_date"):
        conditions += " AND b.event_date >= %s"
        params.append(filters["from_date"])
    if filters.get("to_date"):
        conditions += " AND b.event_date <= %s"
        params.append(filters["to_date"])

    data = frappe.db.sql(f"""
        SELECT
            b.event,
            b.event_date,
            bi.ticket_type,
            SUM(bi.quantity)           AS qty_sold,
            SUM(bi.subtotal)           AS revenue,
            COUNT(DISTINCT b.name)     AS booking_count,
            AVG(bi.price)              AS avg_price
        FROM `tabBooking Item` bi
        JOIN `tabBooking` b ON b.name = bi.parent
        WHERE {conditions}
        GROUP BY b.event, b.event_date, bi.ticket_type
        ORDER BY b.event_date DESC, b.event, bi.ticket_type
    """, params, as_dict=True)

    return columns, data
