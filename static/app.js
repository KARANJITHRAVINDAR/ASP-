// static/app.js
document.addEventListener('DOMContentLoaded', () => {
    // --- State & Configuration ---
    let charts = {};

    // --- API Helper ---
    const api = {
        get: async (endpoint) => {
            const response = await fetch(endpoint);
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            return response.json();
        },
        post: async (endpoint, data) => {
            const response = await fetch(endpoint, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data),
            });
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            return response.json();
        }
    };

    // --- UI Update Functions ---
    const UI = {
        updateHeaderStats: (stats) => {
            document.getElementById('totalPatients').textContent = stats.totalPatients || '0';
            document.getElementById('avgRisk').textContent = `${stats.avgRisk || 0}%`;
            document.getElementById('highRiskCount').textContent = stats.highRiskCount || '0';
        },
        renderDashboard: (patients) => {
            const riskCounts = { Low: 0, Moderate: 0, High: 0 };
            patients.forEach(p => { riskCounts[p.riskLevel] = (riskCounts[p.riskLevel] || 0) + 1; });
            
            document.getElementById('lowRiskPatients').textContent = riskCounts.Low;
            document.getElementById('moderateRiskPatients').textContent = riskCounts.Moderate;
            document.getElementById('highRiskPatients').textContent = riskCounts.High;

            UI.renderRiskDistributionChart(riskCounts);
            UI.renderRecentPatients(patients.slice(0, 5));
        },
        renderRiskDistributionChart: (riskCounts) => {
            const ctx = document.getElementById('riskChart')?.getContext('2d');
            if (!ctx) return;
            if (charts.riskChart) charts.riskChart.destroy();
            charts.riskChart = new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: ['Low Risk', 'Moderate Risk', 'High Risk'],
                    datasets: [{
                        data: [riskCounts.Low, riskCounts.Moderate, riskCounts.High],
                        backgroundColor: ['#1FB8CD', '#FFC185', '#B4413C']
                    }]
                },
                options: { responsive: true, maintainAspectRatio: false }
            });
        },
        renderRecentPatients: (recentPatients) => {
            const container = document.getElementById('recentPatientsList');
            if (!container) return;
            container.innerHTML = recentPatients.map(p => `
                <div class="patient-item" onclick="window.showPatientModal(${p.id})">
                    <div class="patient-header">
                        <div class="patient-name">${p.patientName}</div>
                        <div class="risk-badge ${p.riskLevel.toLowerCase()}">${p.riskLevel} Risk</div>
                    </div>
                    <div class="patient-info">
                        <div>LOS: ${p.predicted_los} days</div>
                        <div>Risk Score: ${p.riskScore}%</div>
                    </div>
                </div>
            `).join('');
        },
        renderPatientsGrid: (patients) => {
            const container = document.getElementById('patientsGrid');
            if (!container) return;
            container.innerHTML = patients.map(p => `
                <div class="patient-card" onclick="window.showPatientModal(${p.id})">
                    <div class="patient-card-header">
                        <div>
                            <div class="patient-card-name">${p.patientName}</div>
                            <div class="patient-card-meta">${p.patientId} • ${p.age}y</div>
                        </div>
                        <div class="risk-badge ${p.riskLevel.toLowerCase()}">${p.riskLevel}</div>
                    </div>
                    <div class="patient-card-details">
                         <div class="detail-item"><div class="detail-label">Predicted LOS</div><div class="detail-value">${p.predicted_los} days</div></div>
                         <div class="detail-item"><div class="detail-label">Risk Score</div><div class="detail-value">${p.riskScore}%</div></div>
                    </div>
                </div>
            `).join('');
        },
        showToast: (message, isError = false) => {
            const toast = document.getElementById('toast');
            toast.textContent = message;
            toast.style.backgroundColor = isError ? '#ef4444' : '#10b981';
            toast.style.display = 'block';
            setTimeout(() => { toast.style.display = 'none'; }, 3000);
        },
        showModal: (patient) => {
            document.getElementById('modalPatientName').textContent = patient.patientName;
            const details = document.getElementById('modalPatientDetails');
            const comorbidities = [
                { label: 'Sepsis', key: 'hasSepsis' }, { label: 'Delirium', key: 'hasDelirium' },
                { label: 'Malignancy', key: 'hasMalignancy' }, { label: 'Diabetes', key: 'hasDiabetes' },
                { label: 'CHF', key: 'hasCHF' }, { label: 'CKD', key: 'hasCKD' },
                { label: 'COPD', key: 'hasCOPD' }, { label: 'Stroke', key: 'hasStroke' },
                { label: 'Liver Disease', key: 'hasLiverDisease' }
            ].filter(c => patient[c.key]).map(c => c.label).join(', ') || 'None';

            details.innerHTML = `
                <p><strong>Patient ID:</strong> ${patient.patientId}</p>
                <p><strong>Admission Date:</strong> ${new Date(patient.admissionDate).toLocaleDateString()}</p>
                <p><strong>Predicted Length of Stay:</strong> ${patient.predicted_los} days</p>
                <p><strong>Complication Risk:</strong> ${patient.riskLevel} (${patient.riskScore}%)</p>
                <hr class="my-4">
                <p><strong>Age:</strong> ${patient.age}</p>
                <p><strong>Admission Type:</strong> ${patient.admissionType === 1 ? 'Emergency' : patient.admissionType === 2 ? 'Elective' : 'Urgent'}</p>
                <p><strong>Surgery Method:</strong> ${patient.surgeryMethod === 0 ? 'Non-surgical' : patient.surgeryMethod === 1 ? 'Minimally Invasive' : 'Open'}</p>
                <p><strong>Albumin:</strong> ${patient.albumin || 'N/A'}</p>
                <p><strong>Hemoglobin:</strong> ${patient.hemoglobin || 'N/A'}</p>
                <p><strong>Comorbidities:</strong> ${comorbidities}</p>
            `;
            document.getElementById('patientModal').classList.remove('hidden');
        }
    };

    // --- Event Handlers & Initialization ---
    const initNav = () => {
        document.querySelectorAll('.nav-tab').forEach(tab => {
            tab.addEventListener('click', (e) => {
                const tabId = e.currentTarget.dataset.tab;
                document.querySelectorAll('.nav-tab').forEach(t => t.classList.remove('active'));
                document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
                e.currentTarget.classList.add('active');
                document.getElementById(tabId).classList.add('active');
            });
        });
    };

    const initForm = () => {
        const form = document.getElementById('patientForm');
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            const formData = new FormData(form);
            const data = {};
            formData.forEach((value, key) => { data[key] = value; });
            
            // Convert checkbox values to boolean
            ['hasSepsis', 'hasDelirium', 'hasMalignancy', 'hasDiabetes', 'hasCHF', 'hasCKD', 'hasCOPD', 'hasStroke', 'hasLiverDisease'].forEach(key => {
                data[key] = form.querySelector(`[name="${key}"]`).checked;
            });
            
            // Convert numbers
            ['age', 'priorAdmissions', 'admissionType', 'surgeryMethod', 'albumin', 'hemoglobin'].forEach(key => {
                 data[key] = parseFloat(data[key]) || 0;
            });

            try {
                await api.post('/api/assessment', data);
                UI.showToast('Assessment stored successfully.');
                form.reset();
                fetchAllData(); // Refresh all data
                document.querySelector('[data-tab="dashboard"]').click(); // Switch to dashboard
            } catch (error) {
                UI.showToast('Failed to store assessment.', true);
                console.error(error);
            }
        });
    };
    
    const initFeedbackForm = () => {
        const form = document.getElementById('feedbackForm');
        if (!form) return;
    
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            const patientId = document.getElementById('feedbackPatientId').value;
            const feedbackText = document.getElementById('feedbackText').value;
    
            if (!patientId || !feedbackText) {
                UI.showToast('Patient ID and feedback text are required.', true);
                return;
            }
    
            try {
                const result = await api.post('/submit_feedback', {
                    patient_id: patientId,
                    feedback_text: feedbackText
                });
                UI.showToast(`Feedback submitted for category: ${result.analysis.category}.`);
                form.reset();
            } catch (error) {
                UI.showToast('Failed to submit feedback.', true);
                console.error(error);
            }
        });
    };

    const fetchAllData = async () => {
        try {
            const [stats, patients] = await Promise.all([
                api.get('/api/dashboard-stats'),
                api.get('/api/patients')
            ]);
            
            window.allPatients = patients; // Store globally for modal access
            UI.updateHeaderStats(stats);
            UI.renderDashboard(patients);
            UI.renderPatientsGrid(patients);
        } catch (error) {
            UI.showToast('Failed to load initial data. Please check the backend.', true);
            console.error(error);
        }
    };

    // --- Global Functions ---
    window.showPatientModal = (patientId) => {
        const patient = window.allPatients.find(p => p.id === patientId);
        if (patient) UI.showModal(patient);
    };
    
    window.closePatientModal = () => {
        document.getElementById('patientModal').classList.add('hidden');
    };
    
    document.addEventListener('click', (e) => {
       if (e.target === document.getElementById('patientModal')) {
           window.closePatientModal();
       }
    });

    // --- App Start ---
    initNav();
    initForm();
    initFeedbackForm();
    fetchAllData();
});