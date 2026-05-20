/* Booking DocType – desk form enhancements */
frappe.ui.form.on("Booking", {
  refresh(frm) {
    if (!frm.is_new() && frm.doc.status === "Confirmed" && frm.doc.payment_status !== "Paid") {
      frm.add_custom_button(__("Record Payment"), () => {
        const d = new frappe.ui.Dialog({
          title: __("Record Payment"),
          fields: [
            { fieldname: "amount",     fieldtype: "Currency", label: "Amount",     reqd: 1, default: frm.doc.outstanding_amount },
            { fieldname: "method",     fieldtype: "Select",   label: "Method",     options: "\nOnline\nUPI\nCard\nCash", reqd: 1 },
            { fieldname: "reference",  fieldtype: "Data",     label: "Reference #" },
          ],
          primary_action_label: __("Save"),
          primary_action({ amount, method, reference }) {
            frappe.call({
              method: "online_ticket_booking.booking.booking.mark_paid",
              args:   { booking: frm.doc.name, amount, method, reference },
              callback() { d.hide(); frm.reload_doc(); },
            });
          },
        });
        d.show();
      }, __("Actions"));
    }

    if (frm.doc.qr_code) {
      frm.set_df_property("qr_code", "hidden", 0);
    }
  },

  event(frm) {
    if (frm.doc.event) {
      frappe.db.get_value("Event", frm.doc.event, ["available_seats", "is_active"],
        ({ available_seats, is_active }) => {
          if (!is_active) frappe.msgprint({ message: __("This event is not active."), indicator: "orange" });
          if (available_seats === 0) frappe.msgprint({ message: __("No seats available!"), indicator: "red" });
        }
      );
    }
  },
});
