document.addEventListener('DOMContentLoaded', function() {
    console.log('DOMContentLoaded event fired.');

    var calendarEl = document.getElementById('calendar');
    console.log('Calendar element:', calendarEl);
    
    var calendarContainer = document.getElementById('calendar-container');
    console.log('Calendar container element:', calendarContainer);
    
    var step1 = document.getElementById('step-1');
    console.log('Step 1 element:', step1);
    
    var step2 = document.getElementById('step-2');
    console.log('Step 2 element:', step2);
    
    var nextButton = document.getElementById('next-button');
    console.log('Next button element:', nextButton);
    
    var userTimezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
    console.log('User Timezone detected:', userTimezone);
    
    var csrfToken = getCsrfToken();
    console.log('CSRF Token fetched:', csrfToken);
    
    let calendar; // Declare calendar variable to be accessible throughout

    if (typeof FullCalendar !== 'undefined') {
        try {
            // Initialize the calendar
            calendar = new FullCalendar.Calendar(calendarEl, {
                initialView: 'dayGridMonth',
                selectable: true, // Enable date selection
                headerToolbar: {
                    left: 'prev,next today',
                    center: 'title',
                    right: 'dayGridMonth,listMonth'
                },
                events: '/api/upcoming_appointments',
                eventColor: '#378006',
                timeZone: 'local',  // Ensure FullCalendar uses the local time zone

                select: function(info) {
                    console.log('Date selected:', info.startStr);

                    // Highlight the selected date
                    highlightDate(info.startStr);

                    // Handle date selection
                    handleDateSelection(info.startStr);
                },

                dateClick: function(info) {
                    console.log('Date clicked:', info.dateStr);

                    // Highlight the clicked date
                    highlightDate(info.dateStr);

                    // Handle date click
                    handleDateSelection(info.dateStr);
                }
            });

            console.log('Calendar initialized successfully.');

            // Render the calendar
            calendar.render();
            console.log('Calendar rendered.');
        } catch (error) {
            console.error('Error initializing or rendering FullCalendar:', error);
        }
    } else {
        console.error('FullCalendar is not defined.');
    }

    // Add touch event listener for date selection on touch devices
    calendarEl.addEventListener('touchstart', function(event) {
        console.log('Touchstart event detected:', event);
        var touch = event.touches[0];
        var targetElement = document.elementFromPoint(touch.clientX, touch.clientY);
        console.log('Touch event detected on element:', targetElement);
        if (targetElement && targetElement.hasAttribute('data-date')) {
            var dateStr = targetElement.getAttribute('data-date');
            console.log('Date string from touch event:', dateStr);
            if (dateStr) {
                highlightDate(dateStr);
                handleDateSelection(dateStr);
            }
        }
    });

    // Add event listener to the date input field
    addDateInputListener();

    function addDateInputListener() {
        var dateInput = document.getElementById('preferred_date');
        dateInput.addEventListener('change', function() {
            var selectedDate = this.value;
            if (selectedDate) {
                handleDateInputChange(selectedDate);
            }
        });
    }

    function handleDateInputChange(dateStr) {
        console.log('Date input changed:', dateStr);

        // Select the date in the calendar
        var date = new Date(dateStr + 'T00:00:00'); // Ensure time component is set to midnight
        calendar.select(date);

        // Highlight the date
        highlightDate(dateStr);

        // Fetch available time slots
        handleDateSelection(dateStr);
    }

    function highlightDate(dateStr) {
        // Remove highlight from previously selected date
        document.querySelectorAll('.selected-date').forEach(function(cell) {
            cell.classList.remove('selected-date');
        });

        // Add highlight to the selected date
        var selectedCell = document.querySelector('[data-date="' + dateStr + '"]');
        if (selectedCell) {
            selectedCell.classList.add('selected-date');
        }
    }

    function handleDateSelection(dateStr) {
        console.log('Handling date selection:', dateStr);

        document.getElementById('preferred_date').value = dateStr;
        console.log('Preferred date set to:', dateStr);

        fetch('/get_available_time_slots', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify({
                date: dateStr,
                timezone: userTimezone
            })
        })
        .then(response => {
            console.log('Fetch response:', response);
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            console.log('Time slots data received:', data);
            populateTimeSlots(data, userTimezone);
        })
        .catch(error => {
            console.error('Error fetching time slots:', error);
        });
    }

    nextButton.addEventListener('click', handleNextButtonClick);
    nextButton.addEventListener('touchstart', handleNextButtonClick);

    function handleNextButtonClick(event) {
        event.preventDefault();
        console.log('"Next" button clicked.');

        var form = document.getElementById('personal-info-form');
        console.log('Personal info form element:', form);

        if (form.checkValidity()) {
            console.log('Personal info form validation successful.');

            copyPersonalInfoToStep2();

            step1.style.display = 'none';
            step2.style.display = 'block';
            calendarContainer.style.display = 'block';
            console.log('Navigating to Step 2 and showing the calendar.');

            // Force a reflow and repaint of the calendar container
            calendarContainer.offsetHeight;

            // Re-render the calendar to ensure it displays correctly
            calendar.render();
        } else {
            console.warn('Personal info form validation failed.');
            form.reportValidity();
        }
    }
});

function copyPersonalInfoToStep2() {
    var form = document.getElementById('personal-info-form');
    console.log('Copying personal info from form:', form);

    document.getElementById('hidden_first_name').value = form.querySelector('[name="first_name"]').value;
    document.getElementById('hidden_last_name').value = form.querySelector('[name="last_name"]').value;
    document.getElementById('hidden_phone').value = form.querySelector('[name="phone"]').value;
    document.getElementById('hidden_email').value = form.querySelector('[name="email"]').value;
    console.log('Personal info copied to Step 2.');
}

function convertUTCToLocal(utcTimeStr, userTimezone) {
    console.log('Converting UTC time to local time:', utcTimeStr, 'for timezone:', userTimezone);
    const utcDateTime = new Date(utcTimeStr);

    if (isNaN(utcDateTime)) {
        console.error('Invalid UTC Date string:', utcTimeStr);
        return 'Invalid Date';
    }

    const localTimeFormatter = new Intl.DateTimeFormat('en-US', {
        timeZone: userTimezone,
        hour: '2-digit',
        minute: '2-digit',
        hour12: true
    });

    const localTime = localTimeFormatter.format(utcDateTime);
    console.log('Converted UTC to local time:', utcTimeStr, '->', localTime);
    return localTime;
}

function populateTimeSlots(data, userTimezone) {
    console.log('Populating time slots with data:', data, 'and timezone:', userTimezone);
    const timeDropdown = document.getElementById('preferred_time');
    timeDropdown.innerHTML = '';

    if (data.timeSlots.length === 0) {
        const option = document.createElement('option');
        option.textContent = 'No available slots';
        option.disabled = true;
        timeDropdown.appendChild(option);
        console.warn('No available time slots for the selected date.');
    } else {
        data.timeSlots.forEach(slot => {
            const localTime = convertUTCToLocal(slot, userTimezone);
            const option = document.createElement('option');
            option.value = slot;
            option.textContent = localTime;
            timeDropdown.appendChild(option);
        });
        console.log('Time slots populated in dropdown.');
    }
}