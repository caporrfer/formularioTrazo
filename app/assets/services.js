const gallery = document.querySelector('.contents-grid');
const cards = [...document.querySelectorAll('.content-card')];
const progress = document.querySelector('.services-gallery-progress');

if (gallery && cards.length && progress) {
  const dots = cards.map((card, index) => {
    card.setAttribute('role', 'listitem');
    card.setAttribute('aria-label', `Servicio ${index + 1} de ${cards.length}`);

    const dot = document.createElement('button');
    dot.type = 'button';
    dot.setAttribute('aria-label', `Ver servicio ${index + 1}`);
    dot.addEventListener('click', () => card.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'start' }));
    progress.appendChild(dot);
    return dot;
  });

  const setActive = (index) => dots.forEach((dot, dotIndex) => {
    const active = dotIndex === index;
    dot.classList.toggle('active', active);
    dot.setAttribute('aria-current', active ? 'true' : 'false');
  });

  const observer = new IntersectionObserver((entries) => {
    const visible = entries
      .filter((entry) => entry.isIntersecting)
      .sort((a, b) => b.intersectionRatio - a.intersectionRatio)[0];
    if (visible) setActive(cards.indexOf(visible.target));
  }, { root: gallery, threshold: [0.55, 0.75, 0.95] });

  cards.forEach((card) => observer.observe(card));
  setActive(0);
}
