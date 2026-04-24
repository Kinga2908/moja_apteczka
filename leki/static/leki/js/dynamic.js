function initFadeInOnScroll() {
  const cards = document.querySelectorAll('.fade-card');

  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry, i) => {
      if (entry.isIntersecting) {
        // opóźnienie zależne od kolejności karty
        setTimeout(() => {
          entry.target.classList.add('visible');
        }, i * 100);
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.1 });

  cards.forEach(card => observer.observe(card));
}

function initChart() {
  const canvas = document.getElementById('przyjecia-chart');
  if (!canvas) return;

  // Zbieramy dane z atrybutów data-* na kartkach przyjęć
  const today = new Date();
  const labels = [];
  const counts = {};

  for (let i = 6; i >= 0; i--) {
    const d = new Date(today);
    d.setDate(today.getDate() - i);
    const key = d.toISOString().slice(0, 10);
    const label = d.toLocaleDateString('pl-PL', { weekday: 'short', day: 'numeric', month: 'numeric' });
    labels.push(label);
    counts[key] = 0;
  }

  // Zliczamy przyjęcia z DOM (data-date na każdej karcie przyjęcia)
  document.querySelectorAll('[data-przyjecie-date]').forEach(el => {
    const dateStr = el.dataset.przyjecie_date || el.dataset.przyjecieDate;
    if (dateStr && dateStr in counts) {
      counts[dateStr]++;
    }
  });

  const data = Object.values(counts);

  new Chart(canvas, {
    type: 'bar',
    data: {
      labels,
      datasets: [{
        label: 'Przyjęcia leków',
        data,
        backgroundColor: 'rgba(99, 102, 241, 0.7)',
        borderColor: 'rgba(99, 102, 241, 1)',
        borderWidth: 2,
        borderRadius: 6,
      }]
    },
    options: {
      responsive: true,
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: ctx => ` ${ctx.parsed.y} przyjęć`
          }
        }
      },
      scales: {
        y: {
          beginAtZero: true,
          ticks: { stepSize: 1 },
          grid: { color: 'rgba(0,0,0,0.05)' }
        },
        x: { grid: { display: false } }
      }
    }
  });
}


function initDragAndDrop() {
  const container = document.getElementById('przyjecia-lista');
  if (!container) return;

  let draggedEl = null;

  container.querySelectorAll('.przyjecie-card').forEach(card => {
    card.setAttribute('draggable', 'true');

    card.addEventListener('dragstart', e => {
      draggedEl = card;
      card.classList.add('dragging');
      e.dataTransfer.effectAllowed = 'move';
    });

    card.addEventListener('dragend', () => {
      card.classList.remove('dragging');
      draggedEl = null;
      // Usuń podświetlenie ze wszystkich
      container.querySelectorAll('.przyjecie-card').forEach(c => c.classList.remove('drag-over'));
    });

    card.addEventListener('dragover', e => {
      e.preventDefault();
      e.dataTransfer.dropEffect = 'move';
      if (card !== draggedEl) {
        card.classList.add('drag-over');
      }
    });

    card.addEventListener('dragleave', () => {
      card.classList.remove('drag-over');
    });

    card.addEventListener('drop', e => {
      e.preventDefault();
      card.classList.remove('drag-over');
      if (draggedEl && draggedEl !== card) {
        // Wstaw przeciągany element przed kartą, na którą upuszczono
        const allCards = [...container.querySelectorAll('.przyjecie-card')];
        const dragIdx = allCards.indexOf(draggedEl);
        const dropIdx = allCards.indexOf(card);

        if (dragIdx < dropIdx) {
          container.insertBefore(draggedEl, card.nextSibling);
        } else {
          container.insertBefore(draggedEl, card);
        }

        // Krótka animacja potwierdzenia
        draggedEl.classList.add('drop-success');
        setTimeout(() => draggedEl.classList.remove('drop-success'), 500);
      }
    });
  });
}


document.addEventListener('DOMContentLoaded', () => {
  initFadeInOnScroll();
  initChart();
  initDragAndDrop();
});
