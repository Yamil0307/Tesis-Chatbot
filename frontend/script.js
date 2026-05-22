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
  const homePage = document.getElementById("home-page");
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
  let isQueryRunning = false;
  let currentQueryId = null;
  let lastCancelledQueryId = null;

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
    currentQueryId = null;
    lastCancelledQueryId = null;
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
    homePage.classList.add("hidden");
    chatPage.classList.remove("hidden");
    userWelcome.textContent = `👤 ${currentUser}`;
  }

  function showHome() {
    authPage.classList.add("hidden");
    homePage.classList.remove("hidden");
    chatPage.classList.add("hidden");
    document.getElementById("user-welcome-home").textContent =
      `👤 ${currentUser}`;
  }

  function showAuth() {
    authPage.classList.remove("hidden");
    homePage.classList.add("hidden");
    chatPage.classList.add("hidden");
    authMessage.textContent = "";
    authPassword.value = "";
  }

  function toggleLoading(isLoading) {
    if (isLoading) {
      isQueryRunning = true;
      sendButton.disabled = false; // Permitir hacer clic para cancelar
      sendButton.innerHTML = `
        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
          <rect x="4" y="4" width="16" height="16" rx="2"/>
        </svg>
      `;
      sendButton.id = "cancel-button";
      apiStatusSpan.textContent = "Procesando...";
    } else {
      isQueryRunning = false;
      sendButton.disabled = false;
      sendButton.innerHTML = "<span>Enviar</span>";
      sendButton.id = "send-button";
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
  async function cancelQuery() {
    if (!currentThreadId || !currentToken) {
      addMessage("❌ No hay consulta en proceso para cancelar.", "bot");
      return;
    }

    try {
      const response = await fetch(`${API_BASE}/cancel/${currentThreadId}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${currentToken}`,
        },
      });

      const data = await response.json();
      if (response.ok) {
        // Marcar esta consulta como cancelada para ignorar respuestas futuras
        lastCancelledQueryId = currentQueryId;
        console.log(`🛑 Cancelada consulta ID: ${lastCancelledQueryId}`);
        addMessage("⏹️ Consulta cancelada por el usuario.", "bot");
        isQueryRunning = false;
        toggleLoading(false);
      } else {
        addMessage("❌ No se pudo cancelar la consulta.", "bot");
      }
    } catch (error) {
      console.error("Error al cancelar:", error);
      addMessage("❌ Error al cancelar la consulta.", "bot");
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

  // Event listener para cerrar sesión desde home
  const logoutBtnHome = document.getElementById("logout-btn-home");
  if (logoutBtnHome) {
    logoutBtnHome.addEventListener("click", () => {
      clearSession();
      showAuth();
    });
  }

  // Event listener para botón "Iniciar Consulta"
  const goToChatBtn = document.getElementById("go-to-chat-btn");
  if (goToChatBtn) {
    goToChatBtn.addEventListener("click", () => {
      showChat();
    });
  }

  // Event listener para volver al inicio desde el chat
  const backToHomeBtn = document.getElementById("back-to-home-btn");
  if (backToHomeBtn) {
    backToHomeBtn.addEventListener("click", (e) => {
      e.preventDefault();
      showHome();
    });
  }

  // Event listener para ir al chat desde home (link en header)
  const goToChatLink = document.getElementById("go-to-chat-link");
  if (goToChatLink) {
    goToChatLink.addEventListener("click", (e) => {
      e.preventDefault();
      showChat();
    });
  }
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
          showHome();
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

    // Si hay una consulta en proceso y el usuario hace clic, cancelar
    if (isQueryRunning && currentThreadId) {
      await cancelQuery();
      return;
    }

    const message = userInput.value.trim();
    if (!message || !currentToken) return;

    // Resetear flag de último cancelado si es una nueva sesión
    if (!currentThreadId) {
      lastCancelledQueryId = null;
    }

    // Agregar mensaje del usuario
    addMessage(message, "user");
    userInput.value = "";
    toggleLoading(true);

    // Generar ID único para esta consulta
    currentQueryId =
      Date.now().toString() + Math.random().toString(36).substr(2, 9);

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
          query_id: currentQueryId,
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

      // Ignorar respuesta si esta consulta fue cancelada
      if (data.query_id && data.query_id === lastCancelledQueryId) {
        console.log(
          `ℹ️ Respuesta ignorada - Query ID recibido: ${data.query_id}, Last Cancelled: ${lastCancelledQueryId}`,
        );
        toggleLoading(false);
        checkApiStatus();
        return;
      }

      console.log(
        `✅ Aceptando respuesta - Query ID: ${data.query_id}, Current Query: ${currentQueryId}`,
      );

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
    showHome();
  } else {
    showAuth();
  }

  // Verificar estado de la API
  checkApiStatus();
});
