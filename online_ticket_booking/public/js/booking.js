/* ===== Online Ticket Booking – Portal JS ===== */

const OTB = (function () {

  /* ── Helpers ── */
  const api = (method, args = {}) =>
    frappe.call({ method: `online_ticket_booking.api.${method}`, args }).then(r => r.message);

  const fmt_currency = v => "₹" + parseFloat(v || 0).toLocaleString("en-IN", { minimumFractionDigits: 2 });

  /* ── Events page ── */
  async function initEventsPage() {
    const container = document.getElementById("event-grid");
    if (!container) return;
    container.innerHTML = `<div class="otb-loading">Loading events…</div>`;
    const { events } = await api("get_events", { page_size: 24 });
    if (!events.length) {
      container.innerHTML = `<div class="otb-empty">No events found.</div>`;
      return;
    }
    container.innerHTML = events.map(ev => `
      <div class="event-card" onclick="location.href='/events/${ev.name}'">
        <img class="event-card__img" src="${ev.event_image || '/assets/online_ticket_booking/images/placeholder.png'}" alt="${ev.event_name}">
        <div class="event-card__body">
          <div class="event-card__badge">${ev.event_category || "Event"}</div>
          <h3 class="event-card__title">${ev.event_name}</h3>
          <p class="event-card__meta">📅 ${ev.event_date} &nbsp;|&nbsp; 📍 ${ev.venue}, ${ev.city || ""}</p>
          <p class="event-card__meta">🪑 ${ev.available_seats} seats left</p>
        </div>
      </div>
    `).join("");
  }

  /* ── Event Detail / Booking Form ── */
  async function initEventDetail(eventId) {
    const data = await api("get_event_detail", { event: eventId });
    document.getElementById("event-title").textContent       = data.event_name;
    document.getElementById("event-description").innerHTML   = data.description || "";
    document.getElementById("event-date").textContent        = data.event_date;
    document.getElementById("event-venue").textContent       = `${data.venue}, ${data.city || ""}`;
    document.getElementById("event-available").textContent   = data.available_seats;

    const tbody = document.getElementById("ticket-rows");
    tbody.innerHTML = "";
    (data.ticket_availability || []).forEach(tt => {
      const tr = document.createElement("tr");
      tr.className = "ticket-row";
      tr.innerHTML = `
        <td class="ticket-row__name">${tt.ticket_type}</td>
        <td class="ticket-row__price">${fmt_currency(tt.price)}</td>
        <td class="ticket-row__qty">
          <button onclick="OTB.adjustQty(this, -1)">−</button>
          <span class="qty-val" data-type="${tt.ticket_type}" data-price="${tt.price}">0</span>
          <button onclick="OTB.adjustQty(this, 1)" ${tt.available === 0 ? "disabled" : ""}>+</button>
        </td>
        <td>${tt.available > 0 ? `<span style="color:green">${tt.available} left</span>` : `<span style="color:red">Sold Out</span>`}</td>
      `;
      tbody.appendChild(tr);
    });

    document.getElementById("btn-book").addEventListener("click", () => submitBooking(eventId));
  }

  function adjustQty(btn, delta) {
    const span  = btn.parentElement.querySelector(".qty-val");
    const cur   = parseInt(span.textContent);
    const next  = Math.max(0, cur + delta);
    span.textContent = next;
    updateTotal();
  }

  function updateTotal() {
    let total = 0;
    document.querySelectorAll(".qty-val").forEach(el => {
      total += parseInt(el.textContent) * parseFloat(el.dataset.price);
    });
    document.getElementById("total-display").textContent = fmt_currency(total);
  }

  async function submitBooking(eventId) {
    const name  = document.getElementById("cust-name").value.trim();
    const email = document.getElementById("cust-email").value.trim();
    const phone = document.getElementById("cust-phone").value.trim();
    if (!name || !email) { frappe.msgprint("Please fill name and email."); return; }

    const items = [];
    document.querySelectorAll(".qty-val").forEach(el => {
      const qty = parseInt(el.textContent);
      if (qty > 0)
        items.push({ ticket_type: el.dataset.type, quantity: qty, passenger_name: name });
    });
    if (!items.length) { frappe.msgprint("Please select at least one ticket."); return; }

    frappe.dom.freeze("Creating booking…");
    const res = await api("create_booking", {
      event: eventId, customer_name: name,
      customer_email: email, customer_phone: phone,
      items: JSON.stringify(items),
    });
    frappe.dom.unfreeze();

    if (res && res.booking) {
      await api("confirm_booking", { booking: res.booking });
      location.href = `/booking/${res.booking}`;
    }
  }

  /* ── Booking Confirmation page ── */
  async function initBookingConfirmation(bookingId) {
    const data = await api("get_booking_detail", { booking: bookingId });
    document.getElementById("booking-id").textContent   = data.name;
    document.getElementById("event-name").textContent   = data.event;
    document.getElementById("venue-name").textContent   = data.venue || "";
    document.getElementById("event-date").textContent   = data.event_date;
    document.getElementById("cust-name").textContent    = data.customer_name;
    document.getElementById("total-amt").textContent    = fmt_currency(data.total_amount);
    document.getElementById("status-badge").textContent = data.status;
    document.getElementById("status-badge").className   = `status-badge ${data.status.toLowerCase()}`;
    if (data.qr_code)
      document.getElementById("qr-img").src = data.qr_code;

    const tbody = document.getElementById("items-body");
    tbody.innerHTML = (data.items || []).map(i => `
      <tr>
        <td>${i.ticket_type}</td>
        <td>${i.quantity}</td>
        <td>${fmt_currency(i.price)}</td>
        <td>${fmt_currency(i.subtotal)}</td>
      </tr>
    `).join("");
  }

  /* ── My Bookings page ── */
  async function initMyBookings() {
    const container = document.getElementById("my-bookings-list");
    if (!container) return;
    container.innerHTML = `<div class="otb-loading">Loading…</div>`;
    const { bookings } = await api("get_my_bookings");
    if (!bookings.length) {
      container.innerHTML = `<div class="otb-empty">You have no bookings yet.</div>`;
      return;
    }
    container.innerHTML = bookings.map(b => `
      <div class="booking-list-item" onclick="location.href='/booking/${b.name}'">
        <div>
          <strong>${b.event}</strong>
          <p style="margin:0;font-size:.85rem;color:#666">${b.event_date} · ${b.venue || ""}</p>
        </div>
        <div style="text-align:right">
          <span class="status-badge ${b.status.toLowerCase()}">${b.status}</span>
          <p style="margin:.2rem 0 0;font-weight:700">${fmt_currency(b.total_amount)}</p>
        </div>
      </div>
    `).join("");
  }

  return { initEventsPage, initEventDetail, initBookingConfirmation, initMyBookings, adjustQty };
})();
