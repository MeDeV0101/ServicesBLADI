// Added additional logging for the WebSocket connection to client_chat.html
// 1. Enhanced onmessage handler 
// 2. Added better error handling
// 3. Added state logging to track message flow

chatSocket.onmessage = function(e) {
    try {
        const data = JSON.parse(e.data);
        console.log('Client received message:', data);
        
        // Si erreur, afficher message d'erreur
        if (data.error) {
            console.error('Error from server:', data.error);
            displayError(data.error);
            return;
        }
        
        // Traiter les indicateurs de frappe
        if (data.typing) {
            console.log('Typing indicator received:', data.typing);
            if (data.typing.user_id !== currentUserId) {
                if (data.typing.is_typing) {
                    typingUserName.textContent = data.typing.user_name;
                    typingIndicator.style.display = 'block';
                } else {
                    typingIndicator.style.display = 'none';
                }
            }
            return;
        }
        
        // Pour les messages sortants, mettre à jour le statut
        if (data.sender_id === currentUserId) {
            console.log('Updating status for outgoing message');
            const pendingMessages = document.querySelectorAll('[data-message-pending="true"]');
            pendingMessages.forEach(msg => {
                if (msg.dataset.messageContent === data.message) {
                    const statusDiv = msg.querySelector('.message-status');
                    if (statusDiv) {
                        statusDiv.textContent = 'Envoyé';
                        statusDiv.className = 'message-status message-delivered';
                    }
                    msg.removeAttribute('data-message-pending');
                }
            });
        } else {
            // Ajouter le message à la conversation
            console.log('Adding incoming message to chat from:', data.sender_name, '(ID:', data.sender_id, ')');
            addMessageToChat(data);
        }
    } catch (error) {
        console.error('Error processing WebSocket message:', error);
        console.error('Raw message:', e.data);
    }
};
