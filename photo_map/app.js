const memories = [
  { id: "barcelona", title: "La sobremesa infinita", place: "Barcelona, España", date: "Mayo 2019", year: "2019", x: 38, y: 35, tags: ["viajes", "sabores"], palette: ["#d98364", "#f3c98b", "#50756b"], scene: "city", story: "Compartimos pan con tomate hasta que las luces de la plaza se encendieron. Nadie miró el reloj; aquella mesa pequeña parecía contener toda la ciudad." },
  { id: "paris", title: "Lluvia sobre el canal", place: "París, Francia", date: "Octubre 2019", year: "2019", x: 34, y: 24, tags: ["viajes"], palette: ["#677a89", "#c7b8a0", "#e8ddd0"], scene: "rain", story: "La lluvia vació las calles junto a Saint-Martin. Caminamos sin paraguas, siguiendo los reflejos dorados de los cafés sobre el adoquín." },
  { id: "tokio", title: "Neón a medianoche", place: "Tokio, Japón", date: "Febrero 2020", year: "2020", x: 86, y: 39, tags: ["viajes", "sabores"], palette: ["#27445a", "#df5f6a", "#efb65e"], scene: "city", story: "Un ramen humeante después del último tren. Afuera, Shinjuku seguía brillando como si la noche acabara de empezar." },
  { id: "oaxaca", title: "Domingo de mole", place: "Oaxaca, México", date: "Noviembre 2021", year: "2021", x: 18, y: 49, tags: ["viajes", "sabores", "celebraciones"], palette: ["#a84d32", "#e6a33d", "#4c7a58"], scene: "market", story: "La fiesta llegó hasta la cocina: siete moles, flores de papel y una abuela que medía cada ingrediente con la memoria." },
  { id: "buenos-aires", title: "Bailar hasta el alba", place: "Buenos Aires, Argentina", date: "Marzo 2022", year: "2022", x: 30, y: 79, tags: ["viajes", "celebraciones"], palette: ["#7f3151", "#d98b75", "#efcf9b"], scene: "dance", story: "La fiesta terminó cuando el cielo de San Telmo se volvió rosa. Aprendimos apenas tres pasos, suficientes para no querer sentarnos." },
  { id: "marrakech", title: "Té bajo las estrellas", place: "Marrakech, Marruecos", date: "Junio 2022", year: "2022", x: 43, y: 52, tags: ["viajes", "sabores"], palette: ["#b65c3b", "#ddb972", "#315b52"], scene: "desert", story: "Menta fresca, vasos diminutos y el rumor de la medina apagándose. Desde la terraza, el Atlas era una sombra azul en el horizonte." },
  { id: "nueva-york", title: "Azotea en verano", place: "Nueva York, EE. UU.", date: "Agosto 2022", year: "2022", x: 14, y: 29, tags: ["viajes", "celebraciones"], palette: ["#315a66", "#d56e51", "#f3c66b"], scene: "city", story: "Una fiesta improvisada sobre Brooklyn, luces colgadas entre chimeneas y canciones compartidas con gente que acabábamos de conocer." },
  { id: "lisboa", title: "Pasteles junto al Tajo", place: "Lisboa, Portugal", date: "Abril 2023", year: "2023", x: 35, y: 47, tags: ["sabores"], palette: ["#477a82", "#e7b552", "#f5e4bd"], scene: "coast", story: "Todavía tibios, cubiertos de canela y comidos mirando los tranvías. El río hacía que la tarde entera pareciera dorada." },
  { id: "bangkok", title: "El puesto de la esquina", place: "Bangkok, Tailandia", date: "Julio 2023", year: "2023", x: 78, y: 59, tags: ["sabores"], palette: ["#3d735d", "#ef9d38", "#bf3f45"], scene: "market", story: "Volvimos tres noches al mismo puesto. La cocinera ya conocía nuestro pedido y siempre añadía una lima extra al curry." },
  { id: "sevilla", title: "Patio de naranjos", place: "Sevilla, España", date: "Septiembre 2023", year: "2023", x: 39, y: 43, tags: ["celebraciones"], palette: ["#d97945", "#f0c875", "#538260"], scene: "garden", story: "La celebración se extendió por todo el patio: guitarras, palmas y perfume de azahar entrando por las ventanas abiertas." },
  { id: "rio", title: "Confeti frente al mar", place: "Río de Janeiro, Brasil", date: "Febrero 2024", year: "2024", x: 34, y: 69, tags: ["celebraciones"], palette: ["#1c8192", "#f0b83f", "#e45a69"], scene: "coast", story: "La fiesta era una corriente de música bajando hacia el océano. Guardamos un puñado de confeti dentro del cuaderno de viaje." },
  { id: "patagonia", title: "Viento del fin del mundo", place: "Patagonia, Chile", date: "Abril 2024", year: "2024", x: 25, y: 89, tags: ["naturaleza"], palette: ["#335d67", "#8aa6a1", "#d8d6c5"], scene: "mountain", story: "El sendero desaparecía entre nubes bajas. Al llegar al mirador, el viento abrió el paisaje durante unos segundos perfectos." },
  { id: "kioto", title: "Silencio entre cedros", place: "Kioto, Japón", date: "Octubre 2024", year: "2024", x: 88, y: 48, tags: ["naturaleza"], palette: ["#315c4b", "#9aaf77", "#d8aa77"], scene: "forest", story: "Subimos temprano a Kurama. Solo se oían nuestros pasos, agua corriendo bajo las hojas y una campana muy lejos." },
  { id: "islandia", title: "La noche se volvió verde", place: "Vík, Islandia", date: "Enero 2025", year: "2025", x: 47, y: 13, tags: ["naturaleza"], palette: ["#173d49", "#4fa47e", "#b8e0c5"], scene: "aurora", story: "Esperamos horas en la playa negra. Entonces una línea verde cruzó el cielo y todos olvidamos el frío al mismo tiempo." }
];

const state = { filter: "all", query: "", selected: null };
const elements = {
  markers: document.querySelector("#markers"), search: document.querySelector("#search"),
  filters: document.querySelector("#filters"), count: document.querySelector("#visible-count"),
  card: document.querySelector("#memory-card"), empty: document.querySelector("#empty-state"),
  image: document.querySelector("#memory-image"), meta: document.querySelector("#memory-meta"),
  title: document.querySelector("#memory-title"), story: document.querySelector("#memory-story"),
  place: document.querySelector("#memory-place")
};

const normalize = value => value.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase();
const escapeXml = value => value.replace(/[&<>"']/g, char => ({"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&apos;"}[char]));

function illustration(memory) {
  const [a, b, c] = memory.palette;
  const motifs = {
    city: `<rect x="35" y="95" width="62" height="105" fill="${c}"/><rect x="105" y="65" width="88" height="135" fill="${a}"/><rect x="202" y="110" width="80" height="90" fill="${c}"/><g fill="${b}">${[55,75,125,150,220,245].map(x=>`<rect x="${x}" y="125" width="9" height="13"/>`).join("")}</g>`,
    rain: `<g stroke="${b}" stroke-width="3" opacity=".65">${[30,70,110,150,190,230,270].map((x,i)=>`<path d="M${x} ${15+i%2*20}l-28 72"/>`).join("")}</g><path d="M50 170 Q150 70 250 170" fill="${c}"/><rect x="145" y="145" width="10" height="60" fill="${a}"/>`,
    market: `<path d="M35 95h230l-22-55H57z" fill="${b}"/><path d="M55 95v105h190V95" fill="${c}"/><g fill="${a}">${[0,1,2,3,4].map(i=>`<circle cx="${82+i*34}" cy="142" r="14"/>`).join("")}</g>`,
    dance: `<circle cx="110" cy="88" r="25" fill="${b}"/><path d="M105 110l-40 90h100z" fill="${a}"/><circle cx="205" cy="82" r="23" fill="${c}"/><path d="M201 104l-25 96h78z" fill="${b}"/>`,
    desert: `<circle cx="230" cy="55" r="32" fill="${b}"/><path d="M0 170Q75 105 150 170T300 158V220H0z" fill="${a}"/><path d="M0 195Q100 140 190 195T330 182V220H0z" fill="${c}"/>`,
    coast: `<circle cx="235" cy="50" r="30" fill="${b}"/><path d="M0 130Q50 110 100 130T200 130T300 130V220H0z" fill="${a}"/><path d="M0 160Q70 135 140 160T280 160V220H0z" fill="${c}"/>`,
    garden: `<rect x="0" y="155" width="300" height="65" fill="${c}"/><g fill="${a}">${[45,95,150,205,260].map((x,i)=>`<circle cx="${x}" cy="${110-i%2*18}" r="30"/>`).join("")}</g><g fill="${b}">${[60,130,220].map(x=>`<circle cx="${x}" cy="125" r="12"/>`).join("")}</g>`,
    mountain: `<path d="M0 205L85 72l38 50 45-72 132 155z" fill="${c}"/><path d="M105 205L205 45l95 160z" fill="${a}"/><path d="M174 96l31-51 33 55-28-12z" fill="${b}"/>`,
    forest: `<rect width="300" height="220" fill="${c}"/><g fill="${a}">${[25,72,120,182,235,280].map((x,i)=>`<path d="M${x} 15l-${28+i%2*8} 165h${56+i%2*16}z"/>`).join("")}</g><path d="M135 220l24-140 20 140" fill="${b}" opacity=".55"/>`,
    aurora: `<rect width="300" height="220" fill="${a}"/><path d="M-20 55Q65 0 145 55T320 35" fill="none" stroke="${c}" stroke-width="29" opacity=".72"/><path d="M-10 78Q100 20 190 72T315 62" fill="none" stroke="${b}" stroke-width="13" opacity=".65"/><path d="M0 180l70-55 45 40 52-70 133 85v40H0z" fill="#162f38"/>`
  };
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 300 220"><rect width="300" height="220" fill="${memory.palette[1]}"/>${motifs[memory.scene]}<rect y="188" width="300" height="32" fill="rgba(20,30,27,.42)"/><text x="16" y="208" fill="white" font-family="Georgia" font-size="12">${escapeXml(memory.place)}</text></svg>`;
  return `url("data:image/svg+xml,${encodeURIComponent(svg)}")`;
}

function matches(memory) {
  const category = state.filter === "all" || memory.tags.includes(state.filter);
  const haystack = normalize([memory.title, memory.place, memory.date, memory.story, ...memory.tags].join(" "));
  return category && (!state.query || haystack.includes(normalize(state.query)));
}

function renderMarkers() {
  const visible = memories.filter(matches);
  elements.count.textContent = String(visible.length);
  elements.empty.hidden = visible.length !== 0;
  elements.markers.querySelectorAll(".marker").forEach(marker => {
    const memory = memories.find(item => item.id === marker.dataset.id);
    marker.classList.toggle("filtered", !matches(memory));
    marker.classList.toggle("active", state.selected === memory.id);
    marker.setAttribute("aria-pressed", String(state.selected === memory.id));
  });
}

function updateUrl() {
  const params = new URLSearchParams();
  if (state.filter !== "all") params.set("filter", state.filter);
  if (state.query) params.set("q", state.query);
  if (state.selected) params.set("memory", state.selected);
  history.replaceState(null, "", `${location.pathname}${params.size ? `?${params}` : ""}`);
}

function selectMemory(id, sync = true) {
  const memory = memories.find(item => item.id === id);
  state.selected = memory?.id || null;
  if (!memory) {
    elements.card.hidden = true;
  } else {
    elements.image.style.backgroundImage = illustration(memory);
    elements.image.setAttribute("aria-label", `Ilustración de ${memory.place}`);
    elements.meta.textContent = `${memory.date} · ${memory.tags[0]}`;
    elements.title.textContent = memory.title;
    elements.story.textContent = memory.story;
    elements.place.textContent = `⌖ ${memory.place}`;
    elements.card.hidden = false;
  }
  renderMarkers();
  if (sync) updateUrl();
}

function setFilter(filter, sync = true) {
  state.filter = ["all", "viajes", "sabores", "celebraciones"].includes(filter) ? filter : "all";
  document.querySelectorAll(".filter").forEach(button => button.classList.toggle("active", button.dataset.filter === state.filter));
  if (state.selected && !matches(memories.find(item => item.id === state.selected))) selectMemory(null, false);
  renderMarkers();
  if (sync) updateUrl();
}

function resetAll() {
  state.query = "";
  elements.search.value = "";
  selectMemory(null, false);
  setFilter("all", false);
  updateUrl();
}

memories.forEach(memory => {
  const marker = document.createElement("button");
  marker.className = "marker";
  marker.dataset.id = memory.id;
  marker.style.left = `${memory.x}%`;
  marker.style.top = `${memory.y}%`;
  marker.setAttribute("aria-label", `Abrir recuerdo: ${memory.title}, ${memory.place}`);
  marker.innerHTML = `<span class="marker-label">${memory.place.split(",")[0]}</span>`;
  marker.addEventListener("click", () => selectMemory(memory.id));
  elements.markers.appendChild(marker);
});

elements.filters.addEventListener("click", event => {
  const button = event.target.closest(".filter");
  if (button) setFilter(button.dataset.filter);
});
elements.search.addEventListener("input", event => {
  state.query = event.target.value.trim();
  if (state.selected && !matches(memories.find(item => item.id === state.selected))) selectMemory(null, false);
  renderMarkers(); updateUrl();
});
document.querySelector("#close-card").addEventListener("click", () => selectMemory(null));
document.querySelector("#clear-search").addEventListener("click", resetAll);
document.querySelector("#reset-view").addEventListener("click", resetAll);
document.querySelector("#next-memory").addEventListener("click", () => {
  const visible = memories.filter(matches);
  const current = visible.findIndex(memory => memory.id === state.selected);
  selectMemory(visible[(current + 1) % visible.length]?.id);
});
document.addEventListener("keydown", event => {
  if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") { event.preventDefault(); elements.search.focus(); }
  if (event.key === "Escape") selectMemory(null);
});

const initial = new URLSearchParams(location.search);
state.query = initial.get("q") || "";
elements.search.value = state.query;
setFilter(initial.get("filter") || "all", false);
selectMemory(initial.get("memory"), false);
document.body.dataset.ready = "true";