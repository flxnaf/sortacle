// 1. Initialize Icons
lucide.createIcons({
  attrs: { 'stroke-width': 2.5 }
});

// --- 2. OVERVIEW CHART (Sustainability Trajectory) ---
const chartCanvas = document.getElementById('trajectoryChart');
if (chartCanvas) {
  const ctx = chartCanvas.getContext('2d');
  const gradient = ctx.createLinearGradient(0, 0, 0, 400);
  gradient.addColorStop(0, 'rgba(27, 67, 50, 0.5)'); 
  gradient.addColorStop(1, 'rgba(27, 67, 50, 0.0)');

  new Chart(ctx, {
      type: 'line',
      data: {
          labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
          datasets: [{
              label: 'Plastic Diverted (Tons)',
              data: [12, 19, 15, 25, 22, 30, 28],
              borderColor: '#1b4332',
              backgroundColor: gradient,
              borderWidth: 2,
              tension: 0.4,
              fill: true,
              pointRadius: 4,
              pointBackgroundColor: '#fff',
              pointBorderColor: '#1b4332'
          }]
      },
      options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: { legend: { display: false } },
          scales: {
              y: { beginAtZero: true, grid: { color: 'rgba(0,0,0,0.05)' } },
              x: { grid: { display: false } }
          }
      }
  });
}

// ==========================================
    // 2. LIVE NETWORK COUNTER & IMPACT CALCULATOR
    // ==========================================
    const counterElement = document.getElementById('live-counter');
    const treeElement = document.getElementById('impact-trees');
    const energyElement = document.getElementById('impact-energy');
    const co2Element = document.getElementById('impact-co2');

    // Start with a higher number so the "Trees" stat isn't zero
    let totalItems = 3420; 

    function updateStats() {
        // 1. Update the Main Counter
        if (counterElement) {
            counterElement.innerText = totalItems.toLocaleString();
            
            // Pop animation
            counterElement.style.transform = "scale(1.05)";
            setTimeout(() => counterElement.style.transform = "scale(1)", 100);
        }

        // 2. Calculate Real-Time Impact
        // Coefficients based on average mixed recycling data
        const trees = (totalItems * 0.00067); // approx 1 tree per 1500 items
        const energy = (totalItems * 0.18);   // 0.18 kWh per item
        const co2 = (totalItems * 0.12);      // 0.12 kg CO2 per item

        // 3. Update the Impact DOM Elements
        if (treeElement) treeElement.innerText = trees.toFixed(2); // 2.45 Trees
        if (energyElement) energyElement.innerText = Math.floor(energy).toLocaleString(); // 615 kWh
        if (co2Element) co2Element.innerText = co2.toFixed(1); // 410.4 kg
    }

    if (counterElement) {
        // Run once on load to set initial numbers
        updateStats();

        // Update loop: Simulate items coming in
        setInterval(() => {
            // Randomly add 1-3 items
            const increment = Math.floor(Math.random() * 3) + 1;
            totalItems += increment;
            
            updateStats(); // Recalculate everything
            
        }, 2000); // Every 2 seconds
    }


// --- 4. MAP CONFIGURATION (Bin Location Tracker) ---
let mapInitialized = false;
let map;

// This function simulates getting data from your Raspberry Pi
// LATER: You will replace this with a real fetch() call to your Pi's IP
async function fetchBinLocation() {
    // --- SIMULATION MODE (Works right now) ---
    // Simulating a location (Providence, RI - Brown University area)
    return { lat: 41.8268, lng: -71.4025, intensity: 1.0 };

    /* --- REAL HARDWARE MODE (Uncomment this later) ---
    try {
        // Replace with your Pi's actual IP address
        const response = await fetch('http://192.168.1.X:8080/api/location'); 
        const data = await response.json();
        return { lat: data.lat, lng: data.lng, intensity: data.fillLevel };
    } catch (error) {
        console.error("Could not connect to Bin:", error);
        // Fallback to default location if Pi is offline
        return { lat: 41.8268, lng: -71.4025, intensity: 0.5 };
    }
    */
}

async function initMap() {
    if (mapInitialized) return;

    // 1. Get the location (Simulated for now)
    const binData = await fetchBinLocation();

    // 2. Initialize Map centered on the Bin
    map = L.map('map').setView([binData.lat, binData.lng], 15);

    L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
        attribution: '&copy; OpenStreetMap &copy; CARTO',
        subdomains: 'abcd',
        maxZoom: 20
    }).addTo(map);

    // 3. Add a Pulse Marker (The Bin Itself)
    // This creates a visual "Ping" showing exactly where your prototype is
    const binIcon = L.divIcon({
        className: 'bin-marker',
        html: `<div style="
            background: #1b4332; 
            width: 16px; 
            height: 16px; 
            border-radius: 50%; 
            border: 3px solid #ffffff; 
            box-shadow: 0 0 0 4px rgba(27, 67, 50, 0.3);">
        </div>`,
        iconSize: [20, 20],
        iconAnchor: [10, 10]
    });

    L.marker([binData.lat, binData.lng], { icon: binIcon }).addTo(map)
        .bindPopup(`
            <div style="font-family: 'Plus Jakarta Sans', sans-serif;">
                <strong>Smart Bin #01</strong><br>
                Status: Online<br>
                Location: Providence, RI
            </div>
        `);

    // 4. Add Heat/Intensity Layer
    // Instead of random dots, we show a "Heat Zone" around your bin
    // effectively showing the "Impact Radius" of your device.
    const heatData = [
        [binData.lat, binData.lng, 1.0], // The Bin (Hot Center)
        [binData.lat + 0.001, binData.lng + 0.001, 0.5], // Nearby Impact
        [binData.lat - 0.001, binData.lng - 0.001, 0.5],
        [binData.lat + 0.001, binData.lng - 0.001, 0.5],
        [binData.lat - 0.001, binData.lng + 0.001, 0.5]
    ];

    L.heatLayer(heatData, {
        radius: 35,
        blur: 20,
        gradient: { 0.4: '#74c69d', 0.6: '#2d6a4f', 1.0: '#1b4332' }
    }).addTo(map);

    mapInitialized = true;
}

// --- 5. TAB LOGIC ---
const navItems = document.querySelectorAll('.nav-item[data-tab]');
const tabPanes = document.querySelectorAll('.tab-pane');
const titleElement = document.getElementById('current-tab-title');

navItems.forEach(item => {
  item.addEventListener('click', () => {
      const tabId = item.getAttribute('data-tab');
      if (!tabId) return;

      navItems.forEach(nav => nav.classList.remove('active'));
      item.classList.add('active');

      tabPanes.forEach(pane => {
          pane.style.opacity = '0';
          pane.style.transform = 'translateY(10px)';
          
          setTimeout(() => {
              pane.classList.remove('active');
              if (pane.id === tabId) {
                  pane.classList.add('active');
                  
                  // Map Resize Hack
                  if (tabId === 'heatmaps') {
                      setTimeout(() => { initMap(); map.invalidateSize(); }, 100);
                  }

                  setTimeout(() => {
                      pane.style.opacity = '1';
                      pane.style.transform = 'translateY(0)';
                  }, 50);
              }
          }, 300);
      });

      const tabName = item.querySelector('span').textContent;
      titleElement.textContent = tabName === 'Overview' ? 'Project Overview' : tabName;
  });
});

// ==========================================
    // 2B. COMPOSITION CHART 
    // ==========================================
    const ctxComp = document.getElementById('compositionChart');
    let compositionChart; 

    // Debugging: Check if element exists
    if (!ctxComp) {
        console.error("ERROR: Could not find element with id 'compositionChart'");
    } else {
        console.log("SUCCESS: Found chart element. Drawing graph...");
        
        compositionChart = new Chart(ctxComp.getContext('2d'), {
            type: 'doughnut',
            data: {
                labels: ['Recyclables', 'General Waste'], 
                datasets: [{
                    data: [2460, 960], // Start with dummy data so it shows immediately
                    backgroundColor: [
                        '#1b4332', // Dark Green
                        '#94a3b8'  // Grey
                    ],
                    borderWidth: 0,
                    hoverOffset: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false, // Vital for fitting in the box
                plugins: {
                    legend: {
                        position: 'right',
                        labels: {
                            font: { family: "sans-serif", size: 11 },
                            boxWidth: 10,
                            padding: 15
                        }
                    }
                },
                cutout: '70%', 
            }
        });
    }

    // Helper: Function to update the graph live
    function updateChart() {
        if (compositionChart) {
            // Using the global countRecycle/countWaste variables
            compositionChart.data.datasets[0].data = [countRecycle, countWaste];
            compositionChart.update();
        }
    }

// ==========================================
    // 3B. INTERACTIVE WEEKLY HISTORY CHART (Future-Proof)
    // ==========================================
    const weeklyCanvas = document.getElementById('weeklyChart');
    
    if (weeklyCanvas) {
        // 1. Determine "Today" (End of day)
        const now = new Date(); 
        now.setHours(23, 59, 59, 999); 

        function getMonday(d) {
            d = new Date(d);
            const day = d.getDay(),
                diff = d.getDate() - day + (day === 0 ? -6 : 1); 
            return new Date(d.setDate(diff));
        }

        let currentStartDate = getMonday(now);

        const ctxWeekly = weeklyCanvas.getContext('2d');
        const historyChart = new Chart(ctxWeekly, {
            type: 'bar',
            data: {
                labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
                datasets: [{
                    label: 'Items Sorted',
                    data: [0,0,0,0,0,0,0], 
                    backgroundColor: '#74c69d',
                    borderRadius: 4,
                    hoverBackgroundColor: '#1b4332'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    y: { beginAtZero: true },
                    x: { grid: { display: false } }
                }
            }
        });

        // --- CORE LOGIC ---
        function updateWeekView() {
            // 1. Calculate End Date
            const endDate = new Date(currentStartDate);
            endDate.setDate(currentStartDate.getDate() + 6);

            // 2. Update Label
            const options = { month: 'short', day: 'numeric' };
            const label = `${currentStartDate.toLocaleDateString('en-US', options)} - ${endDate.toLocaleDateString('en-US', options)}`;
            document.getElementById('dateRangeLabel').innerText = label;

            // 3. GENERATE DATA
            const seed = currentStartDate.getTime(); 
            const finalData = [];
            
            for (let i = 0; i < 7; i++) {
                let barDate = new Date(currentStartDate);
                barDate.setDate(currentStartDate.getDate() + i);

                // If date is in future, push 0. If past, push fake data.
                if (barDate > now) {
                    finalData.push(0); 
                } else {
                    // Simple math to make random-looking but consistent graph
                    const val = Math.floor((Math.abs(Math.sin(seed + i)) * 4000) + 2000);
                    finalData.push(val);
                }
            }

            historyChart.data.datasets[0].data = finalData;
            historyChart.update();
        }

        // --- EVENT LISTENERS (Unlimited Navigation) ---
        
        document.getElementById('prevWeek').addEventListener('click', () => {
            currentStartDate.setDate(currentStartDate.getDate() - 7);
            updateWeekView();
        });

        document.getElementById('nextWeek').addEventListener('click', () => {
            currentStartDate.setDate(currentStartDate.getDate() + 7);
            updateWeekView();
        });

        // Month Picker - No alerts, just jumps to the date
        const monthPicker = document.getElementById('monthPicker');
        monthPicker.addEventListener('change', (e) => {
            if(e.target.value) {
                const [year, month] = e.target.value.split('-');
                const newDate = new Date(year, month - 1, 1);
                
                // We just accept the date, even if it's 2050
                currentStartDate = getMonday(newDate);
                updateWeekView();
            }
        });

        updateWeekView();
    }