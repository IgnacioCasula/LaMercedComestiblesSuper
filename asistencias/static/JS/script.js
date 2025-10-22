// Elementos
const btnRegistro = document.getElementById("btnRegistro");
const btnVolver = document.getElementById("btnVolver");
const mainScreen = document.getElementById("mainScreen");
const registroScreen = document.getElementById("registroScreen");
const currentDateTime = document.getElementById("currentDateTime");
const weekInfo = document.getElementById("weekInfo");

// Mostrar fecha y hora actual en inicio
function updateDateTime() {
  const now = new Date();
  const options = { day: '2-digit', month: '2-digit', year: 'numeric' };
  const date = now.toLocaleDateString("es-ES", options);
  const time = now.toLocaleTimeString("es-ES");
  currentDateTime.textContent = `${date} - ${time}`;
}
setInterval(updateDateTime, 1000);
updateDateTime();

// Calcular semana ISO
function getISOWeek(date) {
  const tempDate = new Date(date.valueOf());
  const dayNumber = (date.getDay() + 6) % 7;
  tempDate.setDate(tempDate.getDate() - dayNumber + 3);
  const firstThursday = tempDate.valueOf();
  tempDate.setMonth(0, 1);
  if (tempDate.getDay() !== 4) {
    tempDate.setMonth(0, 1 + ((4 - tempDate.getDay()) + 7) % 7);
  }
  const week = 1 + Math.ceil((firstThursday - tempDate) / 604800000);
  return { week, year: date.getFullYear() };
}

// Actualizar encabezado en pantalla de registro
function updateHeaderInfo() {
  const { week, year } = getISOWeek(new Date());
  weekInfo.textContent = `Semana número ${week} del año ${year}`;
}

// Botón Registro
btnRegistro.addEventListener("click", () => {
  mainScreen.classList.add("d-none");
  registroScreen.classList.remove("d-none");
  updateHeaderInfo();
});

// Botón Volver
btnVolver.addEventListener("click", () => {
  registroScreen.classList.add("d-none");
  mainScreen.classList.remove("d-none");
});
