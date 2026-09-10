package cl.augustogames.gastos

import android.content.Context
import androidx.test.core.app.ApplicationProvider
import cl.augustogames.gastos.data.CATEGORIAS_INICIALES
import cl.augustogames.gastos.data.Categoria
import cl.augustogames.gastos.data.Gasto
import cl.augustogames.gastos.data.ID_CATEGORIA_OTROS
import cl.augustogames.gastos.data.MetodoPago
import cl.augustogames.gastos.data.Repositorio
import cl.augustogames.gastos.data.Tema
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.annotation.Config
import java.io.File
import java.time.LocalDate
import java.time.YearMonth

@RunWith(RobolectricTestRunner::class)
@Config(sdk = [34])
class RepositorioTest {

    private lateinit var contexto: Context

    @Before
    fun preparar() {
        contexto = ApplicationProvider.getApplicationContext()
        File(contexto.filesDir, "mis-gastos.json").delete()
        Repositorio.reiniciar(contexto)
    }

    @Test
    fun `parte con las categorias por defecto`() {
        assertEquals(CATEGORIAS_INICIALES.size, Repositorio.categorias.size)
        assertTrue(Repositorio.categorias.any { it.nombre == "Alimentación" })
        assertTrue(Repositorio.categorias.any { it.nombre == "Bencina" })
        assertTrue(Repositorio.categorias.any { it.nombre == "Deudas" })
    }

    @Test
    fun `suma los gastos del mes y los ordena por fecha`() {
        val mes = YearMonth.of(2026, 4)
        Repositorio.agregarGasto(gasto(15_000, "alimentacion", mes.atDay(3)))
        Repositorio.agregarGasto(gasto(25_000, "bencina", mes.atDay(20)))
        Repositorio.agregarGasto(gasto(5_000, "alimentacion", mes.atDay(10)))
        Repositorio.agregarGasto(gasto(99_000, "deudas", mes.plusMonths(1).atDay(1)))

        assertEquals(45_000L, Repositorio.totalDe(mes))
        assertEquals(3, Repositorio.gastosDe(mes).size)
        // El más reciente queda primero.
        assertEquals(mes.atDay(20), Repositorio.gastosDe(mes).first().fecha)
        assertEquals(listOf(mes.plusMonths(1), mes), Repositorio.mesesConGastos())
    }

    @Test
    fun `agrupa por categoria con porcentajes`() {
        val mes = YearMonth.of(2026, 4)
        Repositorio.agregarGasto(gasto(30_000, "alimentacion", mes.atDay(1)))
        Repositorio.agregarGasto(gasto(10_000, "bencina", mes.atDay(2)))

        val totales = Repositorio.totalesPorCategoria(Repositorio.gastosDe(mes))
        assertEquals(2, totales.size)
        assertEquals("Alimentación", totales.first().categoria.nombre)
        assertEquals(30_000L, totales.first().total)
        assertEquals(0.75f, totales.first().porcentaje, 0.001f)
        assertEquals(0.25f, totales[1].porcentaje, 0.001f)
    }

    @Test
    fun `al borrar una categoria sus gastos pasan a otros`() {
        Repositorio.guardarCategoria(Categoria("viajes", "Viajes", "✈️", 0xFF42A5F5))
        Repositorio.agregarGasto(gasto(80_000, "viajes", LocalDate.of(2026, 2, 14)))

        Repositorio.eliminarCategoria("viajes")

        assertNull(Repositorio.categoria("viajes"))
        assertEquals(ID_CATEGORIA_OTROS, Repositorio.gastos.single().categoriaId)
        assertEquals(80_000L, Repositorio.gastos.single().monto)
    }

    @Test
    fun `nunca borra la categoria otros`() {
        Repositorio.eliminarCategoria(ID_CATEGORIA_OTROS)
        assertTrue(Repositorio.categorias.any { it.id == ID_CATEGORIA_OTROS })
    }

    @Test
    fun `los datos siguen ahi despues de cerrar la app`() {
        Repositorio.agregarGasto(gasto(7_500, "bencina", LocalDate.of(2026, 1, 9), "bomba Copec"))
        Repositorio.guardarCategoria(
            Repositorio.categoria("alimentacion")!!.copy(presupuesto = 300_000)
        )
        Repositorio.actualizarAjustes(Repositorio.ajustes.copy(simbolo = "€", tema = Tema.OSCURO))

        Repositorio.reiniciar(contexto)

        val recuperado = Repositorio.gastos.single()
        assertEquals(7_500L, recuperado.monto)
        assertEquals("bomba Copec", recuperado.nota)
        assertEquals(LocalDate.of(2026, 1, 9), recuperado.fecha)
        assertEquals(MetodoPago.DEBITO, recuperado.metodo)
        assertEquals(300_000L, Repositorio.categoria("alimentacion")!!.presupuesto)
        assertEquals("€", Repositorio.ajustes.simbolo)
        assertEquals(Tema.OSCURO, Repositorio.ajustes.tema)
    }

    @Test
    fun `editar y eliminar un gasto`() {
        val original = gasto(1_000, "alimentacion", LocalDate.of(2026, 5, 5))
        Repositorio.agregarGasto(original)
        Repositorio.actualizarGasto(original.copy(monto = 2_000, nota = "corregido"))

        assertEquals(1, Repositorio.gastos.size)
        assertEquals(2_000L, Repositorio.gastos.single().monto)
        assertEquals("corregido", Repositorio.gastos.single().nota)

        Repositorio.eliminarGasto(original.id)
        assertTrue(Repositorio.gastos.isEmpty())
    }

    @Test
    fun `el csv trae encabezado y una linea por gasto`() {
        Repositorio.agregarGasto(gasto(4_990, "alimentacion", LocalDate.of(2026, 6, 1), "pan; leche"))
        val lineas = Repositorio.exportarCsv().trim().lines()

        assertEquals("fecha;categoria;monto;metodo;nota", lineas.first())
        assertEquals(2, lineas.size)
        assertEquals("2026-06-01;Alimentación;4990;Débito;pan, leche", lineas[1])
    }

    private fun gasto(
        monto: Long,
        categoria: String,
        fecha: LocalDate,
        nota: String = ""
    ) = Gasto(
        monto = monto,
        categoriaId = categoria,
        fecha = fecha,
        nota = nota,
        metodo = MetodoPago.DEBITO
    )
}
