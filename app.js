/**
 * S-ELT Platform Logic
 * Professional Academic Prototype
 */

// Toast Notification Helper
function showToast(msg) {
    const t = document.getElementById('toast');
    if (!t) return;
    t.innerText = msg;
    t.style.display = 'block';
    setTimeout(() => {
        t.style.display = 'none';
    }, 3000);
}

// Module specific logic (if needed)
function startDecompTest(type) {
    showToast(`Starting ${type.toUpperCase()} module...`);
    setTimeout(() => {
        showToast(`${type.toUpperCase()} Complete!`);
    }, 1000);
}

// Navigation Sync (Optional for MPA but good to have)
window.onload = () => {
    console.log("S-ELT Page Loaded: " + window.location.pathname);
};
