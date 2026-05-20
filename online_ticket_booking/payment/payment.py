import frappe
from frappe.model.document import Document
from frappe.utils import flt

class Payment(Document):
    def on_submit(self):
        if self.payment_status == "Success":
            booking = frappe.get_doc("Booking", self.booking)
            booking.mark_paid(self.amount, self.payment_method, self.transaction_id)

    def on_cancel(self):
        self.payment_status = "Refunded"
        self.save(ignore_permissions=True)
