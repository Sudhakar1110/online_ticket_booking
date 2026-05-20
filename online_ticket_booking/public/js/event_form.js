/* Event DocType – desk form enhancements */
frappe.ui.form.on("Event", {
  refresh(frm) {
    if (!frm.is_new()) {
      frm.add_custom_button(__("View on Portal"), () =>
        window.open(`/events/${frm.doc.name}`, "_blank")
      );
      frm.add_custom_button(__("Booking Analytics"), () => {
        frappe.call({
          method: "online_ticket_booking.api.get_event_analytics",
          args:   { event: frm.doc.name },
          callback({ message }) {
            const rows = (message.ticket_summary || [])
              .map(r => `<tr><td>${r.ticket_type}</td><td>${r.qty_sold}</td><td>₹${r.revenue}</td></tr>`)
              .join("");
            frappe.msgprint({
              title: __("Event Analytics"),
              message: `
                <table class="table table-bordered">
                  <thead><tr><th>Ticket Type</th><th>Sold</th><th>Revenue</th></tr></thead>
                  <tbody>${rows}</tbody>
                </table>`,
              wide: true,
            });
          },
        });
      }, __("Actions"));
    }
  },

  total_capacity(frm) {
    if (!frm.doc.available_seats)
      frm.set_value("available_seats", frm.doc.total_capacity);
  },
});
