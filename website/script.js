document.addEventListener('DOMContentLoaded', () => {
    
    // 1. Initialize Icons
    lucide.createIcons();

    // 2. Navigation Logic
    const navItems = document.querySelectorAll('.nav-item[data-tab]');
    const tabPanes = document.querySelectorAll('.tab-pane');
    const titleElement = document.getElementById('current-tab-title');
    const descElement = document.getElementById('current-tab-desc');

    // Updated Descriptions based on your screenshots
    const descriptions = {
        'home': ['Home', 'Accelerating the transition to a circular economy with real-time AI analysis.'],
        'heatmaps': ['Heatmaps', 'Accelerating the transition to a circular economy with real-time AI analysis.'],
        'realtime': ['Real-time', 'Accelerating the transition to a circular economy with real-time AI analysis.'],
        'mission': ['Mission', 'Accelerating the transition to a circular economy with real-time AI analysis.']
    };

    navItems.forEach(item => {
        item.addEventListener('click', () => {
            // Deactivate all
            navItems.forEach(nav => nav.classList.remove('active'));
            tabPanes.forEach(pane => pane.style.display = 'none');

            // Activate clicked
            item.classList.add('active');
            const tabId = item.getAttribute('data-tab');
            const targetPane = document.getElementById(tabId);
            
            if(targetPane) {
                targetPane.style.display = 'block';
                // Trigger Map Resize (Vital for Leaflet inside hidden tabs)
                if(tabId === 'heatmaps' && typeof map !== 'undefined') {
                    setTimeout(() => { map.invalidateSize(); }, 200);
                }
            }

            // Update Header Text
            if(descriptions[tabId]) {
                titleElement.textContent = descriptions[tabId][0];
                descElement.textContent = descriptions[tabId][1];
            }
        });
    });

// 3. MAP LOGIC (City-Wide + High Density Campus)
const mapElement = document.getElementById('map');
let map;

if (mapElement) {
    // Center on Providence
    map = L.map('map').setView([41.8240, -71.4128], 12); 

    L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
        attribution: '&copy; CARTO', 
        maxZoom: 20
    }).addTo(map);

    const heatData = [
        // --- CAMPUS CORE (BROWN & RISD) - High Density ---
        [41.8268, -71.4025, 1.0], // Main Green (Center)
        [41.8262, -71.4015, 0.9], // Sciences Library (SciLi)
        [41.8250, -71.4030, 0.8], // Rockefeller Library
        [41.8280, -71.4005, 0.8], // Barus & Holley (Engineering)
        [41.8255, -71.4045, 0.7], // Keeney Quad
        [41.8245, -71.4015, 0.7], // Wriston Quad
        [41.8300, -71.4000, 0.8], // Pembroke Campus
        [41.8290, -71.4030, 0.6], // Faunce House
        [41.8315, -71.4010, 0.7], // Life Sciences Building
        [41.8320, -71.3980, 0.6], // Erickson Athletic Complex
        [41.8235, -71.4060, 0.8], // RISD Auditorium / Museum Area
        [41.8250, -71.4080, 0.7], // RISD Design Center

        // --- DOWNTOWN CORE ---
        [41.8236, -71.4128, 1.0], // Kennedy Plaza (Full)
        [41.8295, -71.4135, 0.9], // Providence Place Mall
        [41.8200, -71.4130, 0.7], // JWU Downcity
        [41.8170, -71.4100, 0.8], // Jewelry District

        // --- EAST SIDE ---
        [41.8270, -71.4005, 0.9], // Thayer Street (Very Busy)
        [41.8380, -71.3960, 0.7], // Hope Street Shops
        [41.8155, -71.3960, 0.6], // Wickenden Street
        [41.8120, -71.3910, 0.5], // India Point Park
        [41.8300, -71.3880, 0.6], // Wayland Square

        // --- WEST SIDE ---
        [41.8230, -71.4250, 0.95], // Federal Hill (Atwells)
        [41.8170, -71.4450, 0.85], // Olneyville Square
        [41.8220, -71.4350, 0.6],  // Broadway
        [41.8100, -71.4500, 0.5],  // Silver Lake

        // --- NORTH END ---
        [41.8420, -71.4380, 0.8],  // Providence College
        [41.8500, -71.4200, 0.6],  // Charles St
        [41.8600, -71.4100, 0.5],  // North Main St

        // --- SOUTH PROVIDENCE ---
        [41.8050, -71.4300, 0.7],  // Cranston St Armory
        [41.7980, -71.4150, 0.8],  // Broad Street
        [41.7850, -71.4150, 0.6],  // Roger Williams Park Zoo
        [41.7900, -71.4050, 0.7]   // RI Hospital District
    ];

    L.heatLayer(heatData, {
        radius: 25, 
        blur: 15,
        minOpacity: 0.4,
        gradient: { 
            0.4: '#a7f3d0',  // Light Green
            0.6: '#34d399',  // Medium Green
            0.8: '#059669',  // Dark Green
            1.0: '#064e3b'   // Forest Green
        }
    }).addTo(map);
}

    // 4. REAL-TIME DASHBOARD LOGIC
    let totalItems = 4625;
    const counterElement = document.getElementById('live-counter');
    const impactTrees = document.getElementById('impact-trees');
    const impactEnergy = document.getElementById('impact-energy');
    const impactCO2 = document.getElementById('impact-co2');

    if(counterElement) {
        setInterval(() => {
            const increment = Math.random() > 0.5 ? Math.floor(Math.random() * 3) + 1 : 0;
            totalItems += increment;
            
            counterElement.innerText = totalItems.toLocaleString();
            if(impactTrees) impactTrees.innerText = (totalItems * 0.00067).toFixed(2);
            if(impactEnergy) impactEnergy.innerText = Math.floor(totalItems * 0.18).toLocaleString();
            if(impactCO2) impactCO2.innerText = (totalItems * 0.12).toFixed(1) + 'kg';
        }, 3000);
    }

    // 5. CHARTS
    const ctxComp = document.getElementById('compositionChart');
    if (ctxComp) {
        new Chart(ctxComp.getContext('2d'), {
            type: 'doughnut',
            data: {
                labels: ['Recyclables', 'General Waste'], 
                datasets: [{
                    data: [75, 25], 
                    backgroundColor: ['#0a2218', '#94a3b8'], 
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false, 
                plugins: { legend: { position: 'right' } },
                cutout: '75%', 
            }
        });
    }

    const ctxWeekly = document.getElementById('weeklyChart');
    if (ctxWeekly) {
        new Chart(ctxWeekly.getContext('2d'), {
            type: 'bar',
            data: {
                labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
                datasets: [{
                    data: [2500, 5600, 5400, 2100, 5300, 5700, 0], 
                    backgroundColor: '#50cf8f', 
                    borderRadius: 4,
                    barPercentage: 0.7
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    y: { beginAtZero: true, grid: { color: '#f1f5f9' } },
                    x: { grid: { display: false } }
                }
            }
        });
    }

    // --- LINK HOME BUTTON TO REAL-TIME TAB ---
    const viewNetworkBtn = document.getElementById('btn-view-network');
    
    if(viewNetworkBtn) {
        viewNetworkBtn.addEventListener('click', () => {
            // Find the sidebar navigation item for "realtime"
            const realtimeNav = document.querySelector('.nav-item[data-tab="realtime"]');
            
            // Simulate a click on it to trigger the tab switch
            if(realtimeNav) {
                realtimeNav.click();
            }
        });
    }
    
    // 6. LIVE STATISTICS UPDATE
    function updateLiveStats() {
        fetch('http://172.20.10.4:5000/stats')
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    console.error('Stats error:', data.error);
                    return;
                }
                
                // Update counters with animation
                animateValue('recyclable-count', parseInt(document.getElementById('recyclable-count').textContent) || 0, data.recyclable, 500);
                animateValue('non-recyclable-count', parseInt(document.getElementById('non-recyclable-count').textContent) || 0, data.non_recyclable, 500);
                animateValue('total-count', parseInt(document.getElementById('total-count').textContent) || 0, data.total, 500);
            })
            .catch(error => {
                console.error('Failed to fetch stats:', error);
            });
    }
    
    // Animate number changes
    function animateValue(id, start, end, duration) {
        const element = document.getElementById(id);
        if (!element || start === end) return;
        
        const range = end - start;
        const increment = range / (duration / 16); // 60fps
        let current = start;
        
        const timer = setInterval(() => {
            current += increment;
            if ((increment > 0 && current >= end) || (increment < 0 && current <= end)) {
                element.textContent = end;
                clearInterval(timer);
            } else {
                element.textContent = Math.round(current);
            }
        }, 16);
    }
    
    // Update stats every 2 seconds
    updateLiveStats(); // Initial load
    setInterval(updateLiveStats, 2000);
    
});
