const items = document.querySelectorAll('.item');
const qty = document.querySelectorAll('.quantity');

const subtotalEl = document.getElementById('subtotal');
const taxEl = document.getElementById('tax');
const totalEl = document.getElementById('total');

const btn = document.getElementById('purchaseBtn');

// Helper to calculate total
function calculate() {
  let subtotal = 0;

  items.forEach((item, i) => {
    if (item.checked) {
      const price = parseFloat(item.dataset.price);
      const quantity = parseInt(qty[i].value) || 1;
      subtotal += price * quantity;
    }
  });

  const tax = subtotal * 0.1;
  const total = subtotal + tax;

  subtotalEl.textContent = `$${subtotal.toFixed(2)}`;
  taxEl.textContent = `$${tax.toFixed(2)}`;
  totalEl.textContent = `$${total.toFixed(2)}`;
}

items.forEach(i => i.addEventListener('change', calculate));
qty.forEach(q => q.addEventListener('input', calculate));

// Complete purchase button click listener
btn.addEventListener('click', () => {
  calculate();

  // Validate that at least one item was selected
  let anyChecked = false;
  items.forEach(item => {
    if (item.checked) anyChecked = true;
  });

  if (!anyChecked) {
    alert("Please select at least one ticket or concession item before completing your purchase.");
    return;
  }

  const userEmail = document.getElementById('userEmail').value.trim();

  // If user typed something in email, validate basic format
  if (userEmail && (!userEmail.includes('@') || !userEmail.includes('.'))) {
    alert("Please enter a valid email address to receive your ticket receipt.");
    return;
  }

  const code = "MOV-" + Math.random().toString(36).substring(2, 10).toUpperCase();

  // Parse items to send correct details to backend and populate the ticket receipt
  let popcornSize = "None";
  let drinkSize = "None";
  let concessionsTotal = 0;
  let hasTicket = false;
  
  const receiptList = document.getElementById('ticketItemsList');
  receiptList.innerHTML = ""; // Clear old receipt list

  let purchasedItemsList = []; // Array of purchases to send to email API

  items.forEach((item, i) => {
    if (item.checked) {
      const price = parseFloat(item.dataset.price);
      const quantity = parseInt(qty[i].value) || 1;
      const itemName = item.dataset.name || "Cinema Item";
      
      // Track item for API payload
      purchasedItemsList.push({
        name: itemName,
        quantity: quantity,
        price: price
      });

      // Add row to digital ticket receipt list
      const itemRow = document.createElement('div');
      itemRow.className = 'ticket-receipt-row';
      itemRow.innerHTML = `
        <span>${itemName} x${quantity}</span>
        <span>$${(price * quantity).toFixed(2)}</span>
      `;
      receiptList.appendChild(itemRow);

      if (itemName.includes("Ticket")) {
        hasTicket = true;
      }
      if (itemName.includes("Popcorn")) {
        popcornSize = "Large";
        concessionsTotal += price * quantity;
      } else if (itemName.includes("Nachos") || itemName.includes("Candy")) {
        popcornSize = popcornSize === "None" ? "Medium" : popcornSize;
        concessionsTotal += price * quantity;
      }
      if (itemName.includes("Soda")) {
        drinkSize = "Medium";
        concessionsTotal += price * quantity;
      } else if (itemName.includes("Slushie")) {
        drinkSize = "Large";
        concessionsTotal += price * quantity;
      } else if (itemName.includes("Water")) {
        drinkSize = "Small";
        concessionsTotal += price * quantity;
      }
    }
  });

  const pathParts = window.location.pathname.split('/');
  const movieId = parseInt(pathParts[pathParts.length - 1]) || 1;
  const user_id = 1; // Default user Bolokaiemi

  // 1. POST purchase to SQLite database via Flask API
  fetch('/api/purchase', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      user_id: user_id,
      movie_id: movieId,
      qr_code_link: code,
      popcorn_size: popcornSize,
      drink_size: drinkSize,
      concessions_total: concessionsTotal,
      has_ticket: hasTicket
    })
  })
  .then(res => res.json())
  .then(data => {
    if (data.success) {
      console.log("🎟️ Purchase saved in database successfully!");
    } else {
      console.error("❌ Failed to save purchase:", data.message);
    }
  })
  .catch(err => console.error("❌ Network error connecting to purchase API:", err));

  // Populate dynamic ticket values
  document.getElementById('ticketTotalAmount').textContent = totalEl.textContent;
  document.getElementById('ticketCode').textContent = code;
  
  // Set up ticket movie details from page labels
  const movieTitle = document.getElementById('selectedMovieTitle').textContent;
  const movieDate = document.getElementById('selectedMovieDate').textContent;
  const movieTime = document.getElementById('selectedMovieTime').textContent;
  const movieScreen = document.getElementById('selectedMovieScreen').textContent;
  
  document.getElementById('ticketMovieTitle').textContent = movieTitle;
  document.getElementById('ticketDate').textContent = movieDate;
  document.getElementById('ticketTime').textContent = movieTime;
  document.getElementById('ticketScreen').textContent = movieScreen;

  // Generate QR Code
  const qrContainer = document.getElementById('qrcode');
  qrContainer.innerHTML = "";
  new QRCode(qrContainer, {
    text: code,
    width: 140,
    height: 140,
    colorDark : "#09090e",
    colorLight : "#ffffff",
    correctLevel : QRCode.CorrectLevel.H
  });

  // Save active ticket details to sessionStorage
  saveActiveTicketToSession(movieId, {
    ticketCode: code,
    userEmail: userEmail,
    totalAmount: totalEl.textContent,
    movieTitle: movieTitle,
    movieDate: movieDate,
    movieTime: movieTime,
    movieScreen: movieScreen,
    itemsListHtml: receiptList.innerHTML,
    status: 'active'
  });

  // Gorgeous transition to success state
  // Hide checkout form options
  document.querySelector('.purchase-left-column').style.display = 'none';
  document.getElementById('orderSummaryCard').style.display = 'none';
  
  // Center grid layout and show ticket
  const purchaseGrid = document.querySelector('.purchase-grid');
  purchaseGrid.style.display = 'flex';
  purchaseGrid.style.justifyContent = 'center';
  
  const ticketContainer = document.getElementById('ticketContainer');
  ticketContainer.style.display = 'block';
  ticketContainer.classList.add('animate-ticket');

  // Smooth scroll to the top of ticket
  window.scrollTo({ top: 0, behavior: 'smooth' });

  // Automatically trigger the Map Pop-up locator to help them locate their screen!
  setTimeout(() => {
    if (typeof openPurchaseSuccessMap === 'function') {
      openPurchaseSuccessMap();
    }
  }, 1200);

  // 2. Trigger email receipt dispatch if email address was provided
  const emailStatusEl = document.getElementById('ticketEmailStatus');
  if (userEmail) {
    emailStatusEl.style.display = 'block';
    emailStatusEl.textContent = "Sending Email...";
    emailStatusEl.style.color = "#f59e0b"; // Gold

    fetch('/api/send_ticket_email', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        email: userEmail,
        ticket_code: code,
        movie_title: movieTitle,
        date: movieDate,
        time: movieTime,
        screen: movieScreen,
        items: purchasedItemsList,
        total: totalEl.textContent
      })
    })
    .then(res => res.json())
    .then(emailData => {
      if (emailData.success) {
        emailStatusEl.textContent = "📧 Emailed successfully!";
        emailStatusEl.style.color = "#06b6d4"; // Cyan
      } else {
        emailStatusEl.textContent = "⚠️ " + emailData.message;
        emailStatusEl.style.color = "#ef4444"; // Red
      }
    })
    .catch(err => {
      console.error("❌ Email API Network Error:", err);
      emailStatusEl.textContent = "⚠️ Email service offline";
      emailStatusEl.style.color = "#ef4444";
    });
  } else {
    // If no email was typed, hide the email status line entirely
    emailStatusEl.style.display = 'none';
  }
});

// Listen to showtime dropdown changes
const showtimeSelect = document.getElementById('showtimeSelect');
if (showtimeSelect) {
  showtimeSelect.addEventListener('change', () => {
    const selectedOpt = showtimeSelect.options[showtimeSelect.selectedIndex];
    const date = selectedOpt.dataset.date;
    const time = selectedOpt.dataset.time;
    const screen = selectedOpt.dataset.screen;
    
    // Update Banner Card
    document.getElementById('selectedMovieDate').textContent = date;
    document.getElementById('selectedMovieTime').textContent = time;
    document.getElementById('selectedMovieScreen').textContent = screen;
    
    // Update Order Summary screen info
    const summaryScreenEl = document.querySelector('.summary-movie-screen');
    if (summaryScreenEl) {
      summaryScreenEl.textContent = screen;
    }
    
    // Update Ticket fields
    document.getElementById('ticketDate').textContent = date;
    document.getElementById('ticketTime').textContent = time;
    document.getElementById('ticketScreen').textContent = screen;
  });
}

// Run initial calculation
calculate();

// Initialize active ticket from session storage if exists
const pathPartsInit = window.location.pathname.split('/');
const movieIdInit = parseInt(pathPartsInit[pathPartsInit.length - 1]) || 1;
loadActiveTicketFromSession(movieIdInit);


function cancelCurrentBooking() {
  const ticketCode = document.getElementById('ticketCode').textContent;
  const userEmail = document.getElementById('userEmail').value.trim();

  if (!ticketCode) {
    alert("No ticket code found to cancel.");
    return;
  }

  if (!confirm("Are you sure you want to cancel your booking and request a full refund?")) {
    return;
  }

  const cancelBtn = document.getElementById('cancelBookingBtn');
  cancelBtn.textContent = "Processing Cancellation...";
  cancelBtn.disabled = true;

  fetch('/api/cancel_booking', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      ticket_code: ticketCode,
      email: userEmail
    })
  })
  .then(res => res.json())
  .then(data => {
    if (data.success) {
      alert("Ticket successfully cancelled and refund processed! ❌");
      cancelBtn.textContent = "Booking Cancelled & Refunded";
      cancelBtn.style.color = "#64748b";
      cancelBtn.style.border = "1px solid rgba(255,255,255,0.08)";
      
      // Update ticket badge to CANCELLED in red
      const badge = document.querySelector('.ticket-badge');
      if (badge) {
        badge.textContent = "CANCELLED";
        badge.style.background = "#ef4444";
        badge.style.color = "#fff";
      }

      // Update stored session state to cancelled
      const pathParts = window.location.pathname.split('/');
      const movieId = parseInt(pathParts[pathParts.length - 1]) || 1;
      const stored = sessionStorage.getItem('active_ticket_' + movieId);
      if (stored) {
        const parsed = JSON.parse(stored);
        parsed.status = "cancelled";
        sessionStorage.setItem('active_ticket_' + movieId, JSON.stringify(parsed));
      }

      // Add a reload button to book again
      let bookAgainBtn = document.getElementById('bookAgainBtn');
      if (!bookAgainBtn) {
        bookAgainBtn = document.createElement('button');
        bookAgainBtn.id = 'bookAgainBtn';
        bookAgainBtn.textContent = "🔄 Book Another Ticket";
        bookAgainBtn.onclick = function() {
          sessionStorage.removeItem('active_ticket_' + movieId);
          window.location.reload();
        };
        // Apply beautiful styling
        Object.assign(bookAgainBtn.style, {
          background: 'var(--accent)',
          color: 'black',
          border: 'none',
          padding: '12px 28px',
          borderRadius: '10px',
          fontWeight: '800',
          fontSize: '14px',
          cursor: 'pointer',
          marginTop: '10px',
          boxShadow: '0 4px 15px rgba(34, 211, 238, 0.25)',
          transition: 'all 0.3s'
        });
        cancelBtn.parentNode.appendChild(bookAgainBtn);
      }
    } else {
      alert("Error: " + data.message);
      cancelBtn.textContent = "❌ Cancel Ticket & Refund Booking";
      cancelBtn.disabled = false;
    }
  })
  .catch(err => {
    console.error("Cancellation failed:", err);
    alert("Connection failed. Could not process cancellation.");
    cancelBtn.textContent = "❌ Cancel Ticket & Refund Booking";
    cancelBtn.disabled = false;
  });
}


function saveActiveTicketToSession(movieId, ticketData) {
  sessionStorage.setItem('active_ticket_' + movieId, JSON.stringify(ticketData));
}

function loadActiveTicketFromSession(movieId) {
  const stored = sessionStorage.getItem('active_ticket_' + movieId);
  if (!stored) return;

  try {
    const data = JSON.parse(stored);
    
    // Populate dynamic ticket values
    document.getElementById('ticketTotalAmount').textContent = data.totalAmount;
    document.getElementById('ticketCode').textContent = data.ticketCode;
    
    document.getElementById('ticketMovieTitle').textContent = data.movieTitle;
    document.getElementById('ticketDate').textContent = data.movieDate;
    document.getElementById('ticketTime').textContent = data.movieTime;
    document.getElementById('ticketScreen').textContent = data.movieScreen;
    
    document.getElementById('ticketItemsList').innerHTML = data.itemsListHtml;
    
    if (data.userEmail) {
      document.getElementById('userEmail').value = data.userEmail;
    }
    
    // Generate QR Code
    const qrContainer = document.getElementById('qrcode');
    qrContainer.innerHTML = "";
    new QRCode(qrContainer, {
      text: data.ticketCode,
      width: 140,
      height: 140,
      colorDark : "#09090e",
      colorLight : "#ffffff",
      correctLevel : QRCode.CorrectLevel.H
    });

    const cancelBtn = document.getElementById('cancelBookingBtn');

    if (data.status === "cancelled") {
      const badge = document.querySelector('.ticket-badge');
      if (badge) {
        badge.textContent = "CANCELLED";
        badge.style.background = "#ef4444";
        badge.style.color = "#fff";
      }
      if (cancelBtn) {
        cancelBtn.textContent = "Booking Cancelled & Refunded";
        cancelBtn.disabled = true;
        cancelBtn.style.color = "#64748b";
        cancelBtn.style.border = "1px solid rgba(255,255,255,0.08)";
      }

      // Add a reload button to book again
      let bookAgainBtn = document.getElementById('bookAgainBtn');
      if (!bookAgainBtn) {
        bookAgainBtn = document.createElement('button');
        bookAgainBtn.id = 'bookAgainBtn';
        bookAgainBtn.textContent = "🔄 Book Another Ticket";
        bookAgainBtn.onclick = function() {
          sessionStorage.removeItem('active_ticket_' + movieId);
          window.location.reload();
        };
        // Apply beautiful styling
        Object.assign(bookAgainBtn.style, {
          background: 'var(--accent)',
          color: 'black',
          border: 'none',
          padding: '12px 28px',
          borderRadius: '10px',
          fontWeight: '800',
          fontSize: '14px',
          cursor: 'pointer',
          marginTop: '10px',
          boxShadow: '0 4px 15px rgba(34, 211, 238, 0.25)',
          transition: 'all 0.3s'
        });
        cancelBtn.parentNode.appendChild(bookAgainBtn);
      }
    }

    // Hide checkout form and summary
    document.querySelector('.purchase-left-column').style.display = 'none';
    document.getElementById('orderSummaryCard').style.display = 'none';
    
    // Center grid layout and show ticket
    const purchaseGrid = document.querySelector('.purchase-grid');
    purchaseGrid.style.display = 'flex';
    purchaseGrid.style.justifyContent = 'center';
    
    const ticketContainer = document.getElementById('ticketContainer');
    ticketContainer.style.display = 'block';
  } catch (e) {
    console.error("Error loading active ticket from session:", e);
  }
}