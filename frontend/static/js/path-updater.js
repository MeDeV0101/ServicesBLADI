/**
 * Path Updater Script
 * This script updates all path references that might be dynamically loaded
 */

document.addEventListener('DOMContentLoaded', function() {
    console.log('Path Updater: Starting to update paths');
    
    // Function to update any remaining dynamic paths that weren't caught by the static file updates
    function updatePaths() {
        // Handle any dynamically loaded content or elements added after initial page load
        const observer = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
                if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {
                    mutation.addedNodes.forEach((node) => {
                        if (node.nodeType === Node.ELEMENT_NODE) {
                            // Check for any remaining '../assets/' references
                            updateElementPaths(node, '../assets/', '../static/');
                            // Check for any remaining '../views/' references
                            updateElementPaths(node, '../views/', '../template/');
                        }
                    });
                }
            });
        });
        
        // Start observing the document for dynamic content
        observer.observe(document.body, { childList: true, subtree: true });
        
        console.log('Path Updater: Path observer initialized');
    }
    
    // Helper function to update paths in an element
    function updateElementPaths(element, oldPath, newPath) {
        // Update attributes that might contain paths
        if (element.hasAttribute('src') && element.getAttribute('src').includes(oldPath)) {
            element.setAttribute('src', element.getAttribute('src').replace(oldPath, newPath));
        }
        if (element.hasAttribute('href') && element.getAttribute('href').includes(oldPath)) {
            element.setAttribute('href', element.getAttribute('href').replace(oldPath, newPath));
        }
        if (element.hasAttribute('style') && element.getAttribute('style').includes(oldPath)) {
            element.setAttribute('style', element.getAttribute('style').replace(oldPath, newPath));
        }
        
        // Process child elements
        if (element.children && element.children.length > 0) {
            Array.from(element.children).forEach(child => {
                updateElementPaths(child, oldPath, newPath);
            });
        }
    }

    // Run the path updater
    updatePaths();
});