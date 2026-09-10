package cl.augustogames.gastos

import androidx.compose.ui.semantics.SemanticsActions
import androidx.compose.ui.test.SemanticsNodeInteraction
import androidx.compose.ui.test.assertIsDisplayed
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.compose.ui.test.onAllNodesWithText
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performClick
import androidx.compose.ui.test.performSemanticsAction
import androidx.test.core.app.ApplicationProvider
import cl.augustogames.gastos.data.MetodoPago
import cl.augustogames.gastos.data.Movimiento
import cl.augustogames.gastos.data.Repositorio
import cl.augustogames.gastos.data.TipoMovimiento
import org.junit.Before
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.annotation.Config
import java.io.File
import java.time.LocalDate

/** Comprobación de que la app parte y muestra lo que corresponde. */
@RunWith(RobolectricTestRunner::class)
@Config(sdk = [34], qualifiers = "w411dp-h1400dp")
class AppTest {

    @get:Rule
    val regla = createAndroidComposeRule<MainActivity>()

    // El repositorio es un objeto único que sobrevive entre pruebas dentro de la misma JVM,
    // así que cada prueba parte con el archivo borrado y el estado recién cargado.
    @Before
    fun limpiar() {
        val contexto = ApplicationProvider.getApplicationContext<android.content.Context>()
        File(contexto.filesDir, "mis-gastos.json").delete()
        Repositorio.reiniciar(contexto)
        regla.waitForIdle()
    }

    @Test
    fun `la app abre en el resumen`() {
        regla.onNodeWithText("Mis Gastos").assertIsDisplayed()
        regla.onNodeWithText("Gastos del mes").assertExists()
        regla.onNodeWithText("Sin movimientos este mes").assertExists()
        // Las cuatro secciones de la barra inferior.
        regla.onNodeWithText("Resumen").assertIsDisplayed()
        regla.onNodeWithText("Historial").assertIsDisplayed()
        regla.onNodeWithText("Categorías").assertIsDisplayed()
        regla.onNodeWithText("Ajustes").assertIsDisplayed()
    }

    @Test
    fun `un gasto registrado aparece en el resumen y en el historial`() {
        Repositorio.agregarMovimiento(gasto(18_990, "alimentacion", "feria"))
        regla.waitForIdle()

        regla.onNodeWithText("Gastado hoy").assertExists()
        regla.onNodeWithText("En qué se te fue").assertExists()
        primero("$18.990").assertExists()

        regla.onNodeWithText("Historial").performClick()
        regla.waitForIdle()
        regla.onNodeWithText("Hoy").assertExists()
        regla.onNodeWithText("1 movimiento").assertExists()
        // En el historial los gastos van con signo menos.
        primero("−$18.990").assertExists()
    }

    @Test
    fun `el resumen muestra el balance entre lo que entra y lo que sale`() {
        Repositorio.agregarMovimiento(ingreso(500_000, "sueldo", "sueldo del mes"))
        Repositorio.agregarMovimiento(gasto(200_000, "alimentacion", "supermercado"))
        regla.waitForIdle()

        regla.onNodeWithText("Ingresos").assertExists()
        primero("+$500.000").assertExists()
        regla.onNodeWithText("Te queda").assertExists()
        primero("$300.000").assertExists()
        regla.onNodeWithText("De dónde vino la plata").assertExists()
        regla.onNodeWithText("Llevas gastado el 40% de lo que entró este mes").assertExists()
    }

    @Test
    fun `el resumen avisa cuando se gasta mas de lo que entra`() {
        Repositorio.agregarMovimiento(ingreso(100_000, "sueldo"))
        Repositorio.agregarMovimiento(gasto(150_000, "deudas"))
        regla.waitForIdle()

        regla.onNodeWithText("Te falta").assertExists()
        primero("$50.000").assertExists()
    }

    @Test
    fun `el historial filtra por ingresos`() {
        Repositorio.agregarMovimiento(ingreso(500_000, "sueldo"))
        Repositorio.agregarMovimiento(gasto(200_000, "alimentacion"))
        regla.waitForIdle()

        regla.onNodeWithText("Historial").performClick()
        regla.waitForIdle()
        regla.onNodeWithText("2 movimientos").assertExists()

        regla.onNodeWithText("Ingresos").tocar()
        regla.waitForIdle()
        regla.onNodeWithText("1 movimiento").assertExists()
        regla.onNodeWithText("Sueldo").assertExists()
        regla.onNodeWithText("Alimentación").assertDoesNotExist()
        primero("+$500.000").assertExists()
    }

    @Test
    fun `las categorias se separan entre gastos e ingresos`() {
        regla.onNodeWithText("Categorías").performClick()
        regla.waitForIdle()

        regla.onNodeWithText("Alimentación").assertExists()
        regla.onNodeWithText("Bencina").assertExists()
        regla.onNodeWithText("Deudas").assertExists()
        regla.onNodeWithText("Sueldo").assertDoesNotExist()

        regla.onNodeWithText("Ingresos").tocar()
        regla.waitForIdle()
        regla.onNodeWithText("Sueldo").assertExists()
        regla.onNodeWithText("Trabajos extra").assertExists()
        regla.onNodeWithText("Alimentación").assertDoesNotExist()
    }

    /** Los montos se repiten en varias tarjetas del resumen; basta con encontrar el primero. */
    private fun primero(texto: String): SemanticsNodeInteraction =
        regla.onAllNodesWithText(texto)[0]

    /**
     * Robolectric no entrega el toque simulado a los SegmentedButton (sí a los demás
     * botones), así que se invoca directamente su acción de clic.
     */
    private fun SemanticsNodeInteraction.tocar() =
        performSemanticsAction(SemanticsActions.OnClick)

    private fun gasto(monto: Long, categoria: String, nota: String = "") = Movimiento(
        monto = monto,
        categoriaId = categoria,
        fecha = LocalDate.now(),
        nota = nota,
        metodo = MetodoPago.DEBITO,
        tipo = TipoMovimiento.GASTO
    )

    private fun ingreso(monto: Long, categoria: String, nota: String = "") = Movimiento(
        monto = monto,
        categoriaId = categoria,
        fecha = LocalDate.now(),
        nota = nota,
        metodo = MetodoPago.TRANSFERENCIA,
        tipo = TipoMovimiento.INGRESO
    )
}
