function toggleTheme() {
    const currentTheme = document.documentElement.getAttribute('data-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    
    document.documentElement.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
    
    // Update map tiles based on theme
    if (map) {
        const layer = map.getContainer().querySelector('.leaflet-tile-pane');
        layer.style.filter = newTheme === 'dark' ? 'invert(90%) hue-rotate(180deg)' : 'none';
    }
}

document.addEventListener('DOMContentLoaded', () => {
    const savedTheme = localStorage.getItem('theme') || 'light';
    document.documentElement.setAttribute('data-theme', savedTheme);
    
    if (savedTheme === 'dark' && map) {
        const layer = map.getContainer().querySelector('.leaflet-tile-pane');
        layer.style.filter = 'invert(90%) hue-rotate(180deg)';
    }
});
