// Fetch locations and populate dropdown
document.addEventListener("DOMContentLoaded", function () {

fetch("/locations")
  .then(response => response.json())
  .then(data => {
    const dropdown = document.getElementById("location-dropdown");
    dropdown.innerHTML = "<option value=''>-- Or select from list --</option>"; // reset

    data.forEach(loc => {
      const option = document.createElement("option");
      option.value = loc.latitude + "," + loc.longitude; // store coordinates
      option.textContent = loc.location;                  // show name
      dropdown.appendChild(option);
    });
  })
  .catch(err => console.error("Failed to load locations:", err));


  // Dropdown change event
  const dropdownElement = document.getElementById("location-dropdown");
if (dropdownElement) {
  dropdownElement.addEventListener("change", function () {
    if (this.value !== "") {
      navigate();
    }
  });
}

  // Chatbot code starts here
  const chatBtn = document.getElementById("chat-button");
  const chatbot = document.getElementById("chatbot");
  const closeBtn = document.getElementById("chatbot-close");
  const sendBtn = document.getElementById("send-btn");
  const input = document.getElementById("chat-input");
  const chatWindow = document.getElementById("chat-window");

  //safety check
  if (!chatBtn || !chatbot || !closeBtn || !sendBtn || !input || !chatWindow) {
    console.error("Chatbot elements missing!");
    return;
  }

  //open chatbot
  chatBtn.addEventListener("click", () => {
    chatbot.style.display = "flex";
  });

  //close chatbot
  closeBtn.addEventListener("click", () => {
    chatbot.style.display = "none";
  });

  //send message button
  sendBtn.addEventListener("click", sendMessage);

  //enter key support
  input.addEventListener("keypress", function (e) {
    if (e.key === "Enter") {
      sendMessage();
    }
  });
// send message function

  async function sendMessage() {
    const msg = input.value.trim();
    if (!msg) return;

    // Show user message
    chatWindow.insertAdjacentHTML("beforeend",
      `<div class="user-msg">${msg}</div>`
    );
      input.value = "";

    try {
      const res = await fetch("/chatbot", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: msg })
      });

      const data = await res.json();
      
      chatWindow.insertAdjacentHTML("beforeend",`<div class="bot-msg">${data.reply}</div>`
);
    } catch {
      chatWindow.insertAdjacentHTML("beforeend",`<div class="bot-msg">Server not responding 😓</div>`
);
    }

    chatWindow.scrollTop = chatWindow.scrollHeight;
  }

});


// Feedback toggle
function toggleFeedback() {
  const box = document.getElementById("feedback-box");
  box.style.display = (box.style.display === "block") ? "none" : "block";
}

// Feedback submit
function submitFeedback() {
  const feedback = document.getElementById("feedback-text").value.trim();
  const status = document.getElementById("feedback-status");

  if (!feedback) {
    status.textContent = "⚠️ Please enter your message.";
    status.style.color = "red";
    return;
  }

  status.textContent = "✅ Thanks for your feedback!";
  status.style.color = "green";
  document.getElementById("feedback-text").value = "";
}

// Help toggle
function showHelp() {
  const help = document.getElementById("help-info");
  help.style.display = (help.style.display === "block") ? "none" : "block";
}




//login 
function toggleLamp() {
    const lamp = document.getElementById("lampWrapper");
    const login = document.getElementById("login-box");

    lamp.classList.toggle("active");
    login.classList.toggle("show");
}

function showSignup() {
  document.getElementById('login-box').classList.remove('show');
  document.getElementById('signup-box').classList.add('show');
}

function showLogin() {
  document.getElementById('signup-box').classList.remove('show');
  document.getElementById('login-box').classList.add('show');
}

function showForgot() {
  document.getElementById('login-box').classList.remove('show');
  document.getElementById('signup-box').classList.remove('show');
  document.getElementById('forgot-password-box').classList.add('show');
}



// 🔍 Search function
function searchLocation() {
  const query = document.getElementById("searchBox").value.trim().toLowerCase();

  if (!query) {
    alert("Please type a location!");
    return;
  }

  const options = document.getElementById("location-dropdown").options;
  let matches = [];

  for (let i = 0; i < options.length; i++) {
    if (options[i].text.toLowerCase().includes(query)) {
      matches.push(options[i]);
    }
  }

  if (matches.length === 1) {
    matches[0].selected = true;
    navigate();
  } else if (matches.length > 1) {
    alert("Multiple matches found: " + matches.map(o => o.text).join(", "));
  } else {
    alert("Location not found in database!");
  }
}

// 🗺️ Navigation function
function navigate() {
  const destination = document.getElementById("location-dropdown").value;

  if (!destination) {
    alert("Please select a destination!");
    return;
  }

  const originName = prompt("Enter your current location:");
  if (!originName) return;

  fetch("/locations")
    .then(response => response.json())
    .then(data => {

      const startLocation = data.find(loc =>
        loc.location.toLowerCase().includes(originName.toLowerCase())
      );

      if (!startLocation) {
        alert("Starting location not found!");
        return;
      }

      const originCoords = startLocation.latitude + "," + startLocation.longitude;

      const url =
        "https://www.google.com/maps/dir/?api=1" +
        "&origin=" + originCoords +
        "&destination=" + destination +
        "&travelmode=walking";

      window.open(url, "_blank");
    });
}