package cl.augustogames.gastos.data

import android.content.Context
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.mutableStateListOf
import androidx.compose.runtime.setValue
import org.json.JSONArray
import org.json.JSONObject
import java.io.File
import java.time.LocalDate
import java.time.YearMonth

/**
 * Única fuente de datos de la app.
 *
 * Todo vive en memoria como estado de Compose (así la interfaz se actualiza sola)
 * y se persiste en un archivo JSON dentro del almacenamiento privado de la app,
 * por lo que no se necesita ningún permiso ni conexión a internet.
 */
object Repositorio {

    private const val NOMBRE_ARCHIVO = "mis-gastos.json"

    /** 1: solo gastos (app 1.0) · 2: gastos e ingresos (app 1.1). */
    private const val VERSION_DATOS = 2

    private var archivo: File? = null

    val movimientos = mutableStateListOf<Movimiento>()
    val categorias = mutableStateListOf<Categoria>()

    var ajustes by mutableStateOf(Ajustes())
        private set

    fun inicializar(contexto: Context) {
        if (archivo != null) return
        val destino = File(contexto.filesDir, NOMBRE_ARCHIVO)
        archivo = destino
        if (destino.exists()) {
            runCatching { leer(JSONObject(destino.readText())) }
                .onFailure { sembrarCategorias() }
        } else {
            sembrarCategorias()
            guardar()
        }
    }

    /** Deja el repositorio como recién abierto; se usa en las pruebas. */
    internal fun reiniciar(contexto: Context) {
        archivo = null
        movimientos.clear()
        categorias.clear()
        ajustes = Ajustes()
        inicializar(contexto)
    }

    // ───────────────────────────  Movimientos  ──────────────────────────

    fun agregarMovimiento(movimiento: Movimiento) {
        movimientos.add(movimiento)
        ordenarMovimientos()
        guardar()
    }

    fun actualizarMovimiento(movimiento: Movimiento) {
        val indice = movimientos.indexOfFirst { it.id == movimiento.id }
        if (indice >= 0) movimientos[indice] = movimiento else movimientos.add(movimiento)
        ordenarMovimientos()
        guardar()
    }

    fun eliminarMovimiento(id: String) {
        if (movimientos.removeAll { it.id == id }) guardar()
    }

    fun borrarTodosLosMovimientos() {
        movimientos.clear()
        guardar()
    }

    // ───────────────────────────  Categorías  ───────────────────────────

    fun categoriasDe(tipo: TipoMovimiento): List<Categoria> = categorias.filter { it.tipo == tipo }

    fun guardarCategoria(categoria: Categoria) {
        val indice = categorias.indexOfFirst { it.id == categoria.id }
        if (indice >= 0) categorias[indice] = categoria else categorias.add(categoria)
        guardar()
    }

    /**
     * Borra la categoría y manda sus movimientos a la categoría comodín de su mismo tipo
     * ("Otros" o "Otros ingresos") para no perder historial.
     */
    fun eliminarCategoria(id: String) {
        val categoria = categoria(id) ?: return
        val comodin = idCategoriaComodin(categoria.tipo)
        if (id == comodin) return
        if (categorias.none { it.id == comodin }) {
            CATEGORIAS_INICIALES.firstOrNull { it.id == comodin }?.let { categorias.add(it) }
        }
        for (i in movimientos.indices) {
            if (movimientos[i].categoriaId == id) {
                movimientos[i] = movimientos[i].copy(categoriaId = comodin)
            }
        }
        categorias.removeAll { it.id == id }
        guardar()
    }

    fun categoria(id: String): Categoria? = categorias.firstOrNull { it.id == id }

    fun categoriaODefecto(id: String, tipo: TipoMovimiento = TipoMovimiento.GASTO): Categoria =
        categoria(id)
            ?: categoria(idCategoriaComodin(tipo))
            ?: Categoria(idCategoriaComodin(tipo), "Sin categoría", "📦", 0xFF78909C, tipo = tipo)

    fun restablecerCategorias() {
        val existentes = categorias.map { it.id }.toSet()
        CATEGORIAS_INICIALES.filterNot { it.id in existentes }.forEach { categorias.add(it) }
        guardar()
    }

    // ────────────────────────────  Ajustes  ─────────────────────────────

    fun actualizarAjustes(nuevos: Ajustes) {
        ajustes = nuevos
        guardar()
    }

    // ────────────────────────────  Consultas  ───────────────────────────

    fun movimientosDe(mes: YearMonth): List<Movimiento> = movimientos.filter { it.mes == mes }

    fun gastosDe(mes: YearMonth): List<Movimiento> =
        movimientos.filter { it.mes == mes && it.tipo == TipoMovimiento.GASTO }

    fun ingresosDe(mes: YearMonth): List<Movimiento> =
        movimientos.filter { it.mes == mes && it.tipo == TipoMovimiento.INGRESO }

    fun totalDe(mes: YearMonth, tipo: TipoMovimiento): Long =
        movimientos.filter { it.mes == mes && it.tipo == tipo }.sumOf { it.monto }

    fun balanceDe(mes: YearMonth): BalanceMes = BalanceMes(
        ingresos = totalDe(mes, TipoMovimiento.INGRESO),
        gastos = totalDe(mes, TipoMovimiento.GASTO)
    )

    /** Meses que tienen al menos un movimiento, del más nuevo al más antiguo. */
    fun mesesConMovimientos(): List<YearMonth> =
        movimientos.map { it.mes }.distinct().sortedDescending()

    /** Totales por categoría de un periodo, ordenados de mayor a menor. */
    fun totalesPorCategoria(periodo: List<Movimiento>): List<TotalCategoria> {
        val total = periodo.sumOf { it.monto }.toFloat()
        return periodo
            .groupBy { it.categoriaId }
            .map { (idCategoria, lista) ->
                val suma = lista.sumOf { it.monto }
                TotalCategoria(
                    categoria = categoriaODefecto(idCategoria, lista.first().tipo),
                    total = suma,
                    cantidad = lista.size,
                    porcentaje = if (total <= 0f) 0f else suma / total
                )
            }
            .sortedByDescending { it.total }
    }

    /** Total gastado el día indicado. */
    fun gastoDelDia(dia: LocalDate): Long =
        movimientos.filter { it.fecha == dia && it.tipo == TipoMovimiento.GASTO }.sumOf { it.monto }

    // ────────────────────────────  CSV  ─────────────────────────────────

    fun exportarCsv(): String = buildString {
        appendLine("fecha;tipo;categoria;monto;metodo;nota")
        movimientos.sortedWith(compareBy({ it.fecha }, { it.creado })).forEach { movimiento ->
            val categoria = categoriaODefecto(movimiento.categoriaId, movimiento.tipo).nombre
            val nota = movimiento.nota.replace(";", ",").replace("\n", " ")
            appendLine(
                "${movimiento.fecha};${movimiento.tipo.etiqueta};$categoria;" +
                    "${movimiento.monto};${movimiento.metodo.etiqueta};$nota"
            )
        }
    }

    // ─────────────────────────  Persistencia  ───────────────────────────

    private fun ordenarMovimientos() {
        val ordenados = movimientos.sortedWith(
            compareByDescending<Movimiento> { it.fecha }.thenByDescending { it.creado }
        )
        movimientos.clear()
        movimientos.addAll(ordenados)
    }

    private fun sembrarCategorias() {
        categorias.clear()
        categorias.addAll(CATEGORIAS_INICIALES)
    }

    private fun guardar() {
        val destino = archivo ?: return
        val raiz = JSONObject().apply {
            put("version", VERSION_DATOS)
            put("ajustes", JSONObject().apply {
                put("simbolo", ajustes.simbolo)
                put("tema", ajustes.tema.name)
            })
            put("categorias", JSONArray().apply {
                categorias.forEach { categoria ->
                    put(JSONObject().apply {
                        put("id", categoria.id)
                        put("nombre", categoria.nombre)
                        put("emoji", categoria.emoji)
                        put("color", categoria.color)
                        put("presupuesto", categoria.presupuesto)
                        put("tipo", categoria.tipo.name)
                    })
                }
            })
            put("movimientos", JSONArray().apply {
                movimientos.forEach { movimiento ->
                    put(JSONObject().apply {
                        put("id", movimiento.id)
                        put("monto", movimiento.monto)
                        put("categoriaId", movimiento.categoriaId)
                        put("fecha", movimiento.fecha.toString())
                        put("nota", movimiento.nota)
                        put("metodo", movimiento.metodo.name)
                        put("tipo", movimiento.tipo.name)
                        put("creado", movimiento.creado)
                    })
                }
            })
        }
        runCatching { destino.writeText(raiz.toString()) }
    }

    private fun leer(raiz: JSONObject) {
        val ajustesJson = raiz.optJSONObject("ajustes")
        ajustes = Ajustes(
            simbolo = ajustesJson?.optString("simbolo", "$")?.ifBlank { "$" } ?: "$",
            tema = Tema.desde(ajustesJson?.optString("tema"))
        )

        categorias.clear()
        val categoriasJson = raiz.optJSONArray("categorias")
        if (categoriasJson == null || categoriasJson.length() == 0) {
            categorias.addAll(CATEGORIAS_INICIALES)
        } else {
            for (i in 0 until categoriasJson.length()) {
                val item = categoriasJson.getJSONObject(i)
                categorias.add(
                    Categoria(
                        id = item.optString("id"),
                        nombre = item.optString("nombre"),
                        emoji = item.optString("emoji", "📦"),
                        color = item.optLong("color", 0xFF78909C),
                        presupuesto = item.optLong("presupuesto", 0L),
                        // Los archivos de la versión 1.0 no traen tipo: eran todos gastos.
                        tipo = TipoMovimiento.desde(item.optString("tipo"))
                    )
                )
            }
            // Al actualizar desde la 1.0 no existían las categorías de ingreso.
            if (categorias.none { it.tipo == TipoMovimiento.INGRESO }) {
                categorias.addAll(CATEGORIAS_INGRESO_INICIALES)
            }
        }

        movimientos.clear()
        // "gastos" es el nombre que usaba la versión 1.0 del archivo.
        val movimientosJson = raiz.optJSONArray("movimientos")
            ?: raiz.optJSONArray("gastos")
            ?: JSONArray()
        for (i in 0 until movimientosJson.length()) {
            val item = movimientosJson.getJSONObject(i)
            val tipo = TipoMovimiento.desde(item.optString("tipo"))
            val fecha = runCatching { LocalDate.parse(item.optString("fecha")) }
                .getOrDefault(LocalDate.now())
            movimientos.add(
                Movimiento(
                    id = item.optString("id"),
                    monto = item.optLong("monto"),
                    categoriaId = item.optString("categoriaId", idCategoriaComodin(tipo)),
                    fecha = fecha,
                    nota = item.optString("nota"),
                    metodo = MetodoPago.desde(item.optString("metodo")),
                    tipo = tipo,
                    creado = item.optLong("creado", System.currentTimeMillis())
                )
            )
        }
        ordenarMovimientos()
    }
}
