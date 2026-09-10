package cl.augustogames.gastos

import androidx.compose.ui.test.assertCountEquals
import androidx.compose.ui.test.assertIsDisplayed
import androidx.compose.ui.test.onAllNodesWithText
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performClick
import androidx.test.core.app.ApplicationProvider
import cl.augustogames.gastos.data.Gasto
import cl.augustogames.gastos.data.Repositorio
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

    @Before
    fun limpiar() {
        val contexto = ApplicationProvider.getApplicationContext<android.content.Context>()
        File(contexto.filesDir, "mis-gastos.json").delete()
    }

    @Test
    fun `la app abre en el resumen`() {
        regla.onNodeWithText("Mis Gastos").assertIsDisplayed()
        regla.onNodeWithText("Total del mes").assertExists()
        regla.onNodeWithText("Sin gastos este mes").assertExists()
        // Las cuatro secciones de la barra inferior.
        regla.onNodeWithText("Resumen").assertIsDisplayed()
        regla.onNodeWithText("Ajustes").assertIsDisplayed()
    }

    @Test
    fun `un gasto registrado aparece en el resumen y en la lista`() {
        Repositorio.agregarGasto(
            Gasto(monto = 18_990, categoriaId = "alimentacion", fecha = LocalDate.now(), nota = "feria")
        )
        regla.waitForIdle()

        // El mismo monto se refleja en el total, en «hoy», en su categoría y en la lista.
        regla.onAllNodesWithText("$18.990").assertCountEquals(5)

        regla.onNodeWithText("Gastos").performClick()
        regla.waitForIdle()
        regla.onNodeWithText("Hoy").assertExists()
        regla.onNodeWithText("1 gasto").assertExists()
    }

    @Test
    fun `las categorias por defecto estan disponibles`() {
        regla.onNodeWithText("Categorías").performClick()
        regla.waitForIdle()

        regla.onNodeWithText("Alimentación").assertExists()
        regla.onNodeWithText("Bencina").assertExists()
        regla.onNodeWithText("Deudas").assertExists()
        regla.onAllNodesWithText("Nueva categoría")[0].assertIsDisplayed()
    }
}
