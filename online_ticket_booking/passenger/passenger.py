import frappe
from frappe.model.document import Document
from frappe.utils import date_diff, today

class Passenger(Document):
    def validate(self):
        if self.date_of_birth:
            age = date_diff(today(), self.date_of_birth) // 365
            if age < 0 or age > 130:
                frappe.throw("Invalid Date of Birth.")
