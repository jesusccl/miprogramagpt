package cl.augustogames.gastos.ui

import java.time.LocalDate
import java.time.YearMonth
import java.time.format.TextStyle
import java.util.Locale
import kotlin.math.abs

/** Formateo de montos y fechas en español de Chile (miles con punto, sin decimales). */
object Formato {

    private val LOCALE: Locale = Locale.forLanguageTag("es-CL")

    fun miles(valor: Long): String {
        val digitos = abs(valor).toString()
        val agrupado = digitos.reversed().chunked(3).joinToString(".").reversed()
        return if (valor < 0) "-$agrupado" else agrupado
    }

    fun monto(valor: Long, simbolo: String = "$"): String = "$simbolo${miles(valor)}"

    /** Monto con signo para las listas donde se mezclan gastos e ingresos. */
    fun montoConSigno(valor: Long, esIngreso: Boolean, simbolo: String = "$"): String =
        if (esIngreso) "+${monto(valor, simbolo)}" else "\u2212${monto(valor, simbolo)}"

    /** Versión compacta para etiquetas de gráficos: $12,5K · $1,2M */
    fun montoCorto(valor: Long, simbolo: String = "$"): String = when {
        abs(valor) >= 1_000_000 -> "$simbolo${unaDecimal(valor / 1_000_000.0)}M"
        abs(valor) >= 10_000 -> "$simbolo${unaDecimal(valor / 1_000.0)}K"
        else -> monto(valor, simbolo)
    }

    private fun unaDecimal(valor: Double): String =
        String.format(LOCALE, "%.1f", valor).removeSuffix(",0").removeSuffix(".0")

    fun mesAnio(mes: YearMonth): String {
        val nombre = mes.month.getDisplayName(TextStyle.FULL, LOCALE)
        return "${nombre.replaceFirstChar { it.uppercase(LOCALE) }} ${mes.year}"
    }

    fun mesCorto(mes: YearMonth): String {
        val nombre = mes.month.getDisplayName(TextStyle.SHORT, LOCALE).trim('.')
        return "${nombre.replaceFirstChar { it.uppercase(LOCALE) }} ${mes.year}"
    }

    fun fechaCorta(fecha: LocalDate): String {
        val mes = fecha.month.getDisplayName(TextStyle.SHORT, LOCALE).trim('.')
        return "${fecha.dayOfMonth} ${mes.lowercase(LOCALE)}"
    }

    fun fechaLarga(fecha: LocalDate): String {
        val dia = fecha.dayOfWeek.getDisplayName(TextStyle.FULL, LOCALE)
        val mes = fecha.month.getDisplayName(TextStyle.FULL, LOCALE)
        return "${dia.replaceFirstChar { it.uppercase(LOCALE) }} ${fecha.dayOfMonth} de $mes"
    }

    /** "Hoy", "Ayer" o la fecha larga, para los encabezados de la lista. */
    fun etiquetaDia(fecha: LocalDate): String {
        val hoy = LocalDate.now()
        return when (fecha) {
            hoy -> "Hoy"
            hoy.minusDays(1) -> "Ayer"
            else -> fechaLarga(fecha)
        }
    }
}
