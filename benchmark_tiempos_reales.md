# Benchmark Empírico de Cronograma - Torneo Zona Sur CC 2026

Este documento almacena los muestreos en tiempo real tomados en alberca para calibrar y evaluar los modelos de predicción de horarios de natación.

---

## 1. Calibración de Overheads en el Algoritmo (v1.6)

* **50m (Libre, Pecho, Mariposa):** **8 segundos** (salidas rápidas *over-the-top* con nadadores en el agua).
* **50m Dorso:** **12 segundos** (tiempo adicional para entrada al agua y sujeción en agarraderas).
* **100m (Todos los estilos):** **15 segundos** (desalojo de carriles y colocación).
* **200m, 400m, 800m, 1500m:** **15 segundos** (ritmo probado con error < 2%).
* **Descanso cambio de evento (mismo estilo):** **15 segundos**.
* **Descanso cambio de estilo:** **20 segundos**.
* **Protección contra saltos de página:** Si un heat tiene 0 nadadores (encabezado huérfano por salto de página), se ignora y no suma tiempo fantasma.

---

## 2. Muestreo Sesión 4 (Domingo 11 Octubre 2026 - Vespertina)
*Características:* Pruebas de 100m, 200m y 800m. Sesión limpia (sin eventos fusionados).
*Hora de inicio real:* 13:50

| Evento | Serie | Hora Real | Cadencia Observada |
| :--- | :---: | :---: | :--- |
| **E33** (200m Dorso Fem) | 1 | 13:50 | 3.0 min / serie (180s) |
| | 2 | 13:53 | |
| **E34** (200m Dorso Var) | 2 | 14:15 | 3.0 min / serie (180s) |
| | 3 | 14:18 | |
| **E35** (100m Mariposa Fem) | 1 | 14:26 | 2.0 min / serie en series NT (120s) |
| | 2 | 14:28 | |
| | 3 | 14:29 | |
| | 6 | 14:35 | |
| | 9 | 14:41 | |
| **E36** (100m Mariposa Var) | 1 | 14:44 | Series rápidas: 1.25 min / serie (75s)<br>Series NT: 2.0 min / serie (120s) |
| | 5 | 14:49 | |
| | 6 | 14:50 | *(Ian nadó aquí)* |
| | 8 | 14:54 | |
| | 10 | 14:58 | |
| | 12 | 15:02 | |
| | 13 | 15:04 | |
| | 14 | 15:06 | |
| **E37** (200m Pecho Fem) | 1 | 15:07 | 3.33 min / serie (200s) |
| | 4 | 15:17 | |
| **E38** (200m Pecho Var) | 1 | 15:35 | 3.25 min / serie (195s) |
| | 2 | 15:38 | |
| | 4 | 15:45 | |
| **E39** (800m Libre Fem) | 1 | 15:58 *(est)* | Serie 1: 11 min<br>Serie 2: 14 min |
| | 2 | 16:09 | |
| | 3 | 16:23 | |
| **E40** (800m Libre Var) | 1 | 16:36 | 11.0 min / serie |
| | 2 | 16:47 | |

---

## 3. Muestreo Sesión 2 (Domingo 11 Octubre 2026 - Matutina)
*Características:* 400m C.I., 50m Mariposa, 100m Libre, 50m Dorso.
*Observaciones:* Fusión en vivo de los Eventos 25 y 26 (25m) al inicio.

| Evento | Serie | Hora Real | Cadencia Observada |
| :--- | :---: | :---: | :--- |
| **E23** (400m C.I. Fem) | 1 | 09:03 | 7 min / serie |
| | 2 | 09:10 | |
| **E24** (400m C.I. Var) | 1 | 09:17 | 6 min / serie |
| | 2 | 09:23 | |
| | 3 | 09:29 | |
| **E27** (50m Mariposa Fem) | 2 | 09:47 | **60.0 s / serie** (1 min/serie exacto) |
| | 3, 4, 5, 6 | 09:48, 09:49, 09:50, 09:51 | |
| | 8, 10, 13, 18 | 09:54, 09:55, 09:57, 10:03 | |
| **E28** (50m Mariposa Var) | 2, 3 | 10:08, 10:09 | **57.6 s / serie** (< 1 min/serie) |
| | 5, 6, 9, 10 | 10:11, 10:11, 10:14, 10:14 | |
| | 15, 16, 20-24 | 10:19, 10:20, 10:24-10:28 | |
| | 26, 27 | 10:30, 10:32 | |
| **E29** (100m Libre Fem) | 1, 2, 4 | 10:33, 10:34, 10:37 | **96.0 s / serie** (1:36 min/serie) |
| | 7, 8, 12 | 10:41, 10:43, 10:49 | |
| | 15, 17, 21 | 10:55, 10:59, 11:05 | |
| **E30** (100m Libre Var) | 1, 2, 6 | 11:08, 11:09, 11:14 | **91.1 s / serie** (1:31 min/serie) |
| | 14, 16, 19, 20 | 11:25, 11:28, 11:33, 11:35 | |
| | 22, 28 | 11:39, 11:49 | |
| **E31** (50m Dorso Fem) | 1, 2, 4-7 | 11:52, 11:53, 11:54-11:58 | **76.7 s / serie** (1:17 min/serie) |
| | 12, 15, 19 | 12:05, 12:10, 12:15 | |
| **E32** (50m Dorso Var) | 1, 2, 3, 6 | 12:17, 12:18, 12:19, 12:22 | **63.8 s / serie** (1:04 min/serie) |
| | 10, 17 | 12:25, 12:34 | |

---

## 4. Muestreo Sesión 1 (Sábado 10 Octubre 2026 - Matutina)
*Características:* Sesión masiva con 400m Libre, 50m Pecho, 200m C.I., 50m Libre y 100m Dorso.
*Observaciones:* Fusión de los Eventos 3 y 4 (25m Pecho) y cadencia extrema de 45s en 50m Libre.

| Evento | Serie | Hora Real | Cadencia Observada |
| :--- | :---: | :---: | :--- |
| **E5** (50m Pecho Fem) | 5, 9, 10 | 10:43, 10:48, 10:50 | 81.8 s / serie (1:22 min/serie con series NT) |
| | 14, 16 | 10:55, 10:58 | |
| **E6** (50m Pecho Var) | 1, 4, 5, 6 | 10:59, 11:02, 11:03, 11:04 | **60.0 s / serie** (1 min/serie) |
| **E8** (200m C.I. Var) | 3, 4 | 12:04, 12:07 | 3.43 min / serie (206s/serie) |
| | 8, 9, 10 | 12:20, 12:24, 12:28 | |
| **E9** (50m Libre Fem) | 2, 4, 7, 20 | 12:37, 12:39, 12:42, 12:53 | **53.3 s / serie** |
| **E10** (50m Libre Var) | 1, 10, 12, 13 | 12:57, 13:04, 13:05, 13:06 | **45.0 s / serie** *(rotación récord en 50 libre)* |
| **E11** (100m Dorso Fem) | 1 | 13:21 | Inicio de dorso |
