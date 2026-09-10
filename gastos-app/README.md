# Mis Gastos — app Android para registrar gastos por categoría

App nativa (Kotlin + Jetpack Compose) para anotar en qué se te va la plata:
alimentación, bencina, deudas, arriendo, servicios y las categorías que quieras crear.

**Descarga directa del APK:** [augustogames.cl/mis-gastos.apk](https://augustogames.cl/mis-gastos.apk)
(o el archivo `mis-gastos.apk` en la raíz de este repositorio).

## Qué hace

- **Registro rápido**: monto con separador de miles, categoría, fecha (Hoy / Ayer / calendario),
  forma de pago (efectivo, débito, crédito, transferencia) y un detalle opcional.
  Botones de montos rápidos (+1.000, +5.000, …) para no escribir tanto.
- **Resumen mensual**: total del mes, anillo con la repartición por categoría, comparación con
  el mes anterior, gasto de hoy y promedio por día.
- **Presupuestos**: tope mensual por categoría y barra de avance que se pone roja al pasarse.
- **Historial**: gastos agrupados por día, con buscador y filtro por categoría. Se toca un gasto
  para editarlo o borrarlo.
- **Categorías propias**: nombre, emoji, color y tope. Al borrar una, sus gastos pasan a "Otros"
  para no perder historial.
- **Exportar a CSV** desde Ajustes (se comparte por WhatsApp, mail, Drive, lo que sea).
- **Tema claro / oscuro / según el sistema** y símbolo de moneda configurable.

Todo se guarda en un archivo JSON dentro del almacenamiento privado de la app:
**sin permisos, sin cuentas y sin internet**.

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
│   ├── Modelos.kt               Gasto, Categoría, Ajustes y categorías iniciales
│   └── Repositorio.kt           estado en memoria + guardado en JSON + consultas
└── ui/
    ├── App.kt                   navegación (Resumen · Gastos · Categorías · Ajustes)
    ├── Formato.kt               montos y fechas en español
    ├── theme/Tema.kt            paleta clara y oscura
    ├── componentes/             gráfico de dona, formulario, campos y piezas reutilizables
    └── pantallas/               las cuatro pantallas
```

Las pruebas viven en `app/src/test/` y cubren el formateo, el repositorio (totales,
persistencia, borrado de categorías, CSV) y un arranque real de la app con Robolectric.
