// --- INICIO DE INTEGRACIÓN AUTENTICACIÓN Y CHAT ---
document.addEventListener("DOMContentLoaded", () => {
  // --- Elementos de autenticación ---
  const authContainer = document.getElementById("auth-container");
  const authForm = document.getElementById("auth-form");
  const authTitle = document.getElementById("auth-title");
  const authUsername = document.getElementById("auth-username");
  const authEmail = document.getElementById("auth-email");
  const authPassword = document.getElementById("auth-password");
  const authSubmit = document.getElementById("auth-submit");
  const authToggleText = document.getElementById("auth-toggle-text");
  const toggleAuth = document.getElementById("toggle-auth");
  const authMessage = document.getElementById("auth-message");
  const userInfo = document.getElementById("user-info");
  const userWelcome = document.getElementById("user-welcome");
  const logoutBtn = document.getElementById("logout-btn");
  // --- Elementos de chat ---
  const chatContainer = document.getElementById("chat-container");
  const chatForm = document.getElementById("chat-form");
  const userInput = document.getElementById("user-input");
  const chatMessages = document.getElementById("chat-messages");
  const sendButton = document.getElementById("send-button");
  const apiStatusSpan = document.getElementById("api-status");

  // URLs de la API
  const API_BASE = "http://127.0.0.1:8000";
  const API_CHAT = `${API_BASE}/chat`;
  const API_LOGIN = `${API_BASE}/login`;
  const API_REGISTER = `${API_BASE}/register`;

  // Estado de sesión
  let currentThreadId = null;
  let currentToken = null;
  let currentUser = null;
  let currentUserId = null;
  let isRegisterMode = false;

  // --- Manejo de sesión y autenticación ---
  function saveSession(token, user, userId) {
    currentToken = token;
    currentUser = user;
    currentUserId = userId;
    localStorage.setItem("token", token);
    localStorage.setItem("user", user);
    localStorage.setItem("userId", userId);
  }
  function clearSession() {
    currentToken = null;
    currentUser = null;
    currentUserId = null;
    currentThreadId = null;
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    localStorage.removeItem("userId");
    localStorage.removeItem("threadId");
  }
  function loadSession() {
    currentToken = localStorage.getItem("token");
    currentUser = localStorage.getItem("user");
    currentUserId = localStorage.getItem("userId");
    currentThreadId = localStorage.getItem("threadId");
  }
  function saveSessionId(threadId) {
    currentThreadId = threadId;
    localStorage.setItem("threadId", threadId);
  }

  // --- UI helpers ---
  function showChat() {
    chatContainer.style.display = "block";
    userInfo.style.display = "flex";
    authContainer.style.display = "none";
    userWelcome.textContent = `👤 ${currentUser}`;
  }
  function showAuth() {
    chatContainer.style.display = "none";
    userInfo.style.display = "none";
    authContainer.style.display = "block";
    authMessage.textContent = "";
    authPassword.value = "";
  }

  // --- Alternar entre login y registro ---
  toggleAuth.addEventListener("click", (e) => {
    e.preventDefault();
    isRegisterMode = !isRegisterMode;
    if (isRegisterMode) {
      authTitle.textContent = "Registro";
      authEmail.style.display = "block";
      authSubmit.textContent = "Registrarse";
      authToggleText.innerHTML =
        '¿Ya tienes cuenta? <a href="#" id="toggle-auth">Inicia sesión</a>';
    } else {
      authTitle.textContent = "Iniciar sesión";
      authEmail.style.display = "none";
      authSubmit.textContent = "Entrar";
      authToggleText.innerHTML =
        '¿No tienes cuenta? <a href="#" id="toggle-auth">Regístrate</a>';
    }
  });

  // --- Logout ---
  logoutBtn.addEventListener("click", () => {
    clearSession();
    showAuth();
  });

  // --- Login/Registro ---
  authForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    authMessage.textContent = "";
    const username = authUsername.value.trim();
    const password = authPassword.value;
    const email = authEmail.value.trim();
    if (!username || !password || (isRegisterMode && !email)) {
      authMessage.textContent = "Completa todos los campos.";
      return;
    }
    try {
      let res;
      if (isRegisterMode) {
        res = await fetch(API_REGISTER, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ username, email, password }),
        });
        const data = await res.json();
        if (res.ok) {
          authMessage.textContent = "Registro exitoso. Ahora inicia sesión.";
          isRegisterMode = false;
          authTitle.textContent = "Iniciar sesión";
          authEmail.style.display = "none";
          authSubmit.textContent = "Entrar";
        } else {
          authMessage.textContent = data.detail || "Error en el registro.";
        }
      } else {
        res = await fetch(API_LOGIN, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ username, password }),
        });
        const data = await res.json();
        if (res.ok && data.token) {
          saveSession(data.token, username, data.user_id);
          showChat();
        } else {
          authMessage.textContent = data.detail || "Credenciales inválidas.";
        }
      }
    } catch (err) {
      authMessage.textContent = "Error de conexión con el servidor.";
    }
  });

  // --- Inicialización: cargar sesión si existe ---
  loadSession();
  if (currentToken && currentUser) {
    showChat();
  } else {
    showAuth();
  }

  // --- Chat ---
  function addMessage(text, sender, isRag = false) {
    const messageDiv = document.createElement("div");
    messageDiv.classList.add("message");
    messageDiv.classList.add(
      sender === "user" ? "user-message" : "bot-message",
    );
    if (sender === "bot") {
      const parts = text.split("FUENTES CONSULTADAS:");
      const responseText = parts[0].trim();
      const sourcesText = parts[1] ? parts[1].trim() : null;
      let content = responseText.replace(/\n/g, "<br>");
      if (sourcesText) {
        const sourceLines = sourcesText
          .split("\n")
          .filter((line) => line.trim().startsWith("-"))
          .map((line) => line.trim());
        content += `<div class="sources-section"><h4>📚 FUENTES CONSULTADAS:</h4><ul class="sources-list">${sourceLines.map((source) => `<li>${source.substring(1).trim()}</li>`).join("")}</ul></div>`;
      } else {
        content += `<div class="sources-section"><p class="general-knowledge">📖 Respuesta basada en conocimiento general</p></div>`;
      }
      messageDiv.innerHTML = content;
    } else {
      let content = text.replace(/\n/g, "<br>");
      messageDiv.innerHTML = content;
    }
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
  }
  function toggleLoading(isLoading) {
    if (isLoading) {
      sendButton.disabled = true;
      sendButton.innerHTML = '<div class="spinner"></div>';
      apiStatusSpan.textContent = "Pensando...";
    } else {
      sendButton.disabled = false;
      sendButton.innerHTML = "Enviar";
      apiStatusSpan.textContent = "Listo";
    }
    userInput.disabled = isLoading;
  }
  async function checkApiStatus() {
    try {
      const response = await fetch(`${API_BASE}/`, { method: "GET" });
      if (response.ok) {
        apiStatusSpan.textContent = "Conectado";
        apiStatusSpan.style.color = "#28a745";
      } else {
        throw new Error("API no responde");
      }
    } catch (error) {
      apiStatusSpan.textContent = "Desconectado";
      apiStatusSpan.style.color = "#dc3545";
    }
  }
  checkApiStatus();
  chatForm.addEventListener("submit", async function (event) {
    event.preventDefault();
    const message = userInput.value.trim();
    if (!message || !currentToken) return;
    addMessage(message, "user");
    userInput.value = "";
    toggleLoading(true);
    try {
      const response = await fetch(API_CHAT, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${currentToken}`,
        },
        body: JSON.stringify({
          user_input: message,
          thread_id: currentThreadId,
        }),
      });
      if (response.status === 401) {
        clearSession();
        showAuth();
        addMessage("⚠️ Tu sesión ha expirado. Inicia sesión de nuevo.", "bot");
        return;
      }
      const data = await response.json();
      if (data.thread_id && !currentThreadId) {
        saveSessionId(data.thread_id);
      }
      if (data.status === "success") {
        addMessage(data.response, "bot", data.agent_used_tool);
      } else {
        addMessage(`❌ Error del Agente: ${data.response}`, "bot");
      }
    } catch (error) {
      addMessage(
        "❌ Error de conexión. Asegúrate de que FastAPI esté corriendo en http://127.0.0.1:8000.",
        "bot",
      );
    } finally {
      toggleLoading(false);
      checkApiStatus();
    }
  });
});
