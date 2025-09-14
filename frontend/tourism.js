const session_id = "user_" + Math.floor(Math.random() * 1000); 
const chatBtn = document.getElementById("chatbot-btn");
const chatWindow = document.getElementById("chatbot-window");
const messagesDiv = document.getElementById("chat-messages");
const inputField = document.getElementById("userInput");

// Toggle chatbot window
function toggleChat() {
  chatWindow.style.display = (chatWindow.style.display === "flex") ? "none" : "flex";
}
chatBtn.addEventListener("click", toggleChat);

// Close chat directly
function closeChat() {
  chatWindow.style.display = "none";
}

// Add message to chat with typewriter + markdown
function addMessage(text, sender) {
  const msg = document.createElement("div");
  msg.classList.add("msg", sender);

  if (sender === "bot") {
    msg.innerHTML = "";  // start empty
    messagesDiv.appendChild(msg);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;

    let i = 0;
    function typeChar() {
      if (i < text.length) {
        msg.innerHTML = marked.parse(text.substring(0, i + 1));
        i++;
        messagesDiv.scrollTop = messagesDiv.scrollHeight;
        setTimeout(typeChar, 30); // adjust speed here
      }
    }
    typeChar();
  } else {
    msg.textContent = text; // user message instant
    messagesDiv.appendChild(msg);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
  }
}

// Typing indicator dots
function showTyping() {
  const typingDiv = document.createElement("div");
  typingDiv.classList.add("typing");
  typingDiv.innerHTML = '<span class="dot"></span><span class="dot"></span><span class="dot"></span>';
  typingDiv.id = "typingIndicator";
  messagesDiv.appendChild(typingDiv);
  messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

function removeTyping() {
  const typingDiv = document.getElementById("typingIndicator");
  if (typingDiv) typingDiv.remove();
}

// Send message to FastAPI backend
async function sendMessage() {
  const text = inputField.value.trim();
  if (!text) return;

  addMessage(text, "traveler");  // user message
  inputField.value = "";
  showTyping();

  try {
    const res = await fetch("http://127.0.0.1:8000/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: text, session_id: session_id })
    });

    const data = await res.json();
    removeTyping();
    console.log("Bot Reply:", data.reply);
    addMessage(data.reply, "bot");
  } catch (err) {
    removeTyping();
    addMessage("⚠️ Error connecting to server", "bot");
    console.error(err);
  }
}

// Allow Enter key to send message
inputField.addEventListener("keypress", (e) => {
  if (e.key === "Enter") sendMessage();
});