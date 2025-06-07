function createICSContent(appointment) {
    try {
        if (!appointment.preferred_date_time) {
            throw new Error('preferred_date_time is undefined');
        }

        const startDateTime = new Date(appointment.preferred_date_time);
        if (isNaN(startDateTime.getTime())) {
            throw new Error(`Invalid start date value: ${appointment.preferred_date_time}`);
        }

        const endDateTime = new Date(startDateTime.getTime() + 60 * 60000); // Assuming 1 hour appointments

        // Convert the dates to ISO strings without dashes, colons, and milliseconds
        const startISO = startDateTime.toISOString().replace(/-|:|\.\d\d\d/g, '');
        const endISO = endDateTime.toISOString().replace(/-|:|\.\d\d\d/g, '');

        const icsContent = [
            'BEGIN:VCALENDAR',
            'VERSION:2.0',
            'BEGIN:VEVENT',
            `DTSTART:${startISO}`,
            `DTEND:${endISO}`,
            `SUMMARY:${appointment.first_name} ${appointment.last_name}`,
            `DESCRIPTION:Appointment with ${appointment.first_name} ${appointment.last_name}. Service: ${appointment.service ? appointment.service : 'N/A'}.`,
            'END:VEVENT',
            'END:VCALENDAR'
        ].join('\n');

        return icsContent;
    } catch (error) {
        console.error('Error creating ICS content:', error, appointment);
        return '';
    }
}

function fetchAppointments() {
    fetch('api/admin_appointments', {
        credentials: 'include'  // Include cookies for session authentication
    })
    .then(response => {
        if (!response.ok) {
            console.error(`Server returned status ${response.status}`);
            throw new Error('Network response was not ok');
        }
        return response.json();
    })
    .then(data => {
        const appointmentsList = document.getElementById('appointmentsList');
        appointmentsList.innerHTML = ''; // Clear existing appointments
        data.forEach(appointment => {
            try {
                if (!appointment.preferred_date_time) {
                    console.warn('Skipping appointment due to missing preferred_date_time:', appointment);
                    return; // Skip this appointment
                }

                const dateTime = new Date(appointment.preferred_date_time);
                if (isNaN(dateTime.getTime())) {
                    throw new Error(`Invalid date value: ${appointment.preferred_date_time}`);
                }

                // Convert the dateTime to the user's local timezone
                const userTimezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
                const localDateTime = dateTime.toLocaleString('en-US', { timeZone: userTimezone });
                const formattedDateTime = new Date(localDateTime).toLocaleString('en-US', {
                    month: 'short',
                    day: '2-digit',
                    year: 'numeric',
                    hour: 'numeric',
                    minute: '2-digit',
                    hour12: true
                });

                const icsContent = createICSContent(appointment);
                const icsBlob = new Blob([icsContent], { type: 'text/calendar' });
                const icsUrl = URL.createObjectURL(icsBlob);

                const li = document.createElement('li');
                li.innerHTML = `<h3>${appointment.first_name} ${appointment.last_name}</h3> - 
                                <h4><a href="tel:${appointment.phone}">${appointment.phone}</a></h4> -
                                <h4>${appointment.email}</h4>
                                <h4><a href="${icsUrl}" download="${appointment.first_name}_${appointment.last_name}_appointment.ics">${formattedDateTime}</a></h4> - 
                                <h4>Service: ${appointment.service ? appointment.service : 'N/A'}</h4> - 
                                <h4>Estimator: ${appointment.estimator ? appointment.estimator : 'N/A'}</h4>
                                <button onclick="deleteAppointment(${appointment.id})">Delete</button>`;
                appointmentsList.appendChild(li);
            } catch (error) {
                console.error('Error processing appointment:', error, appointment);
            }
        });
    })
    .catch(error => {
        console.error('Fetch error:', error);
    });
}

function deleteAppointment(appointmentId) {
    const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
    fetch(`api/appointments/delete`, {
        method: 'POST',
        credentials: 'include',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        },
        body: JSON.stringify({ appointment_id: appointmentId })
    })
    .then(response => {
        if (!response.ok) {
            console.error(`Server returned status ${response.status}`);
            throw new Error('Network response was not ok');
        }
        return response.json();
    })
    .then(data => {
        if (data.status === 'success') {
            fetchAppointments(); // Refresh the appointments list
        } else {
            console.error('Error deleting appointment:', data.message);
        }
    })
    .catch(error => {
        console.error('Fetch error:', error);
    });
}

// Fetch appointments every minute
setInterval(fetchAppointments, 60000);
fetchAppointments(); // Initial fetch