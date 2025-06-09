// app/static/js/calendar.js
document.addEventListener('DOMContentLoaded', function() {
    console.debug('DOMContentLoaded event fired.');

    const calendarEl = document.getElementById('calendar');
    console.debug('Calendar element:', calendarEl);
    
    const calendarContainer = document.getElementById('calendar-container');
    console.debug('Calendar container element:', calendarContainer);
    
    const step1 = document.getElementById('step-1');
    console.debug('Step 1 element:', step1);
    
    const step2 = document.getElementById('step-2');
    console.debug('Step 2 element:', step2);
    
    const nextButton = document.getElementById('next-button');
    console.debug('Next button element:', nextButton);
    
    const userTimezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
    console.debug('User Timezone detected:', userTimezone);
    
    const csrfToken = getCsrfToken();
    console.debug('CSRF Token fetched:', csrfToken);

    let companyConfig = null; // Store business configuration
    let calendar; // Declare calendar variable

    // Fetch business configuration
    fetch('/api/business_config', {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Failed to fetch business configuration');
        }
        return response.json();
    })
    .then(data => {
        companyConfig = data;
        console.debug('Business configuration loaded:', companyConfig);
        initializeCalendar();
    })
    .catch(error => {
        console.error('Error fetching business configuration:', error);
        // Fallback to defaults
        companyConfig = {
            company_timezone: 'America/Denver',
            business_start_time: '08:00',
            business_end_time: '17:00',
            buffer_time_minutes: 30
        };
        initializeCalendar();
    });

    function initializeCalendar() {
        if (typeof FullCalendar !== 'undefined') {
            try {
                calendar = new FullCalendar.Calendar(calendarEl, {
                    initialView: 'dayGridMonth',
                    selectable: true,
                    headerToolbar: {
                        left: 'prev,next today',
                        center: 'title',
                        right: 'dayGridMonth,listMonth'
                    },
                    events: '/api/upcoming_appointments',
                    eventColor: '#378006',
                    timeZone: companyConfig.company_timezone, // Use company timezone

                    select: function(info) {
                        console.debug('Date selected:', info.startStr);
                        highlightDate(info.startStr);
                        handleDateSelection(info.startStr);
                    },

                    dateClick: function(info) {
                        console.debug('Date clicked:', info.dateStr);
                        highlightDate(info.dateStr);
                        handleDateSelection(info.dateStr);
                    }
                });

                console.debug('Calendar initialized successfully.');
                calendar.render();
                console.debug('Calendar rendered.');
            } catch (error) {
                console.error('Error initializing or rendering FullCalendar:', error);
            }
        } else {
            console.error('FullCalendar is not defined.');
        }
    }

    // Touch event listener for date selection on mobile
    calendarEl.addEventListener('touchstart', function(event) {
        console.debug('Touchstart event detected:', event);
        const touch = event.touches[0];
        const targetElement = document.elementFromPoint(touch.clientX, touch.clientY);
        console.debug('Touch event detected on element:', targetElement);
        if (targetElement && targetElement.hasAttribute('data-date')) {
            const dateStr = targetElement.getAttribute('data-date');
            console.debug('Date string from touch event:', dateStr);
            if (dateStr) {
                highlightDate(dateStr);
                handleDateSelection(dateStr);
            }
        }
    }, { passive: true });

    // Date input listener
    addDateInputListener();

    function addDateInputListener() {
        const dateInput = document.getElementById('preferred_date');
        dateInput.addEventListener('change', function() {
            const selectedDate = this.value;
            if (selectedDate) {
                handleDateInputChange(selectedDate);
            }
        });
    }

    function handleDateInputChange(dateStr) {
        console.debug('Date input changed:', dateStr);
        const date = new Date(dateStr + 'T00:00:00');
        calendar.select(date);
        highlightDate(dateStr);
        handleDateSelection(dateStr);
    }

    function highlightDate(dateStr) {
        document.querySelectorAll('.selected-date').forEach(cell => {
            cell.classList.remove('selected-date');
        });
        const selectedCell = document.querySelector(`[data-date="${dateStr}"]`);
        if (selectedCell) {
            selectedCell.classList.add('selected-date');
        }
    }

    function handleDateSelection(dateStr) {
        console.debug('Handling date selection:', dateStr);
        document.getElementById('preferred_date').value = dateStr;
        console.debug('Preferred date set to:', dateStr);

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
            console.debug('Fetch response:', response);
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            console.debug('Time slots data received:', data);
            populateTimeSlots(data, userTimezone, companyConfig.company_timezone);
        })
        .catch(error => {
            console.error('Error fetching time slots:', error);
            const timeDropdown = document.getElementById('preferred_time');
            timeDropdown.innerHTML = '<option disabled>Error loading time slots</option>';
        });
    }

    nextButton.addEventListener('click', handleNextButtonClick);
    nextButton.addEventListener('touchstart', handleNextButtonClick, { passive: true });

    function handleNextButtonClick(event) {
        event.preventDefault();
        console.debug('"Next" button clicked.');
        const form = document.getElementById('personal-info-form');
        console.debug('Personal info form element:', form);

        if (form.checkValidity()) {
            console.debug('Personal info form validation successful.');
            copyPersonalInfoToStep2();
            step1.style.display = 'none';
            step2.style.display = 'block';
            calendarContainer.style.display = 'block';
            console.debug('Navigating to Step 2 and showing the calendar.');
            calendarContainer.offsetHeight; // Force reflow
            calendar.render();
        } else {
            console.warn('Personal info form validation failed.');
            form.reportValidity();
        }
    }
});

function copyPersonalInfoToStep2() {
    const form = document.getElementById('personal-info-form');
    console.debug('Copying personal info from form:', form);
    document.getElementById('hidden_first_name').value = form.querySelector('[name="first_name"]').value;
    document.getElementById('hidden_last_name').value = form.querySelector('[name="last_name"]').value;
    document.getElementById('hidden_phone').value = form.querySelector('[name="phone"]').value;
    document.getElementById('hidden_email').value = form.querySelector('[name="email"]').value;
    console.debug('Personal info copied to Step 2.');
}

function convertUTCToLocal(utcTimeStr, targetTimezone, showUserTimezone = false, userTimezone = null) {
    console.debug('Converting UTC time:', utcTimeStr, 'to timezone:', targetTimezone);
    const utcDateTime = new Date(utcTimeStr);
    if (isNaN(utcDateTime)) {
        console.error('Invalid UTC Date string:', utcTimeStr);
        return 'Invalid Date';
    }

    const formatter = new Intl.DateTimeFormat('en-US', {
        timeZone: targetTimezone,
        hour: '2-digit',
        minute: '2-digit',
        hour12: true
    });

    let localTime = formatter.format(utcDateTime);
    if (showUserTimezone && userTimezone && userTimezone !== targetTimezone) {
        const userFormatter = new Intl.DateTimeFormat('en-US', {
            timeZone: userTimezone,
            hour: '2-digit',
            minute: '2-digit',
            hour12: true
        });
        const userTime = userFormatter.format(utcDateTime);
        localTime += ` (${userTime})`;
    }

    console.debug('Converted UTC to local time:', utcTimeStr, '->', localTime);
    return localTime;
}

function populateTimeSlots(data, userTimezone, companyTimezone) {
    console.debug('Populating time slots with data:', data, 'company timezone:', companyTimezone);
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
            // Display time in company timezone, with user timezone in parentheses
            const localTime = convertUTCToLocal(slot, companyTimezone, true, userTimezone);
            const option = document.createElement('option');
            option.value = slot;
            option.textContent = localTime;
            timeDropdown.appendChild(option);
        });
        console.debug('Time slots populated in dropdown.');
    }
}