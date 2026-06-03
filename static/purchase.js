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