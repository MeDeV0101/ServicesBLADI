// Initialize calendar with appointments
document.addEventListener('DOMContentLoaded', function() {
  const calendarEl = document.getElementById('calendar');
  if (calendarEl && typeof FullCalendar !== 'undefined') {
    // Generate some example events spanning next month
    const today = new Date();
    const events = [];
    
    // Add events for the next 30 days
    for (let i = 0; i < 3; i++) {
      const eventDate = new Date();
      eventDate.setDate(today.getDate() + (3 * (i+1)));
      eventDate.setHours(10 + i, 0, 0);
      
      events.push({
        title: i === 0 ? 'Consultation Administrative' : 
               i === 1 ? 'Rendez-vous Immobilier' : 'Consultation Fiscale',
        start: eventDate.toISOString(),
        backgroundColor: '#1e3c72',
        borderColor: '#1e3c72',
        url: '/client/rendezvous/'
      });
    }
    
    const calendar = new FullCalendar.Calendar(calendarEl, {
      initialView: 'dayGridMonth',
      headerToolbar: {
        left: 'prev,next today',
        center: 'title',
        right: 'dayGridMonth,timeGridWeek'
      },
      height: 450,
      contentHeight: 'auto',
      events: events
    });
    calendar.render();
  }
});
