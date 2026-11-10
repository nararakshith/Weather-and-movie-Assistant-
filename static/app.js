const form = document.querySelector("#chat-form");
const input = document.querySelector("#message-input");
const sendButton = document.querySelector("#send-button");
const messages = document.querySelector("#messages");
const welcome = document.querySelector("#welcome");
const toast = document.querySelector("#toast");
let toastTimer;

function showToast(message) {
  toast.textContent = message;
  toast.classList.add("show");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => toast.classList.remove("show"), 3400);
}

function addMessage(role, text, typing = false) {
  const row = document.createElement("div");
  row.className = `message ${role}`;
  if (role === "assistant") {
    const avatar = document.createElement("div");
    avatar.className = "message-avatar";
    avatar.textContent = "✳";
    row.append(avatar);
  }
  const bubble = document.createElement("div");
  bubble.className = "message-bubble";
  if (typing) {
    bubble.setAttribute("aria-label", "Prism is thinking");
    bubble.innerHTML = '<div class="typing"><span></span><span></span><span></span></div>';
  } else {
    bubble.textContent = text;
  }
  row.append(bubble);
  messages.append(row);
  messages.classList.add("active");
  welcome.classList.add("hidden");
  messages.scrollIntoView({ behavior: "smooth", block: "end" });
  return row;
}

async function sendMessage(message) {
  const text = message.trim();
  if (!text || sendButton.disabled) return;
  addMessage("user", text);
  input.value = "";
  input.style.height = "auto";
  sendButton.disabled = true;
  const pending = addMessage("assistant", "", true);
  try {
    const response = await fetch("/agent/invoke", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ input: { input: text } }),
    });
    if (!response.ok) {
      const details = await response.text();
      throw new Error(details || `Request failed (${response.status})`);
    }
    const data = await response.json();
    const answer = data.output;
    pending.querySelector(".message-bubble").textContent =
      typeof answer === "string" ? answer : answer?.content ?? JSON.stringify(answer);
  } catch (error) {
    pending.querySelector(".message-bubble").textContent =
      "I couldn't reach the assistant just now. Please try again in a moment.";
    console.error("Chat request failed:", error);
  } finally {
    sendButton.disabled = false;
    input.focus();
    pending.scrollIntoView({ behavior: "smooth", block: "end" });
  }
}

form.addEventListener("submit", (event) => {
  event.preventDefault();
  sendMessage(input.value);
});

input.addEventListener("input", () => {
  input.style.height = "auto";
  input.style.height = `${Math.min(input.scrollHeight, 130)}px`;
});

input.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    form.requestSubmit();
  }
});

document.querySelectorAll("[data-prompt]").forEach((button) => {
  button.addEventListener("click", () => sendMessage(button.dataset.prompt));
});

document.querySelector("#new-chat").addEventListener("click", () => {
  messages.replaceChildren();
  messages.classList.remove("active");
  welcome.classList.remove("hidden");
  input.value = "";
  input.focus();
});

document.querySelector(".help-button").addEventListener("click", () => {
  showToast("Ask for current weather in an Indian city or Indian movie recommendations by genre.");
});

document.addEventListener("keydown", (event) => {
  if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") {
    event.preventDefault();
    document.querySelector("#new-chat").click();
  }
});
