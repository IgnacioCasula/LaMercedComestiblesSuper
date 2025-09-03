// app.js

document.addEventListener("DOMContentLoaded", function () {
    // Constantes y utilidades
    const diasES = ["Domingo","Lunes","Martes","Miércoles","Jueves","Viernes","Sábado"];
    const two = n => String(n).padStart(2, "0");
  
    function formatTime(date = new Date()) {
      const h = two(date.getHours());
      const m = two(date.getMinutes());
      const s = two(date.getSeconds());
      return `${h}:${m}:${s}`;
    }
  
    function formatDate(date = new Date()) {
      const d = two(date.getDate());
      const m = two(date.getMonth() + 1);
      const y = date.getFullYear();
      return `${d}/${m}/${y}`;
    }
  
    // ISO week number
    function getISOWeek(date = new Date()) {
      const d = new Date(Date.UTC(date.getFullYear(), date.getMonth(), date.getDate()));
      const dayNum = d.getUTCDay() || 7;
      d.setUTCDate(d.getUTCDate() + 4 - dayNum);
      const yearStart = new Date(Date.UTC(d.getUTCFullYear(), 0, 1));
      const weekNo = Math.ceil((((d - yearStart) / 86400000) + 1) / 7);
      return { week: weekNo, year: d.getUTCFullYear() };
    }
  
    // Storage key por semana
    function storageKey() {
      const { week, year } = getISOWeek(new Date());
      return `asistencia:${year}-W${week}`;
    }
  
    function defaultWeekData() {
      return [
        { dia: "Lunes", entrada: "", salida: "" },
        { dia: "Martes", entrada: "", salida: "" },
        { dia: "Miércoles", entrada: "", salida: "" },
        { dia: "Jueves", entrada: "", salida: "" },
        { dia: "Viernes", entrada: "", salida: "" },
        { dia: "Sábado", entrada: "", salida: "" },
        { dia: "Domingo", entrada: "", salida: "" },
      ];
    }
  
    function loadWeek() {
      const raw = localStorage.getItem(storageKey());
      return raw ? JSON.parse(raw) : defaultWeekData();
    }
  
    function saveWeek(data) {
      localStorage.setItem(storageKey(), JSON.stringify(data));
    }
  
    // Elementos DOM
    const viewHome   = document.getElementById("view-home");
    const viewLog    = document.getElementById("view-log");
    const tablaBody  = document.getElementById("tabla-registro");
    const weekLabel  = document.getElementById("week-label");
    const nowDateEl  = document.getElementById("now-date");
    const nowTimeEl  = document.getElementById("now-time");
  
    const btnEntrada = document.getElementById("btn-entrada");
    const btnSalida  = document.getElementById("btn-salida");
    const btnRegistro= document.getElementById("btn-registro");
    const btnVolver  = document.getElementById("btn-volver");
  
    // Renderizar tabla
    function renderTable() {
      const data = loadWeek();
      tablaBody.innerHTML = "";
      for (const item of data) {
        const tr = document.createElement("tr");
        tr.innerHTML = `
          <td class="fw-semibold">${item.dia}</td>
          <td>${item.entrada || ""}</td>
          <td>${item.salida || ""}</td>
        `;
        tablaBody.appendChild(tr);
      }
    }
  
    function updateHeaderInfo() {
    const { week, year } = getISOWeek(new Date());
    weekLabel.textContent = `número ${week} del año ${year}`;
  }
  
    // Día actual en español (nombre usado en la tabla)
    function diaDeHoyES() {
      return diasES[new Date().getDay()];
    }
  
    // Acciones Entrada / Salida
    function registrarEntrada() {
      const data = loadWeek();
      const hoy = diaDeHoyES();
      const hora = formatTime();
  
      const row = data.find(r => r.dia === hoy);
      if (row) {
        row.entrada = hora; // sobrescribe la entrada
        saveWeek(data);
        renderTable();
        alert("Entrada registrada correctamente");
      } else {
        alert("No se pudo registrar la entrada (día no encontrado).");
      }
    }
  
    function registrarSalida() {
      const data = loadWeek();
      const hoy = diaDeHoyES();
      const hora = formatTime();
  
      const row = data.find(r => r.dia === hoy);
      if (row) {
        row.salida = hora; // se coloca solo al pulsar SALIDA
        saveWeek(data);
        renderTable();
        alert("Salida registrada correctamente");
      } else {
        alert("No se pudo registrar la salida (día no encontrado).");
      }
    }
  
    // Navegación de vistas
    function showHome() {
      viewLog.classList.add("hidden");
      viewHome.classList.remove("hidden");
    }
  
    function showLog() {
      renderTable();
      updateHeaderInfo();
      viewHome.classList.add("hidden");
      viewLog.classList.remove("hidden");
    }
  
    // Reloj en vivo
    function tickNow() {
      nowDateEl.textContent = formatDate();
      nowTimeEl.textContent = formatTime();
    }
  
    // Eventos
    btnEntrada.addEventListener("click", registrarEntrada);
    btnSalida .addEventListener("click", registrarSalida);
    btnRegistro.addEventListener("click", showLog);
    btnVolver  .addEventListener("click", showHome);
  
    // Init
    renderTable();
    updateHeaderInfo();
    tickNow();
    setInterval(tickNow, 1000);
  });
  