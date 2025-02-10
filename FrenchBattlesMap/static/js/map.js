let map;
let markers;
let battles = [];
let currentBattleType = 'all';
let timelineChart = null;

// Initialize the map
function initMap() {
    map = L.map('map').setView([46.603354, 1.888334], 6);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors'
    }).addTo(map);

    markers = L.markerClusterGroup();
    map.addLayer(markers);
}

// Fetch and display battles
async function fetchBattles(startYear, endYear) {
    try {
        document.getElementById('loading').style.display = 'block';
        console.log(`Fetching battles between ${startYear} and ${endYear}`);

        const response = await fetch(`/api/battles?start_year=${startYear}&end_year=${endYear}`);
        if (!response.ok) {
            throw new Error('Failed to fetch battles');
        }

        const data = await response.json();
        if (!Array.isArray(data)) {
            throw new Error('Invalid battle data received');
        }

        battles = data.filter(battle => 
            battle && 
            battle.year >= startYear && 
            battle.year <= endYear
        );

        console.log(`Received ${battles.length} battles within range`);
        updateMarkers();
        updateTimelineChart();
    } catch (error) {
        console.error('Error fetching battles:', error);
        alert('Error loading battle data. Please try again.');
    } finally {
        document.getElementById('loading').style.display = 'none';
    }
}

// Update markers on the map
function updateMarkers() {
    markers.clearLayers();

    const filteredBattles = filterBattles();

    filteredBattles.forEach(battle => {
        if (!battle || !battle.latitude || !battle.longitude) {
            console.warn('Invalid battle data:', battle);
            return;
        }

        const marker = L.marker([battle.latitude, battle.longitude]);

        let sourcesHtml = '';
        if (battle.sources) {
            try {
                const sources = JSON.parse(battle.sources);
                sourcesHtml = `
                    <div class="mt-2">
                        <strong>Sources:</strong><br>
                        <div class="d-flex flex-column gap-1">
                            ${Object.entries(sources).map(([name, url]) => 
                                `<a href="${url}" target="_blank" class="btn btn-sm btn-outline-primary">
                                    <i class="fas fa-external-link-alt"></i> ${name.charAt(0).toUpperCase() + name.slice(1)}
                                </a>`
                            ).join('')}
                        </div>
                    </div>`;
            } catch (e) {
                console.error('Error parsing sources:', e);
            }
        }

        const mediaHtml = battle.media_urls ? 
            `<div class="media-gallery mt-2">
                <div class="media-content">
                    ${getMediaContent(battle)}
                </div>
             </div>` : '';

        const contextHtml = battle.historical_context ? 
            `<div class="mt-2">
                <strong>Contexte historique:</strong>
                <p>${battle.historical_context}</p>
            </div>` : '';

        const enrichButton = !battle.sources ? 
            `<button onclick="enrichBattle(${battle.id})" class="btn btn-sm btn-outline-secondary mt-2">
                <i class="fas fa-info-circle"></i> Plus d'informations
            </button>` : '';

        const popupContent = `
            <div class="popup-content">
                ${battle.image_url ? 
                    `<div class="main-image mb-3">
                        <img src="${battle.image_url}" alt="${battle.name}" class="img-fluid rounded">
                    </div>` : ''}
                <h5>${battle.name} (${battle.year})</h5>
                <p>${battle.description || 'Description non disponible'}</p>
                <p><strong>Participants:</strong> ${battle.participants || 'Inconnu'}</p>
                <p><strong>Résultat:</strong> ${battle.outcome || 'Inconnu'}</p>
                ${mediaHtml}
                ${contextHtml}
                ${sourcesHtml}
                ${enrichButton}
            </div>
        `;

        marker.bindPopup(popupContent, {
            maxWidth: 400,
            maxHeight: 400,
            autoPan: true,
            className: 'battle-popup'
        });
        markers.addLayer(marker);
    });
}

// Filter battles based on current type
function filterBattles() {
    return battles.filter(battle => {
        if (currentBattleType === 'all') return true;
        return battle.name.startsWith(currentBattleType);
    });
}

// Create and update timeline chart
function updateTimelineChart() {
    const filteredBattles = filterBattles();

    // Group battles by periods of 25 years for better granularity
    const periodSize = 25;
    const battleCounts = {};

    filteredBattles.forEach(battle => {
        const period = Math.floor(battle.year / periodSize) * periodSize;
        battleCounts[period] = (battleCounts[period] || 0) + 1;
    });

    const labels = Object.keys(battleCounts).sort((a, b) => Number(a) - Number(b))
        .map(year => `${year} - ${Number(year) + periodSize}`);
    const data = labels.map(label => battleCounts[label.split(' - ')[0]]);

    const ctx = document.getElementById('timelineChart').getContext('2d');

    if (timelineChart) {
        timelineChart.destroy();
    }

    timelineChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Nombre de batailles',
                data: data,
                backgroundColor: 'rgba(13, 110, 253, 0.5)',
                borderColor: 'rgb(13, 110, 253)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Nombre de batailles'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'Période'
                    },
                    ticks: {
                        maxRotation: 45,
                        minRotation: 45
                    }
                }
            },
            plugins: {
                legend: {
                    display: true,
                    position: 'top'
                },
                title: {
                    display: true,
                    text: 'Distribution temporelle des batailles'
                }
            }
        }
    });
}

// Initialize toggle button for density visualization
function initDensityToggle() {
    const toggleBtn = document.getElementById('toggleDensityBtn');
    const densityVisualization = document.getElementById('densityVisualization');

    toggleBtn.addEventListener('click', () => {
        const isHidden = densityVisualization.style.display === 'none';
        densityVisualization.style.display = isHidden ? 'block' : 'none';
        toggleBtn.innerHTML = `<i class="fas fa-chart-bar"></i> ${isHidden ? 'Masquer' : 'Afficher'} la distribution temporelle`;

        if (isHidden) {
            updateTimelineChart();
        }
    });
}

// Initialize range slider
function initSlider() {
    const yearSlider = document.getElementById('yearSlider');
    const yearDisplay = document.getElementById('yearDisplay');

    noUiSlider.create(yearSlider, {
        start: [0, 2025],
        connect: true,
        range: {
            'min': 0,
            'max': 2025
        },
        step: 1,
        behaviour: 'drag',
        format: {
            to: value => Math.round(value),
            from: value => Math.round(value)
        },
        pips: {
            mode: 'values',
            values: [0, 500, 1000, 1500, 2000],
            density: 4,
            stepped: true,
            format: {
                to: value => Math.round(value)
            }
        }
    });

    // Update display immediately during drag
    yearSlider.noUiSlider.on('drag', function(values) {
        yearDisplay.textContent = `${values[0]} - ${values[1]}`;
    });

    // Fetch battles only when sliding ends
    yearSlider.noUiSlider.on('change', function(values) {
        fetchBattles(values[0], values[1]);
    });

    // Initial fetch
    fetchBattles(0, 2025);
}

// Initialize battle type filters
function initBattleTypeFilters() {
    const filterButtons = document.querySelectorAll('.battle-type-btn');

    filterButtons.forEach(button => {
        button.addEventListener('click', () => {
            filterButtons.forEach(btn => btn.classList.remove('active'));
            button.classList.add('active');

            currentBattleType = button.getAttribute('data-type');
            updateMarkers();
            updateTimelineChart();
        });
    });
}

// Initialize the application
document.addEventListener('DOMContentLoaded', () => {
    initMap();
    initSlider();
    initBattleTypeFilters();
    initDensityToggle();
    fetchBattles(0, 2025);
});

// Fonction pour enrichir les informations d'une bataille
async function enrichBattle(battleId) {
    try {
        document.getElementById('loading').style.display = 'block';

        const response = await fetch(`/api/battles/${battleId}/enrich`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        console.log('Battle enriched:', data);

        // Recharger les batailles pour mettre à jour les informations
        const slider = document.getElementById('yearSlider');
        if (slider && slider.noUiSlider) {
            const values = slider.noUiSlider.get();
            await fetchBattles(values[0], values[1]);
        }

        // Afficher un message de succès
        alert('Informations enrichies avec succès !');
    } catch (error) {
        console.error('Error enriching battle:', error);
        alert('Erreur lors de l\'enrichissement des informations. Veuillez réessayer.');
    } finally {
        document.getElementById('loading').style.display = 'none';
    }
}

// Add this new function to handle different types of media
function getMediaContent(battle) {
    if (!battle.media_urls) return '';

    try {
        const mediaUrls = JSON.parse(battle.media_urls);
        return mediaUrls.map(media => {
            const url = media.url;
            const type = media.type || detectMediaType(url);

            switch (type) {
                case 'image':
                    return `<div class="media-item">
                        <img src="${url}" alt="Image historique" class="img-fluid rounded" onerror="this.style.display='none'">
                    </div>`;
                case 'video':
                    return `<div class="media-item">
                        <video controls class="img-fluid rounded">
                            <source src="${url}" type="video/mp4">
                            Votre navigateur ne supporte pas la lecture de vidéos.
                        </video>
                    </div>`;
                default:
                    return '';
            }
        }).join('');
    } catch (e) {
        console.error('Error parsing media URLs:', e);
        return '';
    }
}

function detectMediaType(url) {
    const extension = url.split('.').pop().toLowerCase();
    const imageExtensions = ['jpg', 'jpeg', 'png', 'gif', 'webp'];
    const videoExtensions = ['mp4', 'webm', 'ogg'];

    if (imageExtensions.includes(extension)) return 'image';
    if (videoExtensions.includes(extension)) return 'video';
    return 'unknown';
}