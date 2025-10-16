document.addEventListener('DOMContentLoaded', () => {
    const createAgentForm = document.getElementById('create-agent-form');

    if (createAgentForm) {
        createAgentForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const name = document.getElementById('agent-name').value;
            const description = document.getElementById('agent-description').value;

            try {
                const response = await fetch('/agents', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ name, description })
                });

                if (response.ok) {
                    window.location.reload();
                } else {
                    alert('Failed to create agent.');
                }
            } catch (error) {
                console.error('Error creating agent:', error);
                alert('Error creating agent. Check the console for details.');
            }
        });
    }
});
