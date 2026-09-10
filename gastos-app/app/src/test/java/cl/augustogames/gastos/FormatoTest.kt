package cl.augustogames.gastos

import cl.augustogames.gastos.ui.Formato
import org.junit.Assert.assertEquals
import org.junit.Test
import java.time.LocalDate
import java.time.YearMonth

class FormatoTest {

    @Test
    fun `agrupa los miles con punto`() {
        assertEquals("0", Formato.miles(0))
        assertEquals("990", Formato.miles(990))
        assertEquals("12.500", Formato.miles(12_500))
        assertEquals("1.250.000", Formato.miles(1_250_000))
        assertEquals("-3.400", Formato.miles(-3_400))
    }

    @Test
    fun `antepone el simbolo de moneda`() {
        assertEquals("$12.500", Formato.monto(12_500))
        assertEquals("US$980", Formato.monto(980, "US$"))
    }

    @Test
    fun `acorta montos grandes para los graficos`() {
        assertEquals("$9.900", Formato.montoCorto(9_900))
        assertEquals("$12,5K", Formato.montoCorto(12_500))
        assertEquals("$1,3M", Formato.montoCorto(1_250_000))
    }

    @Test
    fun `escribe meses y fechas en espanol`() {
        assertEquals("Septiembre 2026", Formato.mesAnio(YearMonth.of(2026, 9)))
        assertEquals("3 mar", Formato.fechaCorta(LocalDate.of(2026, 3, 3)))
        assertEquals("Hoy", Formato.etiquetaDia(LocalDate.now()))
        assertEquals("Ayer", Formato.etiquetaDia(LocalDate.now().minusDays(1)))
    }
}
