package cl.augustogames.gastos.data

import java.time.LocalDate
import java.time.YearMonth
import java.util.UUID

/** Un movimiento puede ser plata que sale (gasto) o que entra (ingreso). */
enum class TipoMovimiento(val etiqueta: String, val plural: String) {
    GASTO("Gasto", "Gastos"),
    INGRESO("Ingreso", "Ingresos");

    companion object {
        fun desde(nombre: String?): TipoMovimiento =
            entries.firstOrNull { it.name == nombre } ?: GASTO
    }
}

/** Forma en que se pagó un gasto o se recibió un ingreso. */
enum class MetodoPago(val etiqueta: String) {
    EFECTIVO("Efectivo"),
    DEBITO("Débito"),
    CREDITO("Crédito"),
    TRANSFERENCIA("Transferencia");

    companion object {
        fun desde(nombre: String?): MetodoPago =
            entries.firstOrNull { it.name == nombre } ?: EFECTIVO

        /** Pagar con crédito solo tiene sentido para los gastos. */
        fun para(tipo: TipoMovimiento): List<MetodoPago> =
            if (tipo == TipoMovimiento.INGRESO) entries.filterNot { it == CREDITO } else entries
    }
}

/**
 * Categoría de gasto (Alimentación, Bencina, Deudas, ...) o de ingreso (Sueldo, Ventas, ...).
 *
 * @param presupuesto tope mensual si es de gasto, meta mensual si es de ingreso;
 *                    0 significa "sin tope ni meta".
 */
data class Categoria(
    val id: String = UUID.randomUUID().toString(),
    val nombre: String,
    val emoji: String,
    val color: Long,
    val presupuesto: Long = 0L,
    val tipo: TipoMovimiento = TipoMovimiento.GASTO
)

/** Un gasto o un ingreso. El monto se guarda en unidades enteras de la moneda (pesos). */
data class Movimiento(
    val id: String = UUID.randomUUID().toString(),
    val monto: Long,
    val categoriaId: String,
    val fecha: LocalDate,
    val nota: String = "",
    val metodo: MetodoPago = MetodoPago.EFECTIVO,
    val tipo: TipoMovimiento = TipoMovimiento.GASTO,
    val creado: Long = System.currentTimeMillis()
) {
    val mes: YearMonth get() = YearMonth.from(fecha)
    val esIngreso: Boolean get() = tipo == TipoMovimiento.INGRESO
}

enum class Tema(val etiqueta: String) {
    SISTEMA("Según el sistema"),
    CLARO("Claro"),
    OSCURO("Oscuro");

    companion object {
        fun desde(nombre: String?): Tema = entries.firstOrNull { it.name == nombre } ?: SISTEMA
    }
}

/** Preferencias de la app. */
data class Ajustes(
    val simbolo: String = "$",
    val tema: Tema = Tema.SISTEMA
)

/** Total de una categoría durante un periodo, ya listo para mostrar. */
data class TotalCategoria(
    val categoria: Categoria,
    val total: Long,
    val cantidad: Int,
    val porcentaje: Float
)

/** Resumen de un mes: lo que entró, lo que salió y lo que quedó. */
data class BalanceMes(
    val ingresos: Long,
    val gastos: Long
) {
    val balance: Long get() = ingresos - gastos
    val enVerde: Boolean get() = balance >= 0
    /** Qué proporción de lo que entró ya se gastó (1f = se gastó todo). */
    val proporcionGastada: Float
        get() = if (ingresos <= 0L) 0f else gastos.toFloat() / ingresos
}

/** Categorías de gasto con las que parte la app. */
val CATEGORIAS_GASTO_INICIALES: List<Categoria> = listOf(
    Categoria("alimentacion", "Alimentación", "🍽️", 0xFFFF7043),
    Categoria("bencina", "Bencina", "⛽", 0xFF42A5F5),
    Categoria("deudas", "Deudas", "💳", 0xFFEF5350),
    Categoria("hogar", "Arriendo / Hogar", "🏠", 0xFFAB47BC),
    Categoria("servicios", "Cuentas y servicios", "💡", 0xFFFFCA28),
    Categoria("transporte", "Transporte", "🚌", 0xFF26C6DA),
    Categoria("salud", "Salud", "🏥", 0xFF66BB6A),
    Categoria("entretencion", "Entretención", "🎬", 0xFFEC407A),
    Categoria("educacion", "Educación", "📚", 0xFF5C6BC0),
    Categoria("vestuario", "Vestuario", "👕", 0xFF8D6E63),
    Categoria("mascotas", "Mascotas", "🐾", 0xFF26A69A),
    Categoria("otros", "Otros", "📦", 0xFF78909C)
)

/** Categorías de ingreso con las que parte la app. */
val CATEGORIAS_INGRESO_INICIALES: List<Categoria> = listOf(
    Categoria("sueldo", "Sueldo", "💼", 0xFF2E9E5B, tipo = TipoMovimiento.INGRESO),
    Categoria("extras", "Trabajos extra", "🧰", 0xFF7CB342, tipo = TipoMovimiento.INGRESO),
    Categoria("ventas", "Ventas", "🏷️", 0xFF00ACC1, tipo = TipoMovimiento.INGRESO),
    Categoria("inversiones", "Inversiones", "📈", 0xFF00897B, tipo = TipoMovimiento.INGRESO),
    Categoria("regalos", "Regalos", "🎁", 0xFFFFB300, tipo = TipoMovimiento.INGRESO),
    Categoria("devoluciones", "Devoluciones", "↩️", 0xFF4DB6AC, tipo = TipoMovimiento.INGRESO),
    Categoria("otros_ingresos", "Otros ingresos", "➕", 0xFF9CCC65, tipo = TipoMovimiento.INGRESO)
)

val CATEGORIAS_INICIALES: List<Categoria> = CATEGORIAS_GASTO_INICIALES + CATEGORIAS_INGRESO_INICIALES

/** Categorías comodín: reciben los movimientos de una categoría que se borra. */
const val ID_CATEGORIA_OTROS = "otros"
const val ID_CATEGORIA_OTROS_INGRESOS = "otros_ingresos"

fun idCategoriaComodin(tipo: TipoMovimiento): String =
    if (tipo == TipoMovimiento.INGRESO) ID_CATEGORIA_OTROS_INGRESOS else ID_CATEGORIA_OTROS

/** Paleta ofrecida al crear o editar una categoría. */
val PALETA_CATEGORIAS: List<Long> = listOf(
    0xFFFF7043, 0xFF42A5F5, 0xFFEF5350, 0xFFAB47BC, 0xFFFFCA28, 0xFF26C6DA,
    0xFF66BB6A, 0xFFEC407A, 0xFF5C6BC0, 0xFF8D6E63, 0xFF26A69A, 0xFF78909C,
    0xFF2E9E5B, 0xFF7CB342, 0xFF00ACC1, 0xFF00897B, 0xFFFFB300, 0xFF9CCC65
)

private val EMOJIS_GASTO = listOf(
    "🍽️", "🛒", "⛽", "💳", "🏠", "💡", "🚌", "🏥", "🎬", "📚", "👕", "🐾",
    "☕", "🍺", "🎁", "✈️", "📱", "🧾", "💇", "🔧", "🏋️", "🎮", "💊", "📦"
)

private val EMOJIS_INGRESO = listOf(
    "💼", "🧰", "🏷️", "📈", "🎁", "↩️", "➕", "💰", "🤝", "🏦", "💵", "🧑‍💻",
    "🚗", "🏠", "🎓", "🪙", "📦", "🎯"
)

/** Emojis sugeridos al crear o editar una categoría, según sea de gasto o de ingreso. */
fun emojisSugeridos(tipo: TipoMovimiento): List<String> =
    if (tipo == TipoMovimiento.INGRESO) EMOJIS_INGRESO else EMOJIS_GASTO
