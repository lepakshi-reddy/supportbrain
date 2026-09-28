const API_URL = (
    (typeof window !== "undefined" && window.VITE_API_URL) ||
    (typeof import.meta !== "undefined" && import.meta.env && import.meta.env.VITE_API_URL) ||
    "http://127.0.0.1:8000"
).replace(/\/$/, "");

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
const activityList = document.getElementById("activityList");

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

        const data = await response.json().catch(() => ({}));

        loading.remove();

        if (!response.ok || !data.success) {
            const detail = data?.error || data?.detail || "Unknown backend error";
            addMessage("assistant", `Backend error (${response.status || "network"}): ${detail}`);
            return;
        }

        addMessage("assistant", data.answer);
        showMemories(data.memories);
        showActivity(data.activity || [
            { type: "retained", text: "Memory retained for this conversation." },
            { type: "recalled", text: "Relevant memories were used for context." }
        ]);

    } catch (error) {
        console.error("Chat request failed:", error);
        console.error(error?.stack || error);
        loading.remove();
        addMessage(
            "assistant",
            `Could not connect to SupportBrain: ${error.message || "network error"}`
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

function showActivity(activityItems) {
    if (!activityList) return;

    activityList.innerHTML = "";

    if (!activityItems || activityItems.length === 0) {
        activityList.innerHTML = '<div class="empty-activity">No activity yet.</div>';
        return;
    }

    activityItems.forEach((item) => {
        const row = document.createElement("div");
        row.className = "activity-item";
        const isRetained = (item.type || "").toLowerCase() === "retained";
        row.innerHTML = `
            <div class="activity-icon ${isRetained ? "retained" : "recalled"}">${isRetained ? "✓" : "↩"}</div>
            <div class="activity-copy">
                <strong>${escapeHtml(isRetained ? "Memory retained" : "Memory recalled")}</strong>
                <div>${escapeHtml(item.text || "Support memory updated.")}</div>
            </div>
        `;
        activityList.appendChild(row);
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
    activityList.innerHTML = `
        <div class="empty-activity">
            No activity yet.
        </div>
    `;
    memoryCount.textContent = "0";
    messageInput.focus();
}

// --------------------------------------------------
// ENTER KEY
// --------------------------------------------------
messageInput.addEventListener("keydown", function (event) {
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

