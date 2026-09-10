package cl.augustogames.gastos.ui

import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Add
import androidx.compose.material.icons.filled.Home
import androidx.compose.material.icons.automirrored.filled.List
import androidx.compose.material.icons.filled.Settings
import androidx.compose.material.icons.filled.ShoppingCart
import androidx.compose.material3.CenterAlignedTopAppBar
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.ExtendedFloatingActionButton
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.NavigationBar
import androidx.compose.material3.NavigationBarItem
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBarDefaults
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.vector.ImageVector
import cl.augustogames.gastos.data.Gasto
import cl.augustogames.gastos.data.Repositorio
import cl.augustogames.gastos.ui.componentes.FormularioGasto
import cl.augustogames.gastos.ui.pantallas.PantallaAjustes
import cl.augustogames.gastos.ui.pantallas.PantallaCategorias
import cl.augustogames.gastos.ui.pantallas.PantallaGastos
import cl.augustogames.gastos.ui.pantallas.PantallaResumen
import java.time.LocalDate
import java.time.YearMonth

enum class Destino(val etiqueta: String, val icono: ImageVector) {
    RESUMEN("Resumen", Icons.Default.Home),
    GASTOS("Gastos", Icons.AutoMirrored.Filled.List),
    CATEGORIAS("Categorías", Icons.Default.ShoppingCart),
    AJUSTES("Ajustes", Icons.Default.Settings)
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun AppGastos() {
    var destino by rememberSaveable { mutableStateOf(Destino.RESUMEN) }
    var mesTexto by rememberSaveable { mutableStateOf(YearMonth.now().toString()) }
    var formularioAbierto by rememberSaveable { mutableStateOf(false) }
    var idEnEdicion by rememberSaveable { mutableStateOf<String?>(null) }
    val gastoEnEdicion = idEnEdicion?.let { id -> Repositorio.gastos.firstOrNull { it.id == id } }

    val mes = remember(mesTexto) { YearMonth.parse(mesTexto) }
    val cambiarMes: (YearMonth) -> Unit = { nuevo -> mesTexto = nuevo.toString() }

    Scaffold(
        containerColor = MaterialTheme.colorScheme.background,
        topBar = {
            CenterAlignedTopAppBar(
                title = {
                    Text(
                        if (destino == Destino.RESUMEN) "Mis Gastos" else destino.etiqueta,
                        style = MaterialTheme.typography.titleLarge
                    )
                },
                colors = TopAppBarDefaults.centerAlignedTopAppBarColors(
                    containerColor = MaterialTheme.colorScheme.background
                )
            )
        },
        bottomBar = {
            NavigationBar(containerColor = MaterialTheme.colorScheme.surface) {
                Destino.entries.forEach { opcion ->
                    NavigationBarItem(
                        selected = destino == opcion,
                        onClick = { destino = opcion },
                        icon = { Icon(opcion.icono, contentDescription = opcion.etiqueta) },
                        label = { Text(opcion.etiqueta, maxLines = 1) }
                    )
                }
            }
        },
        floatingActionButton = {
            if (destino == Destino.RESUMEN || destino == Destino.GASTOS) {
                ExtendedFloatingActionButton(
                    onClick = {
                        idEnEdicion = null
                        formularioAbierto = true
                    },
                    icon = { Icon(Icons.Default.Add, contentDescription = null) },
                    text = { Text("Gasto") }
                )
            }
        }
    ) { relleno ->
        val editar: (Gasto) -> Unit = { gasto ->
            idEnEdicion = gasto.id
            formularioAbierto = true
        }
        val modificador = Modifier.padding(relleno).fillMaxSize()

        when (destino) {
            Destino.RESUMEN -> PantallaResumen(
                mes = mes,
                onCambiarMes = cambiarMes,
                onVerTodos = { destino = Destino.GASTOS },
                onEditarGasto = editar,
                modifier = modificador
            )

            Destino.GASTOS -> PantallaGastos(
                mes = mes,
                onCambiarMes = cambiarMes,
                onEditarGasto = editar,
                modifier = modificador
            )

            Destino.CATEGORIAS -> PantallaCategorias(
                mes = mes,
                modifier = modificador
            )

            Destino.AJUSTES -> PantallaAjustes(modifier = modificador)
        }
    }

    if (formularioAbierto) {
        FormularioGasto(
            gasto = gastoEnEdicion,
            fechaSugerida = if (mes == YearMonth.now()) LocalDate.now() else mes.atDay(1),
            onCerrar = {
                formularioAbierto = false
                idEnEdicion = null
            }
        )
    }
}
