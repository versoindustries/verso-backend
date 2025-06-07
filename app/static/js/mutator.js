document.addEventListener("DOMContentLoaded", function() {
    // Target container where you want the widget to be placed
    const targetContainer = document.getElementById('square-appointments-widget');

    // Options for the observer (which mutations to observe)
    const config = { childList: true, subtree: true };

    // Callback function to execute when mutations are observed
    const callback = function(mutationsList, observer) {
        for(let mutation of mutationsList) {
            if (mutation.type === 'childList') {
                // Check if the Square widget has been added
                const squareWidget = document.querySelector('.square-appointments-widget'); // Adjust the selector based on the actual widget's class or ID
                if (squareWidget) {
                    // Move the widget to the target container
                    targetContainer.appendChild(squareWidget);
                    observer.disconnect(); // Stop observing once the widget has been moved
                }
            }
        }
    };

    // Create an observer instance linked to the callback function
    const observer = new MutationObserver(callback);

    // Start observing the document body for configured mutations
    observer.observe(document.body, config);
});