package cl.augustogames.gastos.data

import java.time.LocalDate
import java.time.YearMonth
import java.util.UUID

/** Forma en que se pagó un gasto. */
enum class MetodoPago(val etiqueta: String) {
    EFECTIVO("Efectivo"),
    DEBITO("Débito"),
    CREDITO("Crédito"),
    TRANSFERENCIA("Transferencia");

    companion object {
        fun desde(nombre: String?): MetodoPago =
            entries.firstOrNull { it.name == nombre } ?: EFECTIVO
    }
}

/**
 * Categoría de gasto (Alimentación, Bencina, Deudas, ...).
 *
 * @param presupuesto tope mensual en pesos; 0 significa "sin presupuesto".
 */
data class Categoria(
    val id: String = UUID.randomUUID().toString(),
    val nombre: String,
    val emoji: String,
    val color: Long,
    val presupuesto: Long = 0L
)

/** Un gasto registrado. El monto se guarda en unidades enteras de la moneda (pesos). */
data class Gasto(
    val id: String = UUID.randomUUID().toString(),
    val monto: Long,
    val categoriaId: String,
    val fecha: LocalDate,
    val nota: String = "",
    val metodo: MetodoPago = MetodoPago.EFECTIVO,
    val creado: Long = System.currentTimeMillis()
) {
    val mes: YearMonth get() = YearMonth.from(fecha)
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

/** Total gastado en una categoría durante un periodo, ya listo para mostrar. */
data class TotalCategoria(
    val categoria: Categoria,
    val total: Long,
    val cantidad: Int,
    val porcentaje: Float
)

/** Categorías con las que parte la app la primera vez que se abre. */
val CATEGORIAS_INICIALES: List<Categoria> = listOf(
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

/** Categoría usada cuando se borra otra que aún tenía gastos. */
const val ID_CATEGORIA_OTROS = "otros"

/** Paleta ofrecida al crear o editar una categoría. */
val PALETA_CATEGORIAS: List<Long> = listOf(
    0xFFFF7043, 0xFF42A5F5, 0xFFEF5350, 0xFFAB47BC, 0xFFFFCA28, 0xFF26C6DA,
    0xFF66BB6A, 0xFFEC407A, 0xFF5C6BC0, 0xFF8D6E63, 0xFF26A69A, 0xFF78909C
)

/** Emojis sugeridos al crear o editar una categoría. */
val EMOJIS_SUGERIDOS: List<String> = listOf(
    "🍽️", "🛒", "⛽", "💳", "🏠", "💡", "🚌", "🏥", "🎬", "📚", "👕", "🐾",
    "☕", "🍺", "🎁", "✈️", "📱", "🧾", "💇", "🔧", "🏋️", "🎮", "💊", "📦"
)
