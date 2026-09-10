package cl.augustogames.gastos.ui.pantallas

import android.content.Context
import android.content.Intent
import android.widget.Toast
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ExperimentalLayoutApi
import androidx.compose.foundation.layout.FlowRow
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Delete
import androidx.compose.material.icons.filled.Share
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.FilterChip
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import androidx.core.content.FileProvider
import cl.augustogames.gastos.BuildConfig
import cl.augustogames.gastos.data.Repositorio
import cl.augustogames.gastos.data.Tema
import cl.augustogames.gastos.ui.Formato
import cl.augustogames.gastos.ui.componentes.Tarjeta
import java.io.File
import java.time.LocalDate

@OptIn(ExperimentalLayoutApi::class)
@Composable
fun PantallaAjustes(modifier: Modifier = Modifier) {
    val contexto = LocalContext.current
    val ajustes = Repositorio.ajustes
    val movimientos = Repositorio.movimientos
    val cuantosGastos = movimientos.count { !it.esIngreso }
    val cuantosIngresos = movimientos.count { it.esIngreso }
    var confirmarBorrado by remember { mutableStateOf(false) }

    Column(
        modifier = modifier
            .verticalScroll(rememberScrollState())
            .padding(horizontal = 16.dp)
            .padding(top = 4.dp, bottom = 32.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp)
    ) {
        Tarjeta(titulo = "Moneda") {
            OutlinedTextField(
                value = ajustes.simbolo,
                onValueChange = { nuevo ->
                    Repositorio.actualizarAjustes(ajustes.copy(simbolo = nuevo.take(3)))
                },
                label = { Text("Símbolo") },
                singleLine = true,
                modifier = Modifier.fillMaxWidth()
            )
            Text(
                "Los montos se muestran así: ${Formato.monto(125_400L, ajustes.simbolo.ifBlank { "$" })}",
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
                modifier = Modifier.padding(top = 8.dp)
            )
        }

        Tarjeta(titulo = "Apariencia") {
            FlowRow(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                Tema.entries.forEach { opcion ->
                    FilterChip(
                        selected = ajustes.tema == opcion,
                        onClick = { Repositorio.actualizarAjustes(ajustes.copy(tema = opcion)) },
                        label = { Text(opcion.etiqueta) }
                    )
                }
            }
        }

        Tarjeta(titulo = "Tus datos") {
            val primero = movimientos.minByOrNull { it.fecha }?.fecha
            Text(
                buildString {
                    append("$cuantosGastos ${if (cuantosGastos == 1) "gasto" else "gastos"}")
                    append(" y $cuantosIngresos ${if (cuantosIngresos == 1) "ingreso" else "ingresos"}")
                    if (primero != null) append(" desde el ${Formato.fechaCorta(primero)}")
                    append(".")
                },
                style = MaterialTheme.typography.bodyMedium
            )
            Text(
                "Todo se guarda solo en este teléfono. La app no pide permisos ni usa internet.",
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
                modifier = Modifier.padding(top = 4.dp)
            )

            Spacer(Modifier.height(12.dp))
            Button(
                onClick = { compartirCsv(contexto) },
                enabled = movimientos.isNotEmpty(),
                modifier = Modifier.fillMaxWidth()
            ) {
                Icon(Icons.Default.Share, contentDescription = null)
                Spacer(Modifier.width(8.dp))
                Text("Exportar a CSV")
            }
            Spacer(Modifier.height(8.dp))
            OutlinedButton(
                onClick = { confirmarBorrado = true },
                enabled = movimientos.isNotEmpty(),
                colors = ButtonDefaults.outlinedButtonColors(
                    contentColor = MaterialTheme.colorScheme.error
                ),
                modifier = Modifier.fillMaxWidth()
            ) {
                Icon(Icons.Default.Delete, contentDescription = null)
                Spacer(Modifier.width(8.dp))
                Text("Borrar todo el historial")
            }
        }

        Tarjeta(titulo = "Acerca de") {
            Text("Mis Gastos ${BuildConfig.VERSION_NAME}", style = MaterialTheme.typography.bodyMedium)
            Text(
                "App para llevar la cuenta de lo que entra y lo que sale, mes a mes y por categoría.",
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
                modifier = Modifier.padding(top = 4.dp)
            )
        }
    }

    if (confirmarBorrado) {
        AlertDialog(
            onDismissRequest = { confirmarBorrado = false },
            title = { Text("¿Borrar todo el historial?") },
            text = { Text("Se eliminarán los ${movimientos.size} movimientos registrados (gastos e ingresos). Las categorías se mantienen. Esto no se puede deshacer.") },
            confirmButton = {
                androidx.compose.material3.TextButton(onClick = {
                    Repositorio.borrarTodosLosMovimientos()
                    confirmarBorrado = false
                }) { Text("Borrar todo", color = MaterialTheme.colorScheme.error) }
            },
            dismissButton = {
                androidx.compose.material3.TextButton(onClick = { confirmarBorrado = false }) {
                    Text("Cancelar")
                }
            }
        )
    }
}

/** Genera un CSV en la caché y abre el menú de compartir de Android. */
private fun compartirCsv(contexto: Context) {
    runCatching {
        val carpeta = File(contexto.cacheDir, "exportaciones").apply { mkdirs() }
        val archivo = File(carpeta, "mis-gastos-${LocalDate.now()}.csv")
        // El BOM hace que Excel abra el archivo con los acentos correctos.
        archivo.writeText("\uFEFF" + Repositorio.exportarCsv())

        val uri = FileProvider.getUriForFile(
            contexto,
            "${contexto.packageName}.fileprovider",
            archivo
        )
        val envio = Intent(Intent.ACTION_SEND).apply {
            type = "text/csv"
            putExtra(Intent.EXTRA_STREAM, uri)
            putExtra(Intent.EXTRA_SUBJECT, "Mis gastos")
            addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
        }
        contexto.startActivity(Intent.createChooser(envio, "Compartir mis gastos"))
    }.onFailure {
        Toast.makeText(contexto, "No se pudo exportar el archivo", Toast.LENGTH_SHORT).show()
    }
}
