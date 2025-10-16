class CivicBriefsApp {
    constructor() {
        this.baseURL = 'http://localhost:8000';
        this.token = localStorage.getItem('token');
        this.role = localStorage.getItem('role');
        this.init();
    }

    init() {
        if (!this.token) {
            window.location.href = '/login';
            return;
        }
        
        this.setupAuth();
        this.setupTabNavigation();
        this.setupEventListeners();
        this.loadDashboardData();
        this.loadCapsule();
        this.initTheme();
        
        if (this.isAdmin()) {
            this.loadAdminData();
        }
    }

    setupAuth() {
        const payload = JSON.parse(atob(this.token.split('.')[1]));
        document.getElementById('user-email').textContent = payload.email;
        
        if (this.isAdmin()) {
            document.querySelectorAll('.admin-only').forEach(el => el.style.display = 'block');
        }
    }
    
    isAdmin() {
        return this.role === 'admin' || this.role === 'manager';
    }

    setupTabNavigation() {
        const navLinks = document.querySelectorAll('.nav-link');
        const tabContents = document.querySelectorAll('.tab-content');

        navLinks.forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const targetTab = link.getAttribute('data-tab');

                navLinks.forEach(nl => nl.classList.remove('active'));
                tabContents.forEach(tc => tc.classList.remove('active'));

                link.classList.add('active');
                document.getElementById(targetTab).classList.add('active');
            });
        });
    }

    setupEventListeners() {
        document.getElementById('refresh-capsule').addEventListener('click', () => this.loadCapsule());
        document.getElementById('run-pipeline').addEventListener('click', () => this.runPipeline());
        document.getElementById('ingest-news').addEventListener('click', () => this.ingestNews());
    }

    async apiCall(endpoint, method = 'GET', body = null) {
        try {
            const options = {
                method,
                headers: {
                    'Content-Type': 'application/json',
                },
            };
            
            if (this.token) {
                options.headers['Authorization'] = `Bearer ${this.token}`;
            }

            if (body) {
                options.body = JSON.stringify(body);
            }

            const response = await fetch(`${this.baseURL}${endpoint}`, options);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error('API call failed:', error);
            this.showNotification('API call failed: ' + error.message, 'error');
            throw error;
        }
    }

    async loadDashboardData() {
        try {
            const capsule = await this.apiCall('/capsule/daily');
            document.getElementById('news-count').textContent = capsule.items?.length || 0;
            document.getElementById('capsule-date').textContent = capsule.date || 'Today';
            
            if (this.isAdmin()) {
                const users = await this.apiCall('/admin/users');
                const subscriberCount = users.filter(u => u.subscribed).length;
                document.getElementById('subscriber-count').textContent = subscriberCount;
            } else {
                document.getElementById('subscriber-count').textContent = 'N/A';
            }
        } catch (error) {
            console.error('Failed to load dashboard data:', error);
        }
    }

    async loadCapsule() {
        const container = document.getElementById('capsule-content');
        container.innerHTML = '<div class="loading">Loading capsule...</div>';

        try {
            const capsule = await this.apiCall('/capsule/daily');
            this.renderCapsule(capsule);
        } catch (error) {
            container.innerHTML = '<div class="error">Failed to load capsule. Please try again.</div>';
        }
    }

    renderCapsule(capsule) {
        const container = document.getElementById('capsule-content');
        
        if (!capsule.items || capsule.items.length === 0) {
            container.innerHTML = '<div class="no-data">No news items available for today.</div>';
            return;
        }

        const html = `
            <div class="capsule-header">
                <h3>Daily UPSC Capsule - ${capsule.date}</h3>
                <p>${capsule.items.length} news items with syllabus mapping</p>
            </div>
            <div class="news-items">
                ${capsule.items.map(item => this.renderNewsItem(item)).join('')}
            </div>
        `;

        container.innerHTML = html;
    }

    renderNewsItem(item) {
        const topics = item.topics || [];
        const pyqs = item.pyqs || [];

        return `
            <div class="news-item">
                <div class="news-title">
                    <a href="${item.url}" target="_blank">${item.title}</a>
                </div>
                <div class="news-summary">
                    ${item.summary || 'No summary available'}
                </div>
                ${topics.length > 0 ? `
                    <div class="topics-section">
                        <h4><i class="fas fa-tags"></i> Syllabus Mapping:</h4>
                        <div class="topics-list">
                            ${topics.map(topic => `
                                <span class="topic-tag">
                                    ${topic.paper}: ${topic.topic} (${topic.score.toFixed(2)})
                                </span>
                            `).join('')}
                        </div>
                    </div>
                ` : ''}
                ${pyqs.length > 0 ? `
                    <div class="pyqs-section">
                        <h4><i class="fas fa-question-circle"></i> Related PYQs:</h4>
                        <ul class="pyqs-list">
                            ${pyqs.slice(0, 3).map(pyq => `
                                <li>${pyq.question} (${pyq.year})</li>
                            `).join('')}
                        </ul>
                    </div>
                ` : ''}
                <div class="news-source">
                    <small><i class="fas fa-link"></i> Source: <a href="${item.url}" target="_blank">${item.url}</a></small>
                </div>
            </div>
        `;
    }

    async runPipeline() {
        const button = document.getElementById('run-pipeline');
        const logsContainer = document.getElementById('pipeline-logs');
        
        button.disabled = true;
        button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Running...';
        logsContainer.innerHTML = 'Starting pipeline...\n';

        try {
            logsContainer.innerHTML += 'Running full pipeline...\n';
            const result = await this.apiCall('/pipeline/run', 'POST');
            logsContainer.innerHTML += `✓ Pipeline completed!\n`;
            logsContainer.innerHTML += `✓ News items: ${result.news_items}\n`;
            logsContainer.innerHTML += `✓ Capsule items: ${result.capsule_items}\n`;
            logsContainer.innerHTML += `✓ Emails sent: ${result.emails_sent || 0}\n`;

            logsContainer.innerHTML += '\n✓ Pipeline completed successfully!\n';
            this.showNotification('Pipeline completed successfully!', 'success');
            this.loadDashboardData();
            this.loadCapsule();
        } catch (error) {
            logsContainer.innerHTML += `\n✗ Pipeline failed: ${error.message}\n`;
            this.showNotification('Pipeline failed', 'error');
        } finally {
            button.disabled = false;
            button.innerHTML = '<i class="fas fa-play"></i> Run Full Pipeline';
        }
    }

    async ingestNews() {
        const button = document.getElementById('ingest-news');
        button.disabled = true;
        button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Ingesting...';

        try {
            await this.apiCall('/ingest/news', 'POST');
            this.showNotification('News ingestion completed!', 'success');
            this.loadDashboardData();
        } catch (error) {
            this.showNotification('News ingestion failed', 'error');
        } finally {
            button.disabled = false;
            button.innerHTML = '<i class="fas fa-download"></i> Ingest News Only';
        }
    }

    async loadAdminData() {
        await this.loadPendingRequests();
        await this.loadUsers();
    }
    
    async loadPendingRequests() {
        try {
            const requests = await this.apiCall('/admin/subscription-requests');
            this.renderPendingRequests(requests);
        } catch (error) {
            document.getElementById('pending-requests').innerHTML = '<div class="error">Failed to load requests</div>';
        }
    }
    
    renderPendingRequests(requests) {
        const container = document.getElementById('pending-requests');
        
        if (requests.length === 0) {
            container.innerHTML = '<div class="no-data">No pending requests</div>';
            return;
        }
        
        const html = requests.map(req => `
            <div class="request-item">
                <div>
                    <strong>${req.full_name}</strong><br>
                    <small>${req.email}</small><br>
                    <em>${req.reason}</em>
                </div>
                <div>
                    <button class="btn btn-success btn-sm" onclick="app.approveRequest(${req.id})">
                        <i class="fas fa-check"></i> Approve
                    </button>
                    <button class="btn btn-danger btn-sm" onclick="app.rejectRequest(${req.id})">
                        <i class="fas fa-times"></i> Reject
                    </button>
                </div>
            </div>
        `).join('');
        
        container.innerHTML = html;
    }
    
    async approveRequest(requestId) {
        try {
            await this.apiCall(`/admin/approve-subscription/${requestId}`, 'POST');
            this.showNotification('Request approved', 'success');
            this.loadAdminData();
        } catch (error) {
            this.showNotification('Failed to approve request', 'error');
        }
    }
    
    async rejectRequest(requestId) {
        try {
            await this.apiCall(`/admin/reject-subscription/${requestId}`, 'POST');
            this.showNotification('Request rejected', 'success');
            this.loadAdminData();
        } catch (error) {
            this.showNotification('Failed to reject request', 'error');
        }
    }
    
    async loadUsers() {
        try {
            const users = await this.apiCall('/admin/users');
            this.renderUsers(users);
        } catch (error) {
            document.getElementById('users-list').innerHTML = '<div class="error">Failed to load users</div>';
        }
    }
    
    renderUsers(users) {
        const container = document.getElementById('users-list');
        
        const html = users.map(user => `
            <div class="user-item">
                <div>
                    <strong>${user.full_name}</strong> (${user.role})<br>
                    <small>${user.email}</small><br>
                    <span class="status ${user.is_active ? 'active' : 'inactive'}">
                        ${user.is_active ? 'Active' : 'Inactive'}
                    </span>
                    <span class="subscription ${user.subscribed ? 'subscribed' : 'unsubscribed'}">
                        ${user.subscribed ? 'Subscribed' : 'Not Subscribed'}
                    </span>
                </div>
                <div>
                    <button class="btn btn-secondary btn-sm" onclick="app.toggleSubscription(${user.id})">
                        <i class="fas fa-envelope"></i> Toggle Sub
                    </button>
                    ${user.role === 'user' ? `
                        <button class="btn btn-danger btn-sm" onclick="app.deactivateUser(${user.id})">
                            <i class="fas fa-ban"></i> Deactivate
                        </button>
                    ` : ''}
                </div>
            </div>
        `).join('');
        
        container.innerHTML = html;
    }
    
    async toggleSubscription(userId) {
        try {
            await this.apiCall(`/admin/toggle-subscription/${userId}`, 'POST');
            this.showNotification('Subscription toggled', 'success');
            this.loadUsers();
        } catch (error) {
            this.showNotification('Failed to toggle subscription', 'error');
        }
    }
    
    async deactivateUser(userId) {
        if (!confirm('Are you sure you want to deactivate this user?')) return;
        
        try {
            await this.apiCall(`/admin/deactivate-user/${userId}`, 'POST');
            this.showNotification('User deactivated', 'success');
            this.loadUsers();
        } catch (error) {
            this.showNotification('Failed to deactivate user', 'error');
        }
    }

    initTheme() {
        const savedTheme = localStorage.getItem('theme') || 'light';
        document.documentElement.setAttribute('data-theme', savedTheme);
        this.updateThemeIcon(savedTheme);
    }

    updateThemeIcon(theme) {
        const icon = document.getElementById('theme-icon');
        if (icon) {
            icon.className = theme === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
        }
    }

    showNotification(message, type = 'success') {
        const notification = document.getElementById('notification');
        notification.textContent = message;
        notification.className = `notification ${type} show`;

        setTimeout(() => {
            notification.classList.remove('show');
        }, 3000);
    }
}

function toggleTheme() {
    const currentTheme = document.documentElement.getAttribute('data-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    
    document.documentElement.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
    window.app.updateThemeIcon(newTheme);
}

function logout() {
    localStorage.removeItem('token');
    localStorage.removeItem('role');
    window.location.href = '/login';
}

document.addEventListener('DOMContentLoaded', () => {
    window.app = new CivicBriefsApp();
});