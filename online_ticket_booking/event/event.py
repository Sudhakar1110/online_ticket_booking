import frappe
from frappe.model.document import Document
from frappe.utils import today, get_datetime


class Event(Document):

    def before_insert(self):
        self.available_seats = self.total_capacity

    def validate(self):
        self.validate_dates()
        self.validate_ticket_types()
        self.sync_available_seats()

    def validate_dates(self):
        if self.event_end_date and self.event_end_date < self.event_date:
            frappe.throw("Event End Date cannot be before Event Date.")

    def validate_ticket_types(self):
        total_allotted = sum(t.total_seats for t in self.ticket_types)
        if self.ticket_types and total_allotted > self.total_capacity:
            frappe.throw(
                f"Total seats allotted across ticket types ({total_allotted}) "
                f"exceeds Event Total Capacity ({self.total_capacity})."
            )
        names = [t.ticket_type_name for t in self.ticket_types]
        if len(names) != len(set(names)):
            frappe.throw("Duplicate ticket type names found.")

    def sync_available_seats(self):
        """Recalculate available seats from confirmed bookings."""
        confirmed = frappe.db.sql("""
            SELECT IFNULL(SUM(bi.quantity), 0)
            FROM `tabBooking Item` bi
            JOIN `tabBooking` b ON b.name = bi.parent
            WHERE b.event = %s AND b.status IN ('Confirmed', 'Paid')
        """, self.name)[0][0]
        self.available_seats = max(0, self.total_capacity - int(confirmed))

    @frappe.whitelist()
    def get_ticket_availability(self):
        """Return ticket type-wise availability."""
        result = []
        for tt in self.ticket_types:
            booked = frappe.db.sql("""
                SELECT IFNULL(SUM(bi.quantity), 0)
                FROM `tabBooking Item` bi
                JOIN `tabBooking` b ON b.name = bi.parent
                WHERE b.event = %s
                  AND bi.ticket_type = %s
                  AND b.status IN ('Confirmed','Paid')
            """, (self.name, tt.ticket_type_name))[0][0]
            result.append({
                "ticket_type": tt.ticket_type_name,
                "price":        tt.price,
                "total_seats":  tt.total_seats,
                "booked":       int(booked),
                "available":    max(0, tt.total_seats - int(booked)),
            })
        return result
