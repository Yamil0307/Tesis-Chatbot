// Lógica JavaScript para interactuar con la API
document.addEventListener("DOMContentLoaded", () => {
  const chatForm = document.getElementById("chat-form");
  const userInput = document.getElementById("user-input");
  const chatMessages = document.getElementById("chat-messages");
  const sendButton = document.getElementById("send-button");
  const apiStatusSpan = document.getElementById("api-status");

  // URL de tu API de FastAPI
  const API_URL = "http://127.0.0.1:8000/chat";

  // NUEVO: Variable para guardar el thread_id de la sesión actual
  let currentThreadId = null;

  // Función de utilidad para agregar un mensaje al contenedor
  function addMessage(text, sender, isRag = false) {
    const messageDiv = document.createElement("div");
    messageDiv.classList.add("message");
    messageDiv.classList.add(
      sender === "user" ? "user-message" : "bot-message"
    );

    let content = text.replace(/\n/g, "<br>");

    if (sender === "bot" && isRag) {
      // Indicador de RAG
      content += `<div class="rag-active">Fuente: Documentos de la UO (RAG)</div>`;
    } else if (sender === "bot") {
      // Indicador de conocimiento general
      content += `<div class="rag-active">Fuente: Conocimiento General (Gemini)</div>`;
    }

    messageDiv.innerHTML = content;
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight; // Scroll automático
  }

  // Función para mostrar/ocultar el spinner
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

  // Comprobación de la conexión inicial (opcional pero profesional)
  async function checkApiStatus() {
    try {
      // Intentamos conectar al endpoint /chat, pero solo para verificar si está vivo
      const response = await fetch("http://127.0.0.1:8000", { method: "GET" });
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

  // NUEVO: Cargar thread_id del localStorage al iniciar (para recuperar sesión anterior)
  function loadSessionId() {
    currentThreadId = localStorage.getItem("threadId");
    if (currentThreadId) {
      console.log(`📝 Sesión recuperada: ${currentThreadId}`);
      // NO mostrar mensaje automático - la sesión se recupera silenciosamente
    }
  }

  // NUEVO: Guardar thread_id en localStorage
  function saveSessionId(threadId) {
    currentThreadId = threadId;
    localStorage.setItem("threadId", threadId);
    console.log(`💾 Sesión guardada: ${threadId}`);
  }

  loadSessionId();

  // Evento principal que maneja el envío del formulario y la comunicación con FastAPI
  chatForm.addEventListener("submit", async function (event) {
    event.preventDefault();
    const message = userInput.value.trim();
    if (!message) return;

    addMessage(message, "user");
    userInput.value = "";
    toggleLoading(true);

    try {
      const response = await fetch(API_URL, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          user_input: message,
          thread_id: currentThreadId, // ← NUEVO: Incluir thread_id en la solicitud
        }),
      });

      const data = await response.json();

      // NUEVO: Guardar el thread_id de la respuesta (si es la primera solicitud)
      if (data.thread_id && !currentThreadId) {
        saveSessionId(data.thread_id);
      }

      if (data.status === "success") {
        addMessage(data.response, "bot", data.agent_used_tool);
      } else {
        addMessage(`❌ Error del Agente: ${data.response}`, "bot");
      }
    } catch (error) {
      console.error("Error al comunicarse con la API:", error);
      addMessage(
        "❌ Error de conexión. Asegúrate de que FastAPI esté corriendo en http://127.0.0.1:8000.",
        "bot"
      );
    } finally {
      toggleLoading(false);
      checkApiStatus(); // Re-chequea el estado después de la interacción
    }
  });
});
