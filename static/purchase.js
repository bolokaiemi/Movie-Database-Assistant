const items = document.querySelectorAll('.item');
const qty = document.querySelectorAll('.quantity');

const subtotalEl = document.getElementById('subtotal');
const taxEl = document.getElementById('tax');
const totalEl = document.getElementById('total');

const btn = document.getElementById('purchaseBtn');
const message = document.getElementById('confirmationMessage');
const qr = document.getElementById('qrcode');

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

btn.addEventListener('click', () => {
  calculate();

  const code = "MOV-" + Math.random().toString(36).substring(2, 10).toUpperCase();

  // Parse items to send correct details to backend
  let popcornSize = "None";
  let drinkSize = "None";
  let concessionsTotal = 0;
  let hasTicket = false;

  items.forEach((item, i) => {
    if (item.checked) {
      const labelText = item.parentElement.textContent.trim();
      const price = parseFloat(item.dataset.price);
      const quantity = parseInt(qty[i].value) || 1;
      
      if (labelText.includes("Ticket")) {
        hasTicket = true;
      }
      if (labelText.includes("Popcorn")) {
        popcornSize = "Large";
        concessionsTotal += price * quantity;
      } else if (labelText.includes("Nachos") || labelText.includes("Candy")) {
        popcornSize = popcornSize === "None" ? "Medium" : popcornSize;
        concessionsTotal += price * quantity;
      }
      if (labelText.includes("Soda")) {
        drinkSize = "Medium";
        concessionsTotal += price * quantity;
      } else if (labelText.includes("Slushie")) {
        drinkSize = "Large";
        concessionsTotal += price * quantity;
      } else if (labelText.includes("Water")) {
        drinkSize = "Small";
        concessionsTotal += price * quantity;
      }
    }
  });

  const pathParts = window.location.pathname.split('/');
  const movieId = parseInt(pathParts[pathParts.length - 1]) || 1;
  const user_id = 1; // Default user Bolokaiemi

  // POST purchase to SQLite via Flask route
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

  message.innerHTML = `
    <b>Success!</b><br>
    Code: ${code}<br>
    Total: ${totalEl.textContent}
  `;

  qr.innerHTML = "";

  new QRCode(qr, {
    text: code,
    width: 180,
    height: 180
  });
});

calculate();