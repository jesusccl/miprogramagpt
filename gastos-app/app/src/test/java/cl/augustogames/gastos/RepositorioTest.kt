package cl.augustogames.gastos

import android.content.Context
import androidx.test.core.app.ApplicationProvider
import cl.augustogames.gastos.data.CATEGORIAS_INICIALES
import cl.augustogames.gastos.data.Categoria
import cl.augustogames.gastos.data.ID_CATEGORIA_OTROS
import cl.augustogames.gastos.data.ID_CATEGORIA_OTROS_INGRESOS
import cl.augustogames.gastos.data.MetodoPago
import cl.augustogames.gastos.data.Movimiento
import cl.augustogames.gastos.data.Repositorio
import cl.augustogames.gastos.data.Tema
import cl.augustogames.gastos.data.TipoMovimiento
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
    private lateinit var archivo: File

    @Before
    fun preparar() {
        contexto = ApplicationProvider.getApplicationContext()
        archivo = File(contexto.filesDir, "mis-gastos.json")
        archivo.delete()
        Repositorio.reiniciar(contexto)
    }

    @Test
    fun `parte con las categorias por defecto de gasto y de ingreso`() {
        assertEquals(CATEGORIAS_INICIALES.size, Repositorio.categorias.size)
        val gastos = Repositorio.categoriasDe(TipoMovimiento.GASTO).map { it.nombre }
        val ingresos = Repositorio.categoriasDe(TipoMovimiento.INGRESO).map { it.nombre }
        assertTrue(gastos.containsAll(listOf("Alimentación", "Bencina", "Deudas")))
        assertTrue(ingresos.containsAll(listOf("Sueldo", "Trabajos extra", "Ventas")))
    }

    @Test
    fun `suma los gastos del mes y los ordena por fecha`() {
        val mes = YearMonth.of(2026, 4)
        Repositorio.agregarMovimiento(gasto(15_000, "alimentacion", mes.atDay(3)))
        Repositorio.agregarMovimiento(gasto(25_000, "bencina", mes.atDay(20)))
        Repositorio.agregarMovimiento(gasto(5_000, "alimentacion", mes.atDay(10)))
        Repositorio.agregarMovimiento(gasto(99_000, "deudas", mes.plusMonths(1).atDay(1)))

        assertEquals(45_000L, Repositorio.totalDe(mes, TipoMovimiento.GASTO))
        assertEquals(3, Repositorio.gastosDe(mes).size)
        // El más reciente queda primero.
        assertEquals(mes.atDay(20), Repositorio.gastosDe(mes).first().fecha)
        assertEquals(listOf(mes.plusMonths(1), mes), Repositorio.mesesConMovimientos())
    }

    @Test
    fun `el balance del mes es lo que entro menos lo que salio`() {
        val mes = YearMonth.of(2026, 9)
        Repositorio.agregarMovimiento(ingreso(900_000, "sueldo", mes.atDay(5)))
        Repositorio.agregarMovimiento(ingreso(100_000, "extras", mes.atDay(12)))
        Repositorio.agregarMovimiento(gasto(250_000, "alimentacion", mes.atDay(6)))
        Repositorio.agregarMovimiento(gasto(150_000, "bencina", mes.atDay(7)))

        val balance = Repositorio.balanceDe(mes)
        assertEquals(1_000_000L, balance.ingresos)
        assertEquals(400_000L, balance.gastos)
        assertEquals(600_000L, balance.balance)
        assertTrue(balance.enVerde)
        assertEquals(0.4f, balance.proporcionGastada, 0.001f)

        assertEquals(2, Repositorio.ingresosDe(mes).size)
        assertEquals(2, Repositorio.gastosDe(mes).size)
        assertEquals(4, Repositorio.movimientosDe(mes).size)
    }

    @Test
    fun `el balance queda en rojo si se gasta mas de lo que entra`() {
        val mes = YearMonth.of(2026, 9)
        Repositorio.agregarMovimiento(ingreso(500_000, "sueldo", mes.atDay(1)))
        Repositorio.agregarMovimiento(gasto(650_000, "deudas", mes.atDay(2)))

        val balance = Repositorio.balanceDe(mes)
        assertEquals(-150_000L, balance.balance)
        assertTrue(!balance.enVerde)
    }

    @Test
    fun `los gastos y los ingresos se agrupan por separado`() {
        val mes = YearMonth.of(2026, 4)
        Repositorio.agregarMovimiento(gasto(30_000, "alimentacion", mes.atDay(1)))
        Repositorio.agregarMovimiento(gasto(10_000, "bencina", mes.atDay(2)))
        Repositorio.agregarMovimiento(ingreso(700_000, "sueldo", mes.atDay(3)))

        val gastos = Repositorio.totalesPorCategoria(Repositorio.gastosDe(mes))
        assertEquals(2, gastos.size)
        assertEquals("Alimentación", gastos.first().categoria.nombre)
        assertEquals(0.75f, gastos.first().porcentaje, 0.001f)

        val ingresos = Repositorio.totalesPorCategoria(Repositorio.ingresosDe(mes))
        assertEquals(1, ingresos.size)
        assertEquals("Sueldo", ingresos.first().categoria.nombre)
        assertEquals(700_000L, ingresos.first().total)
    }

    @Test
    fun `al borrar una categoria sus movimientos pasan a la comodin de su tipo`() {
        Repositorio.guardarCategoria(Categoria("viajes", "Viajes", "✈️", 0xFF42A5F5))
        Repositorio.guardarCategoria(
            Categoria("arriendo", "Arriendo recibido", "🏠", 0xFF2E9E5B, tipo = TipoMovimiento.INGRESO)
        )
        Repositorio.agregarMovimiento(gasto(80_000, "viajes", LocalDate.of(2026, 2, 14)))
        Repositorio.agregarMovimiento(ingreso(300_000, "arriendo", LocalDate.of(2026, 2, 5)))

        Repositorio.eliminarCategoria("viajes")
        Repositorio.eliminarCategoria("arriendo")

        assertNull(Repositorio.categoria("viajes"))
        assertNull(Repositorio.categoria("arriendo"))
        val elGasto = Repositorio.movimientos.single { !it.esIngreso }
        val elIngreso = Repositorio.movimientos.single { it.esIngreso }
        assertEquals(ID_CATEGORIA_OTROS, elGasto.categoriaId)
        assertEquals(ID_CATEGORIA_OTROS_INGRESOS, elIngreso.categoriaId)
        assertEquals(80_000L, elGasto.monto)
        assertEquals(300_000L, elIngreso.monto)
    }

    @Test
    fun `nunca borra las categorias comodin`() {
        Repositorio.eliminarCategoria(ID_CATEGORIA_OTROS)
        Repositorio.eliminarCategoria(ID_CATEGORIA_OTROS_INGRESOS)
        assertTrue(Repositorio.categorias.any { it.id == ID_CATEGORIA_OTROS })
        assertTrue(Repositorio.categorias.any { it.id == ID_CATEGORIA_OTROS_INGRESOS })
    }

    @Test
    fun `los datos siguen ahi despues de cerrar la app`() {
        Repositorio.agregarMovimiento(
            gasto(7_500, "bencina", LocalDate.of(2026, 1, 9), "bomba Copec")
        )
        Repositorio.agregarMovimiento(
            ingreso(850_000, "sueldo", LocalDate.of(2026, 1, 5), "enero")
        )
        Repositorio.guardarCategoria(
            Repositorio.categoria("alimentacion")!!.copy(presupuesto = 300_000)
        )
        Repositorio.guardarCategoria(Repositorio.categoria("sueldo")!!.copy(presupuesto = 900_000))
        Repositorio.actualizarAjustes(Repositorio.ajustes.copy(simbolo = "€", tema = Tema.OSCURO))

        Repositorio.reiniciar(contexto)

        val elGasto = Repositorio.movimientos.single { !it.esIngreso }
        assertEquals(7_500L, elGasto.monto)
        assertEquals("bomba Copec", elGasto.nota)
        assertEquals(LocalDate.of(2026, 1, 9), elGasto.fecha)
        assertEquals(MetodoPago.DEBITO, elGasto.metodo)

        val elIngreso = Repositorio.movimientos.single { it.esIngreso }
        assertEquals(850_000L, elIngreso.monto)
        assertEquals(TipoMovimiento.INGRESO, elIngreso.tipo)

        assertEquals(300_000L, Repositorio.categoria("alimentacion")!!.presupuesto)
        assertEquals(900_000L, Repositorio.categoria("sueldo")!!.presupuesto)
        assertEquals(TipoMovimiento.INGRESO, Repositorio.categoria("sueldo")!!.tipo)
        assertEquals("€", Repositorio.ajustes.simbolo)
        assertEquals(Tema.OSCURO, Repositorio.ajustes.tema)
    }

    @Test
    fun `abre sin perder nada un archivo guardado por la version 1_0`() {
        // Formato antiguo: la lista se llamaba "gastos" y nada tenía tipo.
        archivo.writeText(
            """
            {
              "version": 1,
              "ajustes": { "simbolo": "$", "tema": "OSCURO" },
              "categorias": [
                { "id": "alimentacion", "nombre": "Alimentación", "emoji": "🍽️",
                  "color": 4294930499, "presupuesto": 300000 },
                { "id": "otros", "nombre": "Otros", "emoji": "📦", "color": 4286421660 }
              ],
              "gastos": [
                { "id": "g1", "monto": 12500, "categoriaId": "alimentacion",
                  "fecha": "2026-01-05", "nota": "feria", "metodo": "DEBITO", "creado": 1 }
              ]
            }
            """.trimIndent()
        )

        Repositorio.reiniciar(contexto)

        val movimiento = Repositorio.movimientos.single()
        assertEquals(12_500L, movimiento.monto)
        assertEquals("feria", movimiento.nota)
        assertEquals(TipoMovimiento.GASTO, movimiento.tipo)
        assertEquals(LocalDate.of(2026, 1, 5), movimiento.fecha)

        val alimentacion = Repositorio.categoria("alimentacion")!!
        assertEquals(TipoMovimiento.GASTO, alimentacion.tipo)
        assertEquals(300_000L, alimentacion.presupuesto)
        assertEquals(Tema.OSCURO, Repositorio.ajustes.tema)

        // Y aparecen las categorías de ingreso que la 1.0 no tenía.
        val ingresos = Repositorio.categoriasDe(TipoMovimiento.INGRESO)
        assertTrue(ingresos.any { it.nombre == "Sueldo" })
        assertTrue(ingresos.any { it.id == ID_CATEGORIA_OTROS_INGRESOS })

        // Lo migrado se guarda ya en el formato nuevo.
        Repositorio.agregarMovimiento(ingreso(500_000, "sueldo", LocalDate.of(2026, 1, 6)))
        Repositorio.reiniciar(contexto)
        assertEquals(2, Repositorio.movimientos.size)
        assertEquals(500_000L, Repositorio.totalDe(YearMonth.of(2026, 1), TipoMovimiento.INGRESO))
        assertEquals(12_500L, Repositorio.totalDe(YearMonth.of(2026, 1), TipoMovimiento.GASTO))
    }

    @Test
    fun `editar y eliminar un movimiento`() {
        val original = gasto(1_000, "alimentacion", LocalDate.of(2026, 5, 5))
        Repositorio.agregarMovimiento(original)
        Repositorio.actualizarMovimiento(original.copy(monto = 2_000, nota = "corregido"))

        assertEquals(1, Repositorio.movimientos.size)
        assertEquals(2_000L, Repositorio.movimientos.single().monto)
        assertEquals("corregido", Repositorio.movimientos.single().nota)

        Repositorio.eliminarMovimiento(original.id)
        assertTrue(Repositorio.movimientos.isEmpty())
    }

    @Test
    fun `un gasto puede convertirse en ingreso al editarlo`() {
        val original = gasto(50_000, "alimentacion", LocalDate.of(2026, 5, 5))
        Repositorio.agregarMovimiento(original)
        Repositorio.actualizarMovimiento(
            original.copy(tipo = TipoMovimiento.INGRESO, categoriaId = "sueldo")
        )

        val mes = YearMonth.of(2026, 5)
        assertEquals(0L, Repositorio.totalDe(mes, TipoMovimiento.GASTO))
        assertEquals(50_000L, Repositorio.totalDe(mes, TipoMovimiento.INGRESO))
    }

    @Test
    fun `el csv distingue gastos de ingresos`() {
        Repositorio.agregarMovimiento(
            gasto(4_990, "alimentacion", LocalDate.of(2026, 6, 1), "pan; leche")
        )
        Repositorio.agregarMovimiento(ingreso(800_000, "sueldo", LocalDate.of(2026, 6, 2)))
        val lineas = Repositorio.exportarCsv().trim().lines()

        assertEquals("fecha;tipo;categoria;monto;metodo;nota", lineas.first())
        assertEquals(3, lineas.size)
        assertEquals("2026-06-01;Gasto;Alimentación;4990;Débito;pan, leche", lineas[1])
        assertEquals("2026-06-02;Ingreso;Sueldo;800000;Transferencia;", lineas[2])
    }

    @Test
    fun `el credito no se ofrece como forma de recibir un ingreso`() {
        val paraGasto = MetodoPago.para(TipoMovimiento.GASTO)
        val paraIngreso = MetodoPago.para(TipoMovimiento.INGRESO)
        assertTrue(paraGasto.contains(MetodoPago.CREDITO))
        assertTrue(!paraIngreso.contains(MetodoPago.CREDITO))
        assertTrue(paraIngreso.contains(MetodoPago.TRANSFERENCIA))
    }

    private fun gasto(monto: Long, categoria: String, fecha: LocalDate, nota: String = "") =
        Movimiento(
            monto = monto,
            categoriaId = categoria,
            fecha = fecha,
            nota = nota,
            metodo = MetodoPago.DEBITO,
            tipo = TipoMovimiento.GASTO
        )

    private fun ingreso(monto: Long, categoria: String, fecha: LocalDate, nota: String = "") =
        Movimiento(
            monto = monto,
            categoriaId = categoria,
            fecha = fecha,
            nota = nota,
            metodo = MetodoPago.TRANSFERENCIA,
            tipo = TipoMovimiento.INGRESO
        )
}
