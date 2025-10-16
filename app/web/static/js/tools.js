document.addEventListener('DOMContentLoaded', () => {
    const toolList = document.getElementById('tool-list');
    const addToolForm = document.getElementById('add-tool-form');

    const editToolModal = document.getElementById('edit-tool-modal');
    const closeModalBtn = document.getElementById('close-modal-btn');
    const editToolForm = document.getElementById('edit-tool-form');
    const editToolId = document.getElementById('edit-tool-id');
    const editToolName = document.getElementById('edit-tool-name');
    const editToolDescription = document.getElementById('edit-tool-description');
    const editToolParameters = document.getElementById('edit-tool-parameters');

    const showModal = () => editToolModal.classList.remove('hidden');
    const hideModal = () => editToolModal.classList.add('hidden');

    closeModalBtn.addEventListener('click', hideModal);

    const renderTools = (tools) => {
        toolList.innerHTML = '';
        if (tools && tools.length > 0) {
            tools.forEach(tool => {
                const toolCard = `
                    <div class="bg-white p-6 rounded-lg shadow-md">
                        <h6 class="text-lg font-bold">${tool.name}</h6>
                        <p class="text-gray-600">${tool.description}</p>
                        <div class="mt-4">
                            <button class="bg-gray-500 hover:bg-gray-700 text-white font-bold py-2 px-4 rounded edit-tool-btn" data-tool='${JSON.stringify(tool)}'>Edit</button>
                            <button class="bg-red-500 hover:bg-red-700 text-white font-bold py-2 px-4 rounded delete-tool-btn" data-tool-id="${tool.id}">Delete</button>
                        </div>
                    </div>
                `;
                toolList.insertAdjacentHTML('beforeend', toolCard);
            });
        } else {
            toolList.innerHTML = '<p class="text-gray-500">No tools found for this server.</p>';
        }
    };

    const loadTools = async () => {
        try {
            const response = await fetch(serverInfo.server.url + '/tools');
            const data = await response.json();
            renderTools(data.tools);
        } catch (error) {
            console.error('Error loading tools:', error);
        }
    };

    addToolForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const name = document.getElementById('tool-name').value;
        const description = document.getElementById('tool-description').value;
        const parameters = JSON.parse(document.getElementById('tool-parameters').value);
        const apiUrl = document.getElementById('tool-api-url').value;
        const httpMethod = document.getElementById('tool-http-method').value;

        try {
            const response = await fetch(serverInfo.server.url + '/tools', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name, description, parameters, api_url: apiUrl, http_method: httpMethod })
            });
            if (response.ok) {
                loadTools();
                addToolForm.reset();
            } else {
                alert('Failed to add tool.');
            }
        } catch (error) {
            console.error('Error adding tool:', error);
        }
    });

    toolList.addEventListener('click', async (e) => {
        if (e.target.classList.contains('delete-tool-btn')) {
            const toolId = e.target.dataset.toolId;
            if (confirm('Are you sure you want to delete this tool?')) {
                try {
                    const response = await fetch(`${serverInfo.server.url}/tools/${toolId}`, { method: 'DELETE' });
                    if (response.ok) {
                        loadTools();
                    } else {
                        alert('Failed to delete tool.');
                    }
                } catch (error) {
                    console.error('Error deleting tool:', error);
                }
            }
        }

        if (e.target.classList.contains('edit-tool-btn')) {
            const tool = JSON.parse(e.target.dataset.tool);
            editToolId.value = tool.id;
            editToolName.value = tool.name;
            editToolDescription.value = tool.description;
            editToolParameters.value = JSON.stringify(tool.parameters, null, 2);
            document.getElementById('edit-tool-api-url').value = tool.api_url;
            document.getElementById('edit-tool-http-method').value = tool.http_method;
            showModal();
        }
    });

    editToolForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const toolId = editToolId.value;
        const name = editToolName.value;
        const description = editToolDescription.value;
        const parameters = JSON.parse(editToolParameters.value);
        const apiUrl = document.getElementById('edit-tool-api-url').value;
        const httpMethod = document.getElementById('edit-tool-http-method').value;

        try {
            const response = await fetch(`${serverInfo.server.url}/tools/${toolId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name, description, parameters, api_url: apiUrl, http_method: httpMethod })
            });
            if (response.ok) {
                hideModal();
                loadTools();
            } else {
                alert('Failed to update tool.');
            }
        } catch (error) {
            console.error('Error updating tool:', error);
        }
    });

    // Initial load of tools
    renderTools(initialTools);
});