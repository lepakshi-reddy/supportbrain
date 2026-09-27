const API_URL = "http://127.0.0.1:8000";

// --------------------------------------------------
// CUSTOMER
// --------------------------------------------------
const userId = "demo-customer-001";

// --------------------------------------------------
// ELEMENTS
// --------------------------------------------------
const chatBox = document.getElementById("chatBox");
const messageInput = document.getElementById("messageInput");
const sendButton = document.getElementById("sendButton");
const memoryList = document.getElementById("memoryList");
const memoryCount = document.getElementById("memoryCount");

// --------------------------------------------------
// SEND MESSAGE
// --------------------------------------------------
async function sendMessage() {
    const message = messageInput.value.trim();
    if (!message) {
        return;
    }

    // Add user message
    addMessage("user", message);

    // Clear input
    messageInput.value = "";

    // Disable button
    sendButton.disabled = true;
    sendButton.textContent = "Sending...";

    // Loading
    const loading = addMessage("assistant", "Thinking...");

    try {
        const response = await fetch(`${API_URL}/chat`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                user_id: userId,
                message: message
            })
        });

        const data = await response.json();

        // Remove loading message
        loading.remove();

        if (!data.success) {
            addMessage("assistant", "Sorry, something went wrong.");
            return;
        }

        // Show AI response
        addMessage("assistant", data.answer);

        // Show memories
        showMemories(data.memories);

    } catch (error) {
        console.error(error);
        loading.remove();
        addMessage(
            "assistant",
            "Could not connect to SupportBrain. Make sure the backend is running."
        );
    } finally {
        sendButton.disabled = false;
        sendButton.textContent = "Send";
        messageInput.focus();
    }
}

// --------------------------------------------------
// ADD MESSAGE
// --------------------------------------------------
function addMessage(type, text) {
    const message = document.createElement("div");
    message.className = `message ${type}`;

    const content = document.createElement("div");
    content.className = "message-content";

    const label = document.createElement("div");
    label.className = "message-label";
    label.textContent = type === "user" ? "YOU" : "SUPPORTBRAIN";

    const textElement = document.createElement("div");
    textElement.textContent = text;

    content.appendChild(label);
    content.appendChild(textElement);
    message.appendChild(content);
    chatBox.appendChild(message);

    // Scroll down
    chatBox.scrollTop = chatBox.scrollHeight;

    return message;
}

// --------------------------------------------------
// SHOW MEMORIES
// --------------------------------------------------
function showMemories(memories) {
    memoryList.innerHTML = "";

    if (!memories || memories.length === 0) {
        memoryList.innerHTML = `
            <div class="empty-memory">
                No relevant memories found.
            </div>
        `;
        memoryCount.textContent = "0";
        return;
    }

    memoryCount.textContent = memories.length;

    memories.forEach((memory) => {
        const card = document.createElement("div");
        card.className = "memory-card";
        card.innerHTML = `
            <div class="memory-type">
                ${escapeHtml(memory.type || "memory")}
            </div>
            <div>
                ${escapeHtml(memory.text)}
            </div>
        `;
        memoryList.appendChild(card);
    });
}

// --------------------------------------------------
// NEW CONVERSATION
// --------------------------------------------------
function newConversation() {
    chatBox.innerHTML = `
        <div class="welcome">
            <div class="welcome-icon">🧠</div>
            <h2>New Conversation</h2>
            <p>
                This is a fresh conversation, but SupportBrain can still use relevant memories from previous conversations.
            </p>
            <div class="demo-tip">
                Try asking:
                <br><br>
                <strong>"What was my previous support issue?"</strong>
            </div>
        </div>
    `;

    messageInput.value = "";
    memoryList.innerHTML = `
        <div class="empty-memory">
            Send a message to recall previous customer information.
        </div>
    `;
    memoryCount.textContent = "0";
    messageInput.focus();
}

// --------------------------------------------------
// ENTER KEY
// --------------------------------------------------
messageInput.addEventListener("keydown", function(event) {
    if (event.key === "Enter" && !event.shiftKey) {
        event.preventDefault();
        sendMessage();
    }
});

// --------------------------------------------------
// HTML ESCAPE
// --------------------------------------------------
function escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
}
