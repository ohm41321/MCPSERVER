document.addEventListener('DOMContentLoaded', () => {
    const addServerForm = document.getElementById('add-server-form');
    const assignedServersList = document.getElementById('assigned-servers-list');

    if (addServerForm) {
        addServerForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const serverUrl = document.getElementById('server-url').value;

            try {
                const response = await fetch(`/agents/${agentId}/servers/by_url`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ url: serverUrl })
                });

                if (response.ok) {
                    window.location.reload();
                } else {
                    const error = await response.json();
                    alert(`Failed to add server to agent: ${error.detail}`);
                }
            } catch (error) {
                console.error('Error adding server to agent:', error);
                alert('Error adding server to agent. Check the console for details.');
            }
        });
    }

    if (assignedServersList) {
        assignedServersList.addEventListener('click', async (e) => {
            if (e.target.classList.contains('remove-server-btn')) {
                const serverId = e.target.dataset.serverId;
                if (confirm('Are you sure you want to remove this server from the agent?')) {
                    try {
                        const response = await fetch(`/agents/${agentId}/servers/${serverId}`, {
                            method: 'DELETE'
                        });

                        if (response.ok) {
                            window.location.reload();
                        } else {
                            alert('Failed to remove server from agent.');
                        }
                    } catch (error) {
                        console.error('Error removing server from agent:', error);
                        alert('Error removing server from agent. Check the console for details.');
                    }
                }
            }
        });
    }
});
