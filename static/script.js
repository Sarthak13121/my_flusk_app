document.addEventListener('DOMContentLoaded', () => {
    // ----------------------------------------------------------------------
    // 1. VARIABLE DECLARATIONS
    // ----------------------------------------------------------------------
    const navItems = document.querySelectorAll('.nav-item');
    const pageTitle = document.getElementById('page-title');
    const contentPages = document.querySelectorAll('.page-content');
    
    // STATE VARIABLES
    let currentClientId = null;
    let currentTaskId = null;

    // ======================================================================
    // 2. SUPPORT & HELPER FUNCTIONS - CLIENTS
    // ======================================================================
    
    // --- 2a. WhatsApp Handler (Click-to-Chat) ---
    function handleWhatsAppClick(e) {
        const phone = e.target.getAttribute('data-phone');
        const name = e.target.getAttribute('data-name');
        const message = prompt(`Enter message for ${name}:`); 

        if (message) {
            const encodedMessage = encodeURIComponent(message);
            const whatsappUrl = `https://wa.me/${phone}?text=${encodedMessage}`;
            window.open(whatsappUrl, '_blank'); 
            alert(`Opening WhatsApp chat for ${name}.`);
        } else {
            alert("Message sending cancelled.");
        }
    }

    // --- 2b. Client Form Toggler ---
    function toggleAddClientForm(show) {
        const formArea = document.getElementById('add-client-form-area');
        formArea.style.display = show ? 'block' : 'none';

        if (!show || currentClientId === null) {
            currentClientId = null; 
            document.querySelector('#add-client-form-area h3').textContent = 'Add New Client';
            document.getElementById('save-new-client-btn').textContent = 'Save Client';
            document.getElementById('new-client-name').value = '';
            document.getElementById('new-client-phone').value = '';
            document.getElementById('new-client-status').value = 'Active'; 
        }
    }

    // --- 2c. Delete Client Logic (CRUD Delete) ---
    function deleteClient(clientId) {
        if (!confirm(`Are you sure you want to delete client ID ${clientId}?`)) return;

        fetch(`/api/clients/${clientId}`, { method: 'DELETE' })
        .then(response => {
            if (response.ok) {
                alert(`Client ID ${clientId} deleted successfully.`);
                fetchAndRenderClients(); 
            } else {
                alert('Failed to delete client.');
            }
        })
        .catch(error => {
            console.error('Delete client error:', error);
            alert('An error occurred during deletion.');
        });
    }
    
    // --- 2d. Save Client Logic (CRUD Create/Update) ---
    function saveClient() {
        const name = document.getElementById('new-client-name').value;
        const phone = document.getElementById('new-client-phone').value;
        const status = document.getElementById('new-client-status').value;

        if (!name) {
            alert("Client Name is required.");
            return;
        }

        const clientData = { name: name, phone: phone, status: status };
        
        const method = currentClientId ? 'PUT' : 'POST';
        const endpoint = currentClientId ? `/api/clients/${currentClientId}` : '/api/clients';
        
        fetch(endpoint, {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(clientData),
        })
        .then(response => response.json())
        .then(result => {
            if (result.status === 'success') {
                const action = method === 'POST' ? 'added' : 'updated';
                alert(`Client ${name} ${action} successfully!`);
                toggleAddClientForm(false);
                fetchAndRenderClients();
            } else {
                alert(`Error ${method === 'POST' ? 'adding' : 'updating'} client: ${result.message}`);
            }
        })
        .catch(error => {
            console.error('Save Client Error:', error);
            alert('An error occurred while saving the client.');
        });
    }

    // --- 2e. Start Client Edit Logic ---
    function startClientEdit(clientId) {
        currentClientId = clientId;
        
        fetch(`/api/clients/${clientId}`)
            .then(response => response.json())
            .then(client => {
                document.getElementById('new-client-name').value = client.name;
                document.getElementById('new-client-phone').value = client.phone;
                document.getElementById('new-client-status').value = client.status;
                
                document.querySelector('#add-client-form-area h3').textContent = 'Edit Client';
                document.getElementById('save-new-client-btn').textContent = 'Save Changes';
                
                toggleAddClientForm(true);
            })
            .catch(error => {
                console.error('Error fetching client for edit:', error);
                alert('Could not load client data for editing.');
            });
    }

    // ======================================================================
    // 3. SUPPORT & HELPER FUNCTIONS - TASKS (CRUD)
    // ======================================================================

    // --- 3a. Task Form Toggler ---
    function toggleAddTaskForm(show) {
        const formArea = document.getElementById('add-task-form-area');
        formArea.style.display = show ? 'block' : 'none';

        if (!show || currentTaskId === null) {
            currentTaskId = null;
            document.querySelector('#add-task-form-area h3').textContent = 'Add New Task';
            document.getElementById('save-task-btn').textContent = 'Save Task';
            document.getElementById('new-task-name').value = '';
            document.getElementById('new-task-due-date').value = '';
            document.getElementById('new-task-priority').value = 'Medium';
            document.getElementById('new-task-assigned-to').value = 'User';
        }
    }

    // --- 3b. Delete Task Logic (CRUD Delete) ---
    function deleteTask(taskId) {
        if (!confirm(`Are you sure you want to delete Task ID ${taskId}?`)) return;

        fetch(`/api/tasks/${taskId}`, { method: 'DELETE' })
        .then(response => {
            if (response.ok) {
                alert(`Task ID ${taskId} deleted successfully.`);
                fetchAndRenderTasks(); 
            } else {
                alert('Failed to delete task.');
            }
        });
    }

    // --- 3c. Start Task Edit Logic ---
    function startTaskEdit(taskId) {
        currentTaskId = taskId;
        fetch(`/api/tasks/${taskId}`)
            .then(response => response.json())
            .then(task => {
                document.getElementById('new-task-name').value = task.name;
                document.getElementById('new-task-due-date').value = task.due_date;
                document.getElementById('new-task-priority').value = task.priority;
                document.getElementById('new-task-assigned-to').value = task.assigned_to;
                
                document.querySelector('#add-task-form-area h3').textContent = 'Edit Task';
                document.getElementById('save-task-btn').textContent = 'Save Changes';
                
                toggleAddTaskForm(true);
            });
    }

    // --- 3d. Save Task Logic (CRUD Create/Update) ---
    function saveTask() {
        const name = document.getElementById('new-task-name').value;
        const dueDate = document.getElementById('new-task-due-date').value;
        const priority = document.getElementById('new-task-priority').value;
        const assignedTo = document.getElementById('new-task-assigned-to').value;

        if (!name) {
            alert("Task Name is required.");
            return;
        }

        const taskData = { name: name, due_date: dueDate, priority: priority, assigned_to: assignedTo };
        
        const method = currentTaskId ? 'PUT' : 'POST';
        const endpoint = currentTaskId ? `/api/tasks/${currentTaskId}` : '/api/tasks';
        
        fetch(endpoint, {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(taskData),
        })
        .then(response => response.json())
        .then(result => {
            if (result.status === 'success') {
                const action = method === 'POST' ? 'added' : 'updated';
                alert(`Task ${action} successfully!`);
                toggleAddTaskForm(false);
                fetchAndRenderTasks(); 
            } else {
                alert(`Error ${method === 'POST' ? 'adding' : 'updating'} task: ${result.message}`);
            }
        });
    }


    // ======================================================================
    // 4. DATA FETCHING FUNCTION: CLIENTS (CRUD Read)
    // ======================================================================
    function fetchAndRenderClients() {
        fetch('/api/clients')
            .then(response => {
                if (!response.ok) throw new Error(`Could not fetch data. Status: ${response.status}`);
                return response.json();
            })
            .then(data => {
                const clientsDisplayArea = document.getElementById('client-list-display'); 
                
                let html = '<table class="client-table"><thead><tr><th>Name</th><th>Status</th><th>Actions</th></tr></thead><tbody>';

                data.forEach(client => {
                    html += `
                        <tr>
                            <td>${client.name}</td>
                            <td><span class="status-tag status-${client.status.toLowerCase()}">${client.status}</span></td>
                            <td>
                                <button class="whatsapp-btn" data-phone="${client.phone}" data-name="${client.name}">Send WhatsApp</button>
                                <button class="edit-btn" data-id="${client.id}">Edit</button>
                                <button class="delete-btn" data-id="${client.id}">Delete</button>
                            </td>
                        </tr>
                    `;
                });
                html += '</tbody></table>';
                clientsDisplayArea.innerHTML = html;
                
                // Re-attach all event listeners after rendering the new HTML
                document.querySelectorAll('.whatsapp-btn').forEach(button => {
                    button.addEventListener('click', handleWhatsAppClick);
                });
                document.querySelectorAll('.delete-btn').forEach(button => {
                    button.addEventListener('click', (e) => {
                        const clientId = e.target.getAttribute('data-id');
                        deleteClient(clientId);
                    });
                });
                document.querySelectorAll('.edit-btn').forEach(button => {
                    button.addEventListener('click', (e) => {
                        const clientId = e.target.getAttribute('data-id');
                        startClientEdit(clientId); 
                    });
                });
            })
            .catch(error => {
                console.error('Error fetching and rendering clients:', error);
                document.getElementById('client-list-display').innerHTML = `<h2>Error Loading Data</h2><p>An error occurred loading client data: ${error.message}</p>`;
            });
    }

    
    // ======================================================================
    // 5. DATA FETCHING FUNCTION: TASKS (CRUD Read)
    // ======================================================================
    function fetchAndRenderTasks() {
        fetch('/api/tasks')
            .then(response => {
                if (!response.ok) throw new Error('Could not fetch tasks data');
                return response.json();
            })
            .then(data => {
                const tasksDisplayArea = document.getElementById('task-list-display'); 
                
                let html = '<table class="client-table"><thead><tr><th>Task Name</th><th>Due Date</th><th>Priority</th><th>Assigned To</th><th>Actions</th></tr></thead><tbody>';

                data.forEach(task => {
                    html += `
                        <tr>
                            <td>${task.name}</td>
                            <td>${task.due_date}</td>
                            <td><span class="status-tag status-${task.priority.toLowerCase()}">${task.priority}</span></td>
                            <td>${task.assigned_to}</td>
                            <td>
                                <button class="edit-btn" data-id="${task.id}">Edit</button>
                                <button class="delete-btn" data-id="${task.id}" style="background-color: #dc3545;">Delete</button>
                            </td>
                        </tr>
                    `;
                });
                html += '</tbody></table>';
                tasksDisplayArea.innerHTML = html;
                
                // Re-attach all event listeners for Edit and Delete buttons
                document.querySelectorAll('#task-list-display .delete-btn').forEach(button => {
                    button.addEventListener('click', (e) => {
                        deleteTask(e.target.getAttribute('data-id'));
                    });
                });
                document.querySelectorAll('#task-list-display .edit-btn').forEach(button => {
                    button.addEventListener('click', (e) => {
                        startTaskEdit(e.target.getAttribute('data-id'));
                    });
                });
            })
            .catch(error => {
                console.error('Error fetching and rendering tasks:', error);
                document.getElementById('task-list-display').innerHTML = '<h2>Error Loading Tasks</h2><p>An error occurred loading task data.</p>';
            });
    }


    // ======================================================================
    // 6. NAVIGATION FUNCTION
    // ======================================================================
    function switchPage(pageName) {
        pageTitle.textContent = pageName.charAt(0).toUpperCase() + pageName.slice(1);
        contentPages.forEach(page => page.classList.remove('active'));
        const activePage = document.getElementById(`${pageName}-content`);
        if (activePage) activePage.classList.add('active');

        navItems.forEach(item => {
            item.classList.remove('active');
            if (item.getAttribute('data-page') === pageName) item.classList.add('active');
        });
        
        if (pageName === 'clients') {
            fetchAndRenderClients(); 
        } else if (pageName === 'tasks') {
            fetchAndRenderTasks();
        } else if (pageName === 'settings') { 
            console.log("Settings page loaded.");
        }
    }


    // ======================================================================
    // 7. INITIALIZATION & EVENT LISTENERS
    // ======================================================================
    
    // --- Navigation Listeners ---
    navItems.forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault(); 
            const pageName = item.getAttribute('data-page');
            switchPage(pageName);
        });
    });

    // --- Client Form Listeners ---
    const addClientBtn = document.getElementById('add-client-btn');
    const saveNewClientBtn = document.getElementById('save-new-client-btn');
    const cancelAddClientBtn = document.getElementById('cancel-add-client');

    if (addClientBtn) {
        addClientBtn.addEventListener('click', () => toggleAddClientForm(true));
    }
    if (saveNewClientBtn) { 
        saveNewClientBtn.addEventListener('click', saveClient); 
    }
    if (cancelAddClientBtn) {
        cancelAddClientBtn.addEventListener('click', () => toggleAddClientForm(false));
    }

    // --- Task Form Listeners ---
    const addTaskBtn = document.getElementById('add-task-btn');
    const saveTaskBtn = document.getElementById('save-task-btn');
    const cancelAddTaskBtn = document.getElementById('cancel-add-task');

    if (addTaskBtn) {
        addTaskBtn.addEventListener('click', () => toggleAddTaskForm(true));
    }
    if (saveTaskBtn) {
        saveTaskBtn.addEventListener('click', saveTask);
    }
    if (cancelAddTaskBtn) {
        cancelAddTaskBtn.addEventListener('click', () => toggleAddTaskForm(false));
    }

    // --- Settings Page Logic Listener ---
    const saveButton = document.getElementById('save-settings');
    if (saveButton) {
        saveButton.addEventListener('click', (e) => {
            e.preventDefault(); 
            const newUsername = document.getElementById('username').value;
            const newEmail = document.getElementById('email').value;
            const newTheme = document.getElementById('theme').value;

            console.log("Saving Settings:", { newUsername, newEmail, newTheme });
            alert("Settings saved successfully! (Data not permanently stored in this version)");
            
            document.querySelector('.user-info').textContent = `Welcome, ${newUsername}`;
        });
    }

    // Initialize the dashboard on load
    switchPage('dashboard');
});