import frappe


def get_booking_permission_query(user):
    if frappe.session.user == "Administrator":
        return ""
    if "Booking Admin" in frappe.get_roles(user):
        return ""
    return f"`tabBooking`.booked_by = '{user}'"


def get_payment_permission_query(user):
    if frappe.session.user == "Administrator":
        return ""
    if "Booking Admin" in frappe.get_roles(user):
        return ""
    return f"`tabPayment`.booking IN (SELECT name FROM `tabBooking` WHERE booked_by='{user}')"
