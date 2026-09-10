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
    private const val VERSION_DATOS = 1

    private var archivo: File? = null

    val gastos = mutableStateListOf<Gasto>()
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
        gastos.clear()
        categorias.clear()
        ajustes = Ajustes()
        inicializar(contexto)
    }

    // ─────────────────────────────  Gastos  ─────────────────────────────

    fun agregarGasto(gasto: Gasto) {
        gastos.add(gasto)
        ordenarGastos()
        guardar()
    }

    fun actualizarGasto(gasto: Gasto) {
        val indice = gastos.indexOfFirst { it.id == gasto.id }
        if (indice >= 0) gastos[indice] = gasto else gastos.add(gasto)
        ordenarGastos()
        guardar()
    }

    fun eliminarGasto(id: String) {
        if (gastos.removeAll { it.id == id }) guardar()
    }

    // ───────────────────────────  Categorías  ───────────────────────────

    fun guardarCategoria(categoria: Categoria) {
        val indice = categorias.indexOfFirst { it.id == categoria.id }
        if (indice >= 0) categorias[indice] = categoria else categorias.add(categoria)
        guardar()
    }

    /** Borra la categoría y manda sus gastos a "Otros" para no perder historial. */
    fun eliminarCategoria(id: String) {
        if (id == ID_CATEGORIA_OTROS) return
        if (categorias.none { it.id == ID_CATEGORIA_OTROS }) {
            categorias.add(CATEGORIAS_INICIALES.first { it.id == ID_CATEGORIA_OTROS })
        }
        for (i in gastos.indices) {
            if (gastos[i].categoriaId == id) {
                gastos[i] = gastos[i].copy(categoriaId = ID_CATEGORIA_OTROS)
            }
        }
        categorias.removeAll { it.id == id }
        guardar()
    }

    fun categoria(id: String): Categoria? = categorias.firstOrNull { it.id == id }

    fun categoriaODefecto(id: String): Categoria =
        categoria(id) ?: categorias.firstOrNull { it.id == ID_CATEGORIA_OTROS }
        ?: Categoria(ID_CATEGORIA_OTROS, "Sin categoría", "📦", 0xFF78909C)

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

    fun borrarTodosLosGastos() {
        gastos.clear()
        guardar()
    }

    // ────────────────────────────  Consultas  ───────────────────────────

    fun gastosDe(mes: YearMonth): List<Gasto> = gastos.filter { it.mes == mes }

    fun totalDe(mes: YearMonth): Long = gastosDe(mes).sumOf { it.monto }

    /** Meses que tienen al menos un gasto, del más nuevo al más antiguo. */
    fun mesesConGastos(): List<YearMonth> =
        gastos.map { it.mes }.distinct().sortedDescending()

    /** Totales por categoría de un periodo, ordenados de mayor a menor. */
    fun totalesPorCategoria(gastosDelPeriodo: List<Gasto>): List<TotalCategoria> {
        val total = gastosDelPeriodo.sumOf { it.monto }.toFloat()
        return gastosDelPeriodo
            .groupBy { it.categoriaId }
            .map { (idCategoria, lista) ->
                val suma = lista.sumOf { it.monto }
                TotalCategoria(
                    categoria = categoriaODefecto(idCategoria),
                    total = suma,
                    cantidad = lista.size,
                    porcentaje = if (total <= 0f) 0f else suma / total
                )
            }
            .sortedByDescending { it.total }
    }

    /** Gasto total del día indicado. */
    fun totalDelDia(dia: LocalDate): Long = gastos.filter { it.fecha == dia }.sumOf { it.monto }

    // ────────────────────────────  CSV  ─────────────────────────────────

    fun exportarCsv(): String = buildString {
        appendLine("fecha;categoria;monto;metodo;nota")
        gastos.sortedWith(compareBy({ it.fecha }, { it.creado })).forEach { gasto ->
            val categoria = categoriaODefecto(gasto.categoriaId).nombre
            val nota = gasto.nota.replace(";", ",").replace("\n", " ")
            appendLine("${gasto.fecha};$categoria;${gasto.monto};${gasto.metodo.etiqueta};$nota")
        }
    }

    // ─────────────────────────  Persistencia  ───────────────────────────

    private fun ordenarGastos() {
        val ordenados = gastos.sortedWith(
            compareByDescending<Gasto> { it.fecha }.thenByDescending { it.creado }
        )
        gastos.clear()
        gastos.addAll(ordenados)
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
                    })
                }
            })
            put("gastos", JSONArray().apply {
                gastos.forEach { gasto ->
                    put(JSONObject().apply {
                        put("id", gasto.id)
                        put("monto", gasto.monto)
                        put("categoriaId", gasto.categoriaId)
                        put("fecha", gasto.fecha.toString())
                        put("nota", gasto.nota)
                        put("metodo", gasto.metodo.name)
                        put("creado", gasto.creado)
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
                        presupuesto = item.optLong("presupuesto", 0L)
                    )
                )
            }
        }

        gastos.clear()
        val gastosJson = raiz.optJSONArray("gastos") ?: JSONArray()
        for (i in 0 until gastosJson.length()) {
            val item = gastosJson.getJSONObject(i)
            val fecha = runCatching { LocalDate.parse(item.optString("fecha")) }
                .getOrDefault(LocalDate.now())
            gastos.add(
                Gasto(
                    id = item.optString("id"),
                    monto = item.optLong("monto"),
                    categoriaId = item.optString("categoriaId", ID_CATEGORIA_OTROS),
                    fecha = fecha,
                    nota = item.optString("nota"),
                    metodo = MetodoPago.desde(item.optString("metodo")),
                    creado = item.optLong("creado", System.currentTimeMillis())
                )
            )
        }
        ordenarGastos()
    }
}
