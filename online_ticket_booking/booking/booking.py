import frappe
import qrcode
import os
import base64
from io import BytesIO
from frappe.model.document import Document
from frappe.utils import now_datetime, flt, cint, get_url


class Booking(Document):

    # ── Lifecycle ────────────────────────────────────────────────────────

    def before_insert(self):
        self.booked_by   = frappe.session.user
        self.booking_date = now_datetime()

    def validate(self):
        self.calculate_totals()
        self.validate_seat_availability()

    def on_submit(self):
        self.status = "Confirmed"
        self.generate_qr_codes()
        self.send_confirmation_email()
        self._refresh_event_seats()

    def on_cancel(self):
        self.status = "Cancelled"
        self._refresh_event_seats()

    # ── Calculations ────────────────────────────────────────────────────

    def calculate_totals(self):
        total = 0.0
        for item in self.items:
            item.subtotal = flt(item.price) * cint(item.quantity)
            total += item.subtotal
        self.total_amount       = total
        self.outstanding_amount = flt(self.total_amount) - flt(self.paid_amount or 0)
        if self.outstanding_amount <= 0:
            self.payment_status = "Paid"
        elif flt(self.paid_amount or 0) > 0:
            self.payment_status = "Partially Paid"
        else:
            self.payment_status = "Unpaid"

    def validate_seat_availability(self):
        event = frappe.get_doc("Event", self.event)
        availability = {t["ticket_type"]: t["available"] for t in event.get_ticket_availability()}

        demand = {}
        for item in self.items:
            demand[item.ticket_type] = demand.get(item.ticket_type, 0) + cint(item.quantity)

        for tt, qty in demand.items():
            avail = availability.get(tt, 0)
            # Exclude current booking's already-booked quantity if editing
            if not self.is_new():
                existing = frappe.db.sql("""
                    SELECT IFNULL(SUM(bi.quantity),0)
                    FROM `tabBooking Item` bi
                    WHERE bi.parent=%s AND bi.ticket_type=%s
                """, (self.name, tt))[0][0]
                avail += int(existing)
            if qty > avail:
                frappe.throw(
                    f"Only {avail} seat(s) available for ticket type '{tt}'. "
                    f"You requested {qty}."
                )

    # ── QR Code ─────────────────────────────────────────────────────────

    def generate_qr_codes(self):
        """Generate QR per booking item and one master QR for the booking."""
        # Master booking QR
        booking_url = get_url(f"/booking/{self.name}")
        self.qr_code = self._make_qr_image(booking_url, f"booking_{self.name}")

        for idx, item in enumerate(self.items):
            payload = (
                f"BOOKING:{self.name}|EVENT:{self.event}|"
                f"TYPE:{item.ticket_type}|QTY:{item.quantity}|"
                f"PASSENGER:{item.passenger_name or 'Guest'}"
            )
            item.qr_code = self._make_qr_image(
                payload, f"item_{self.name}_{idx}"
            )
        self.save(ignore_permissions=True)

    def _make_qr_image(self, data, filename):
        qr = qrcode.QRCode(version=1, box_size=8, border=2)
        qr.add_data(data)
        qr.make(fit=True)
        img      = qr.make_image(fill_color="black", back_color="white")
        buf      = BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        fname = f"{filename}.png"
        fpath = frappe.get_site_path("public", "files", fname)
        with open(fpath, "wb") as f:
            f.write(buf.read())
        return f"/files/{fname}"

    # ── Email ────────────────────────────────────────────────────────────

    def send_confirmation_email(self):
        if not self.customer_email:
            return
        items_html = "".join(
            f"<tr><td>{i.ticket_type}</td><td>{i.quantity}</td>"
            f"<td>₹{i.price}</td><td>₹{i.subtotal}</td></tr>"
            for i in self.items
        )
        html = f"""
        <h2>Booking Confirmed 🎉</h2>
        <p>Dear <strong>{self.customer_name}</strong>,</p>
        <p>Your booking for <strong>{self.event}</strong> on {self.event_date} at {self.venue} is confirmed.</p>
        <table border="1" cellpadding="6" cellspacing="0" style="border-collapse:collapse;">
          <thead>
            <tr style="background:#f0f0f0">
              <th>Ticket Type</th><th>Qty</th><th>Unit Price</th><th>Subtotal</th>
            </tr>
          </thead>
          <tbody>{items_html}</tbody>
          <tfoot>
            <tr><td colspan="3"><strong>Total</strong></td><td><strong>₹{self.total_amount}</strong></td></tr>
          </tfoot>
        </table>
        <p>Booking ID: <strong>{self.name}</strong></p>
        <p>Please show your QR code at the venue entrance.</p>
        <a href="{get_url(f'/booking/{self.name}')}">View Booking</a>
        """
        frappe.sendmail(
            recipients=[self.customer_email],
            subject=f"Booking Confirmed – {self.event} [{self.name}]",
            message=html,
        )

    # ── Helpers ──────────────────────────────────────────────────────────

    def _refresh_event_seats(self):
        event = frappe.get_doc("Event", self.event)
        event.sync_available_seats()
        event.save(ignore_permissions=True)

    @frappe.whitelist()
    def mark_paid(self, amount, method, reference):
        self.paid_amount       = flt(amount)
        self.payment_method    = method
        self.payment_reference = reference
        self.calculate_totals()
        if self.payment_status == "Paid":
            self.status = "Paid"
        self.save(ignore_permissions=True)
        frappe.db.commit()
        return {"status": self.status, "payment_status": self.payment_status}
