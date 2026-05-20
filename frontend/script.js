// ============================================
// SCRIPT - CHATBOT AGENTIC RAG - UO
// Universidad de Oriente
// ============================================

document.addEventListener("DOMContentLoaded", () => {
  // --- Mostrar/Ocultar contraseña ---
  const passwordInput = document.getElementById("auth-password");
  const togglePassword = document.getElementById("toggle-password-visibility");
  const eyeOpen = document.getElementById("eye-open");
  const eyeClosed = document.getElementById("eye-closed");

  if (togglePassword && passwordInput && eyeOpen && eyeClosed) {
    togglePassword.addEventListener("click", () => {
      const isHidden = passwordInput.type === "password";
      passwordInput.type = isHidden ? "text" : "password";
      eyeOpen.style.display = isHidden ? "none" : "inline";
      eyeClosed.style.display = isHidden ? "inline" : "none";
    });
    // Accesibilidad: permitir con Enter/Espacio
    togglePassword.addEventListener("keydown", (e) => {
      if (e.key === "Enter" || e.key === " " || e.key === "Spacebar") {
        e.preventDefault();
        togglePassword.click();
      }
    });
  }
  // --- Elementos del DOM ---
  const authPage = document.getElementById("auth-page");
  const chatPage = document.getElementById("chat-page");
  const authForm = document.getElementById("auth-form");
  const authTitle = document.getElementById("auth-title");
  const authSubtitle = document.getElementById("auth-subtitle");
  const authUsername = document.getElementById("auth-username");
  const authEmail = document.getElementById("auth-email");
  const authPassword = document.getElementById("auth-password");
  const authSubmit = document.getElementById("auth-submit");
  const authToggleText = document.getElementById("auth-toggle-text");
  const toggleAuth = document.getElementById("toggle-auth");
  const authMessage = document.getElementById("auth-message");
  const userWelcome = document.getElementById("user-welcome");
  const logoutBtn = document.getElementById("logout-btn");
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
    authPage.classList.add("hidden");
    chatPage.classList.remove("hidden");
    userWelcome.textContent = `👤 ${currentUser}`;
  }

  function showAuth() {
    authPage.classList.remove("hidden");
    chatPage.classList.add("hidden");
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
      sendButton.innerHTML = "<span>Enviar</span>";
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
    messageDiv.classList.add(
      "message",
      sender === "user" ? "user-message" : "bot-message",
    );
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

  // Función para actualizar la UI del toggle
  function updateAuthToggleUI() {
    if (isRegisterMode) {
      authTitle.textContent = "Crear cuenta";
      authSubtitle.textContent = "Regístrate para acceder al chatbot";
      authEmail.classList.remove("hidden");
      authSubmit.textContent = "Registrarse";
      authToggleText.innerHTML =
        '¿Ya tienes cuenta? <a href="#" class="toggle-link">Inicia sesión</a>';
    } else {
      authTitle.textContent = "Iniciar sesión";
      authSubtitle.textContent = "Accede al chatbot de consulta histórica";
      authEmail.classList.add("hidden");
      authSubmit.textContent = "Entrar";
      authToggleText.innerHTML =
        '¿No tienes cuenta? <a href="#" class="toggle-link">Regístrate</a>';
    }
  }

  // Usar event delegation en el contenedor authToggleText
  authToggleText.addEventListener("click", (e) => {
    if (e.target.classList.contains("toggle-link")) {
      e.preventDefault();
      isRegisterMode = !isRegisterMode;
      updateAuthToggleUI();
      // Limpiar campos
      authUsername.value = "";
      authPassword.value = "";
      authEmail.value = "";
      authMessage.textContent = "";
    }
  });

  // Inicializar la UI del toggle (convierte el HTML inicial)
  updateAuthToggleUI();

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
          authSubtitle.textContent = "Accede al chatbot de consulta histórica";
          authEmail.classList.add("hidden");
          authSubmit.textContent = "Entrar";
          authToggleText.innerHTML =
            '¿No tienes cuenta? <a href=\"#\" id=\"toggle-auth\">Regístrate</a>';
          authUsername.value = "";
          authPassword.value = "";
        } else {
          // Mensajes claros según el error
          let msg = data.detail || "Error en el registro.";
          if (msg.includes("usuario ya existe")) {
            msg = "El nombre de usuario ya está en uso.";
          } else if (msg.includes("email ya está registrado")) {
            msg = "El email ya está registrado.";
          } else if (msg.includes("Completa todos los campos")) {
            msg = "Por favor, completa todos los campos.";
          } else if (msg.includes("no es válido")) {
            msg = "El email no es válido.";
          }
          authMessage.style.color = "#dc3545";
          authMessage.textContent = msg;
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
      addMessage(
        "❌ Error de conexión. Asegúrate de que FastAPI esté corriendo en http://127.0.0.1:8000",
        "bot",
      );
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
