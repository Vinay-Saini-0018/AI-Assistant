// ==========================================
// CONFIGURATION
// ==========================================

const API_URL = window.location.port === "8001"
    ? "/chat"
    : "http://127.0.0.1:8001/chat";

let currentThreadId = crypto.randomUUID();


// ==========================================
// ELEMENTS
// ==========================================

const messageInput = document.getElementById("messageInput");
const sendBtn = document.getElementById("sendBtn");
const messagesContainer = document.getElementById("messages");

const newChatBtn = document.getElementById("newChatBtn");
const chatHistoryContainer = document.getElementById("chatHistory");

const chatTitle = document.getElementById("chatTitle");


// ==========================================
// CHAT DATA
// ==========================================

let chats = [];

try {
    const savedChats = localStorage.getItem("chats");
    const parsedChats = savedChats ? JSON.parse(savedChats) : [];

    if (Array.isArray(parsedChats)) {
        chats = parsedChats;
    }
} catch (error) {
    localStorage.removeItem("chats");
}

let currentChatId = null;


// ==========================================
// INITIALIZATION
// ==========================================

function initialize() {

    if (chats.length === 0) {
        createNewChat();
    } else {
        currentChatId = chats[0].id;

        renderHistory();
        loadChat(currentChatId);
    }
}


// ==========================================
// CREATE NEW CHAT
// ==========================================

function createNewChat() {

    const chat = {
        id: crypto.randomUUID(),

        title: "New Chat",

        messages: []
    };

    chats.unshift(chat);

    currentChatId = chat.id;
    currentThreadId = chat.id;

    saveChats();

    renderHistory();

    renderMessages();

    chatTitle.textContent = "New Chat";

    messageInput.focus();
}


// ==========================================
// SAVE CHATS
// ==========================================

function saveChats() {

    localStorage.setItem(
        "chats",
        JSON.stringify(chats)
    );
}


// ==========================================
// GET CURRENT CHAT
// ==========================================

function getCurrentChat() {

    return chats.find(
        chat => chat.id === currentChatId
    );
}


// ==========================================
// RENDER CHAT HISTORY
// ==========================================

function renderHistory() {

    chatHistoryContainer.innerHTML = "";

    chats.forEach(chat => {

        const item = document.createElement("div");
        item.className = "history-item";

        if (chat.id === currentChatId) {
            item.classList.add("active");
        }

        // Chat title
        const title = document.createElement("span");
        title.textContent = chat.title;

        // Delete button
        const deleteBtn = document.createElement("button");
        deleteBtn.className = "delete-chat";
        deleteBtn.innerHTML = "×";

        deleteBtn.addEventListener("click", (event) => {
            event.stopPropagation();
            deleteChat(chat.id);
        });

        item.appendChild(title);
        item.appendChild(deleteBtn);

        // Open chat when clicking the history item
        item.addEventListener("click", () => {
            currentChatId = chat.id;
            currentThreadId = chat.id;

            loadChat(chat.id);
            renderHistory();
        });

        chatHistoryContainer.appendChild(item);
    });
}

function deleteChat(chatId) {

    const confirmed = confirm("Delete this chat?");

    if (!confirmed) {
        return;
    }

    chats = chats.filter(chat => chat.id !== chatId);

    saveChats();

    // If deleting currently opened chat
    if (currentChatId === chatId) {

        if (chats.length > 0) {

            currentChatId = chats[0].id;
            currentThreadId = chats[0].id;

            loadChat(currentChatId);

        } else {

            createNewChat();
            return;
        }
    }

    renderHistory();
}


// ==========================================
// LOAD CHAT
// ==========================================

function loadChat(chatId) {

    const chat = chats.find(
        chat => chat.id === chatId
    );

    if (!chat) return;

    currentChatId = chat.id;
    currentThreadId = chat.id;

    chatTitle.textContent = chat.title;

    renderMessages();
}


// ==========================================
// RENDER MESSAGES
// ==========================================

function renderMessages() {

    const chat = getCurrentChat();

    if (!chat) return;

    messagesContainer.innerHTML = "";

    if (chat.messages.length === 0) {

        const welcome = document.createElement("div");

        welcome.className = "welcome";

        welcome.innerHTML = `
            <h1>How can I help you?</h1>
            <p>Ask me anything.</p>
        `;

        messagesContainer.appendChild(welcome);

        return;
    }


    chat.messages.forEach(message => {

        addMessageToUI(
            message.role,
            message.content
        );

    });
}


// ==========================================
// ADD MESSAGE TO UI
// ==========================================

function addMessageToUI(role, content) {

    const message = document.createElement("div");

    message.className = `message ${role}`;

    const messageContent = document.createElement("div");

    messageContent.className = "message-content";

    messageContent.textContent = content;

    message.appendChild(messageContent);

    messagesContainer.appendChild(message);

    scrollToBottom();
}


// ==========================================
// SEND MESSAGE
// ==========================================

async function sendMessage() {

    const text = messageInput.value.trim();

    if (!text) return;

    const chat = getCurrentChat();

    if (!chat) return;


    // Remove welcome screen

    const welcome = messagesContainer.querySelector(".welcome");

    if (welcome) {
        welcome.remove();
    }


    // Add user message

    chat.messages.push({
        role: "user",
        content: text
    });


    addMessageToUI("user", text);


    // Create title from first message

    if (chat.messages.length === 1) {

        chat.title =
            text.length > 30
                ? text.substring(0, 30) + "..."
                : text;

        chatTitle.textContent = chat.title;

        renderHistory();
    }


    saveChats();


    // Clear input

    messageInput.value = "";

    autoResize();


    // Disable button while API is running

    sendBtn.disabled = true;


    // Show loading

    const loading = document.createElement("div");

    loading.className = "message assistant";

    loading.id = "loadingMessage";

    loading.innerHTML = `
        <div class="message-content">
            <div class="loading">
                <span></span>
                <span></span>
                <span></span>
            </div>
        </div>
    `;

    messagesContainer.appendChild(loading);

    scrollToBottom();


    try {

        // ======================================
        // API REQUEST
        // ======================================

        const response = await fetch(API_URL, {

            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({
                query: text,
                thread_id : currentThreadId
            })

        });

        if (!response.ok) {
            throw new Error(
                `Server error: ${response.status}`
            );
        }

        const reader = response.body.getReader();

        const decoder = new TextDecoder();

        let answer = "";


        // Create assistant message
        const assistantMessage = document.createElement("div");

        assistantMessage.className = "message assistant";

        const assistantContent = document.createElement("div");

        assistantContent.className = "message-content";

        assistantMessage.appendChild(assistantContent);

        messagesContainer.appendChild(assistantMessage);


        // Read stream chunk by chunk
        while (true) {

            const { value, done } = await reader.read();

            if (done) {
                break;
            }

            const chunk = decoder.decode(value);

            answer += chunk;

            // Show new chunk immediately
            assistantContent.textContent = answer;

            scrollToBottom();
        }

        chat.messages.push({
            role: "assistant",
            content: answer
        });

        saveChats();


        // Remove loading

        const loadingMessage =
            document.getElementById("loadingMessage");

        if (loadingMessage) {
            loadingMessage.remove();
        }



    }

    catch (error) {
        console.error("FULL ERROR:", error);

        const loadingMessage =
            document.getElementById("loadingMessage");

        if (loadingMessage) {
            loadingMessage.remove();
        }

        addMessageToUI(
            "assistant",
            error.message
        );
    }


    sendBtn.disabled = false;

    messageInput.focus();
}


// ==========================================
// AUTO RESIZE TEXTAREA
// ==========================================

function autoResize() {

    messageInput.style.height = "auto";

    messageInput.style.height =
        Math.min(
            messageInput.scrollHeight,
            150
        ) + "px";
}


// ==========================================
// SCROLL TO BOTTOM
// ==========================================

function scrollToBottom() {

    messagesContainer.scrollTop =
        messagesContainer.scrollHeight;
}


// ==========================================
// BUTTON EVENTS
// ==========================================

sendBtn.addEventListener(
    "click",
    sendMessage
);


newChatBtn.addEventListener(
    "click",
    createNewChat
);


// ==========================================
// ENTER KEY
// ==========================================

messageInput.addEventListener(
    "keydown",
    event => {

        if (
            event.key === "Enter" &&
            !event.shiftKey
        ) {

            event.preventDefault();

            sendMessage();
        }
    }
);


// ==========================================
// TEXTAREA RESIZE
// ==========================================

messageInput.addEventListener(
    "input",
    autoResize
);


// ==========================================
// START APPLICATION
// ==========================================

initialize();