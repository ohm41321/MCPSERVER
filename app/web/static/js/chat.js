document.addEventListener('DOMContentLoaded', () => {
    const chatForm = document.getElementById('chat-form');
    const messageInput = document.getElementById('message-input');
    const chatContainer = document.getElementById('chat-container');

    const addMessage = (message, sender) => {
        const messageElement = document.createElement('div');
        messageElement.classList.add('p-2', 'rounded-lg', 'mb-2');
        if (sender === 'user') {
            messageElement.classList.add('bg-blue-500', 'text-white', 'self-end');
        } else {
            messageElement.classList.add('bg-gray-300', 'text-black', 'self-start');
        }
        messageElement.textContent = message;
        chatContainer.appendChild(messageElement);
        chatContainer.scrollTop = chatContainer.scrollHeight;
    };

    chatForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const message = messageInput.value.trim();
        if (!message) return;

        addMessage(message, 'user');
        messageInput.value = '';

        const pathParts = window.location.pathname.split('/');
        const agentId = pathParts[pathParts.length - 1];

        try {
            const response = await fetch('/ask', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ 
                    question: message,
                    agent_id: agentId
                }),
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            const botMessage = data.answer || 'Sorry, I could not get a response.';
            addMessage(botMessage, 'bot');

        } catch (error) {
            console.error('Error sending message:', error);
            addMessage('An error occurred while sending your message.', 'bot');
        }
    });

    // Initial message from the bot
    addMessage(`Welcome! You can ask me anything.`, 'bot');
});
