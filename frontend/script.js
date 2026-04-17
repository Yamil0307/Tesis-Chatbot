// ============================================
// SCRIPT - CHATBOT AGENTIC RAG - UO
// Universidad de Oriente
// ============================================

document.addEventListener("DOMContentLoaded", () => {
  // --- Elementos del DOM ---
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
  const chatContainer = document.getElementById("chat-container");
  const chatForm = document.getElementById("chat-form");
  const userInput = document.getElementById("user-input");
  const chatMessages = document.getElementById("chat-messages");
  const sendButton = document.getElementById("send-button");
  const apiStatusSpan = document.getElementById("api-status");
  const statusDot = document.getElementById("status-dot");

  // --- URLs de la API ---
  const API_BASE = "http://127.0.0.1:8000";
  const API_CHAT = `${API_BASE}/chat`;
  const API_LOGIN = `${API_BASE}/login`;
  const API_REGISTER = `${API_BASE}/register`;

  // --- Estado de la aplicación ---
  let currentThreadId = null;
  let currentToken = null;
  let currentUser = null;
  let currentUserId = null;
  let isRegisterMode = false;

  // ============================================
  // FUNCIONES DE SESIÓN
  // ============================================

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

  // ============================================
  // FUNCIONES DE UI
  // ============================================

  function showChat() {
    chatContainer.classList.remove("hidden");
    userInfo.classList.remove("hidden");
    authContainer.classList.add("hidden");
    userWelcome.textContent = `👤 ${currentUser}`;
  }

  function showAuth() {
    chatContainer.classList.add("hidden");
    userInfo.classList.add("hidden");
    authContainer.classList.remove("hidden");
    authMessage.textContent = "";
    authPassword.value = "";
  }

  function toggleLoading(isLoading) {
    if (isLoading) {
      sendButton.disabled = true;
      sendButton.innerHTML = '<div class="spinner"></div>';
      apiStatusSpan.textContent = "Procesando...";
    } else {
      sendButton.disabled = false;
      sendButton.innerHTML = '<span>Enviar</span>';
      apiStatusSpan.textContent = "Listo";
    }
    userInput.disabled = isLoading;
  }

  async function checkApiStatus() {
    try {
      const response = await fetch(`${API_BASE}/`, { method: "GET" });
      if (response.ok) {
        apiStatusSpan.textContent = "Conectado";
        statusDot.classList.add("conectado");
        statusDot.classList.remove("desconectado");
      } else {
        throw new Error("API no responde");
      }
    } catch (error) {
      apiStatusSpan.textContent = "Desconectado";
      statusDot.classList.add("desconectado");
      statusDot.classList.remove("conectado");
    }
  }

  // ============================================
  // RENDERIZADO DE MENSAJES
  // ============================================

  function addMessage(text, sender) {
    // Separar contenido de fuentes
    let cuerpo = text;
    let fuentes = "";

    // Buscar marcador de fuentes (con o sin ###)
    const fuentesRegex = /(?:^|\n)\s*#*\s*FUENTES CONSULTADAS:/i;
    const match = fuentesRegex.exec(text);

    if (match) {
      const idx = match.index;
      cuerpo = text.slice(0, idx).trim();
      fuentes = text
        .slice(idx)
        .replace(/^\s*#*\s*FUENTES CONSULTADAS:/i, "")
        .trim();
    }

    // Crear mensaje principal
    const messageDiv = document.createElement("div");
    messageDiv.classList.add("message", sender === "user" ? "user-message" : "bot-message");
    messageDiv.innerHTML = cuerpo.replace(/\n/g, "<br>");
    chatMessages.appendChild(messageDiv);

    // Crear dropdown de fuentes si existe
    if (fuentes) {
      const details = document.createElement("details");
      details.className = "sources-dropdown";
      
      const summary = document.createElement("summary");
      summary.textContent = "📚 Fuentes consultadas";
      details.appendChild(summary);

      // Parsear cada fuente
      fuentes.split("\n").forEach((line) => {
        const match = line.match(/- \[(.+?)\] \(página (\d+)\):\s*"(.*)"/);
        if (match) {
          const [, archivo, pagina, fragmento] = match;
          const fuenteDiv = document.createElement("div");
          fuenteDiv.className = "fuente-item";
          fuenteDiv.innerHTML = `<strong>${archivo}</strong> (pág. ${pagina}):<br><span class="fuente-fragmento">"${fragmento}"</span>`;
          details.appendChild(fuenteDiv);
        } else if (line.trim()) {
          const fuenteDiv = document.createElement("div");
          fuenteDiv.className = "fuente-item";
          fuenteDiv.textContent = line;
          details.appendChild(fuenteDiv);
        }
      });

      chatMessages.appendChild(details);
    }

    // Scroll al final
    chatMessages.scrollTop = chatMessages.scrollHeight;
  }

  // ============================================
  // EVENT LISTENERS - AUTENTICACIÓN
  // ============================================

  // Alternar entre login y registro
  toggleAuth.addEventListener("click", (e) => {
    e.preventDefault();
    isRegisterMode = !isRegisterMode;
    
    if (isRegisterMode) {
      authTitle.textContent = "Crear cuenta";
      authEmail.classList.remove("hidden");
      authSubmit.textContent = "Registrarse";
      authToggleText.innerHTML = '¿Ya tienes cuenta? <a href="#" id="toggle-auth">Inicia sesión</a>';
    } else {
      authTitle.textContent = "Iniciar sesión";
      authEmail.classList.add("hidden");
      authSubmit.textContent = "Entrar";
      authToggleText.innerHTML = '¿No tienes cuenta? <a href="#" id="toggle-auth">Regístrate</a>';
    }
    
    // Re-asignar el nuevo toggle
    const newToggleAuth = document.getElementById("toggle-auth");
    if (newToggleAuth) {
      newToggleAuth.addEventListener("click", (e) => {
        e.preventDefault();
        isRegisterMode = !isRegisterMode;
        
        if (isRegisterMode) {
          authTitle.textContent = "Crear cuenta";
          authEmail.classList.remove("hidden");
          authSubmit.textContent = "Registrarse";
          authToggleText.innerHTML = '¿Ya tienes cuenta? <a href="#" id="toggle-auth">Inicia sesión</a>';
        } else {
          authTitle.textContent = "Iniciar sesión";
          authEmail.classList.add("hidden");
          authSubmit.textContent = "Entrar";
          authToggleText.innerHTML = '¿No tienes cuenta? <a href="#" id="toggle-auth">Regístrate</a>';
        }
      });
    }
  });

  // Logout
  logoutBtn.addEventListener("click", () => {
    clearSession();
    showAuth();
  });

  // Login / Registro
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
        // Registro
        res = await fetch(API_REGISTER, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ username, email, password }),
        });
        
        const data = await res.json();
        if (res.ok) {
          authMessage.style.color = "#28a745";
          authMessage.textContent = "✅ Registro exitoso. Ahora inicia sesión.";
          isRegisterMode = false;
          authTitle.textContent = "Iniciar sesión";
          authEmail.classList.add("hidden");
          authSubmit.textContent = "Entrar";
          authToggleText.innerHTML = '¿No tienes cuenta? <a href="#" id="toggle-auth">Regístrate</a>';
          authUsername.value = "";
          authPassword.value = "";
        } else {
          authMessage.textContent = data.detail || "Error en el registro.";
        }
      } else {
        // Login
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

  // ============================================
  // EVENT LISTENERS - CHAT
  // ============================================

  chatForm.addEventListener("submit", async function (event) {
    event.preventDefault();
    
    const message = userInput.value.trim();
    if (!message || !currentToken) return;

    // Agregar mensaje del usuario
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

      // Manejar sesión expirada
      if (response.status === 401) {
        clearSession();
        showAuth();
        addMessage("⚠️ Tu sesión ha expirado. Inicia sesión de nuevo.", "bot");
        return;
      }

      const data = await response.json();

      // Guardar thread_id si es nuevo
      if (data.thread_id && !currentThreadId) {
        saveSessionId(data.thread_id);
      }

      // Mostrar respuesta
      if (data.status === "success") {
        addMessage(data.response, "bot");
      } else {
        addMessage(`❌ Error: ${data.response}`, "bot");
      }
    } catch (error) {
      addMessage("❌ Error de conexión. Asegúrate de que FastAPI esté corriendo en http://127.0.0.1:8000", "bot");
    } finally {
      toggleLoading(false);
      checkApiStatus();
    }
  });

  // ============================================
  // INICIALIZACIÓN
  // ============================================

  // Cargar sesión si existe
  loadSession();
  if (currentToken && currentUser) {
    showChat();
  } else {
    showAuth();
  }

  // Verificar estado de la API
  checkApiStatus();
});