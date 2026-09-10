# Mis Gastos — app Android para registrar gastos e ingresos

App nativa (Kotlin + Jetpack Compose) para anotar en qué se te va la plata y cuánta entra:
alimentación, bencina, deudas, arriendo, servicios, sueldo, trabajos extra y las categorías
que quieras crear.

**Versión actual: 1.1** · [Descarga directa del APK](https://augustogames.cl/mis-gastos.apk)
(o el archivo `mis-gastos.apk` en la raíz de este repositorio).

## Qué hace

- **Gastos e ingresos**: cada movimiento se registra como gasto o ingreso con un botón
  al principio del formulario. El botón 💰 del inicio abre directo un ingreso.
- **Registro rápido**: monto con separador de miles, categoría, fecha (Hoy / Ayer / calendario),
  forma de pago (efectivo, débito, crédito, transferencia) y un detalle opcional.
  Botones de montos rápidos (+1.000, +5.000, …) para no escribir tanto.
- **Resumen mensual**: anillo con la repartición de los gastos, total de ingresos, cuánto
  te queda (o cuánto te falta), qué porcentaje de lo que entró llevas gastado, comparación
  con el mes anterior, gasto de hoy y promedio por día.
- **Presupuestos y metas**: tope mensual por categoría de gasto, con barra que se pone roja
  al pasarse; meta mensual por categoría de ingreso, que se pone verde al alcanzarla.
- **Historial**: movimientos agrupados por día con filtro Todo / Gastos / Ingresos, buscador
  y filtro por categoría. Se toca uno para editarlo, cambiarlo de tipo o borrarlo.
- **Categorías propias** separadas por tipo: nombre, emoji, color y tope. Al borrar una, sus
  movimientos pasan a "Otros" (o a "Otros ingresos") para no perder historial.
- **Exportar a CSV** desde Ajustes, con una columna que distingue gastos de ingresos.
- **Tema claro / oscuro / según el sistema** y símbolo de moneda configurable.

Todo se guarda en un archivo JSON dentro del almacenamiento privado de la app:
**sin permisos, sin cuentas y sin internet**.

### Actualizar desde la 1.0

Se instala encima sin desinstalar nada: los gastos, las categorías y los presupuestos que ya
tenías se conservan, y se agregan las categorías de ingreso. La migración del formato antiguo
está cubierta por una prueba automática.

## Instalar el APK en el teléfono

1. Descarga `mis-gastos.apk` desde el teléfono.
2. Ábrelo. Android va a pedir permiso para "instalar apps desconocidas" desde el navegador:
   actívalo y vuelve atrás.
3. Instalar → listo. La app aparece como **Mis Gastos**.

Requiere Android 8.0 (API 26) o superior.

## Compilar desde el código

```bash
cd gastos-app
./gradlew assembleRelease      # APK en app/build/outputs/apk/release/
./gradlew testDebugUnitTest    # pruebas (lógica de datos + interfaz con Robolectric)
```

Necesitas JDK 17+ y el SDK de Android 35. Si Gradle no encuentra el SDK, crea
`gastos-app/local.properties` con `sdk.dir=/ruta/al/android-sdk`.

### Firmar con tu propia llave

Por defecto el APK de release se firma con la clave de depuración, que sirve para instalarlo
a mano. Para firmarlo con una llave propia, define estas variables antes de compilar:

```bash
export KEYSTORE_FILE=/ruta/mi-llave.jks
export KEYSTORE_PASSWORD=...
export KEY_ALIAS=...
export KEY_PASSWORD=...
./gradlew assembleRelease
```

> Ojo: si cambias la firma, hay que desinstalar la versión anterior antes de instalar la nueva.

## Estructura

```
gastos-app/app/src/main/java/cl/augustogames/gastos/
├── MainActivity.kt              punto de entrada
├── data/
│   ├── Modelos.kt               Movimiento, Categoría, Ajustes y categorías iniciales
│   └── Repositorio.kt           estado en memoria + guardado en JSON + consultas
└── ui/
    ├── App.kt                   navegación (Resumen · Historial · Categorías · Ajustes)
    ├── Formato.kt               montos y fechas en español
    ├── theme/Tema.kt            paleta clara y oscura
    ├── componentes/             gráfico de dona, formulario, campos y piezas reutilizables
    └── pantallas/               las cuatro pantallas
```

Las pruebas viven en `app/src/test/` y cubren el formateo, el repositorio (balance mensual,
totales por categoría, persistencia, migración desde el formato 1.0, borrado de categorías,
CSV) y un arranque real de la app con Robolectric.

## Formato de datos

El archivo `mis-gastos.json` guarda `version: 2`:

```json
{
  "version": 2,
  "ajustes": { "simbolo": "$", "tema": "SISTEMA" },
  "categorias": [
    { "id": "sueldo", "nombre": "Sueldo", "emoji": "💼", "color": 4281306715,
      "presupuesto": 0, "tipo": "INGRESO" }
  ],
  "movimientos": [
    { "id": "…", "monto": 850000, "categoriaId": "sueldo", "fecha": "2026-09-05",
      "nota": "", "metodo": "TRANSFERENCIA", "tipo": "INGRESO", "creado": 1757500000000 }
  ]
}
```

Los archivos de la versión 1 (lista `gastos`, sin `tipo`) se leen igual y se guardan
en el formato nuevo al primer cambio.
