package cl.augustogames.gastos.ui.componentes

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ExperimentalLayoutApi
import androidx.compose.foundation.layout.FlowRow
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.layout.imePadding
import androidx.compose.foundation.layout.navigationBarsPadding
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.DateRange
import androidx.compose.material.icons.filled.Delete
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.AssistChip
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.DatePicker
import androidx.compose.material3.DatePickerDialog
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.FilterChip
import androidx.compose.material3.FilterChipDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.ModalBottomSheet
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.rememberDatePickerState
import androidx.compose.material3.rememberModalBottomSheetState
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.dp
import cl.augustogames.gastos.data.Categoria
import cl.augustogames.gastos.data.Gasto
import cl.augustogames.gastos.data.MetodoPago
import cl.augustogames.gastos.data.Repositorio
import cl.augustogames.gastos.ui.Formato
import java.time.Instant
import java.time.LocalDate
import java.time.ZoneOffset

private val MONTOS_RAPIDOS = listOf(1_000L, 2_000L, 5_000L, 10_000L, 20_000L)

/**
 * Hoja para crear o editar un gasto.
 *
 * @param gasto null para crear uno nuevo; si viene con datos, se edita ese gasto.
 * @param fechaSugerida fecha con la que se abre el formulario al crear.
 */
@OptIn(ExperimentalMaterial3Api::class, ExperimentalLayoutApi::class)
@Composable
fun FormularioGasto(
    gasto: Gasto?,
    fechaSugerida: LocalDate,
    onCerrar: () -> Unit
) {
    val estadoHoja = rememberModalBottomSheetState(skipPartiallyExpanded = true)
    val categorias = Repositorio.categorias
    val simbolo = Repositorio.ajustes.simbolo

    // Se guarda con rememberSaveable (y en tipos simples) para no perder lo escrito
    // si el teléfono se rota o Android recrea la pantalla.
    var monto by rememberSaveable { mutableStateOf(gasto?.monto?.takeIf { it > 0 }?.toString() ?: "") }
    var categoriaId by rememberSaveable {
        mutableStateOf(gasto?.categoriaId ?: categorias.firstOrNull()?.id.orEmpty())
    }
    var diaEpoca by rememberSaveable {
        mutableStateOf((gasto?.fecha ?: fechaSugerida).toEpochDay())
    }
    var nota by rememberSaveable { mutableStateOf(gasto?.nota.orEmpty()) }
    var metodoNombre by rememberSaveable {
        mutableStateOf((gasto?.metodo ?: MetodoPago.EFECTIVO).name)
    }
    var mostrarCalendario by rememberSaveable { mutableStateOf(false) }
    var confirmarBorrado by rememberSaveable { mutableStateOf(false) }

    val fecha = LocalDate.ofEpochDay(diaEpoca)
    val metodo = MetodoPago.desde(metodoNombre)

    val valor = monto.toLongOrNull() ?: 0L
    val valido = valor > 0 && categoriaId.isNotBlank()
    val hoy = LocalDate.now()

    ModalBottomSheet(onDismissRequest = onCerrar, sheetState = estadoHoja) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .verticalScroll(rememberScrollState())
                .padding(horizontal = 20.dp)
                .padding(bottom = 24.dp)
                .imePadding()
                .navigationBarsPadding(),
            verticalArrangement = Arrangement.spacedBy(16.dp)
        ) {
            Text(
                text = if (gasto == null) "Nuevo gasto" else "Editar gasto",
                style = MaterialTheme.typography.titleLarge
            )

            CampoMonto(
                texto = monto,
                onCambio = { monto = it },
                simbolo = simbolo,
                etiqueta = "Monto",
                grande = true,
                modifier = Modifier.fillMaxWidth()
            )

            FlowRow(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                MONTOS_RAPIDOS.forEach { extra ->
                    AssistChip(
                        onClick = { monto = (valor + extra).toString() },
                        label = { Text("+${Formato.miles(extra)}") }
                    )
                }
                if (valor > 0) {
                    AssistChip(onClick = { monto = "" }, label = { Text("Borrar") })
                }
            }

            Text("Categoría", style = MaterialTheme.typography.titleMedium)
            FlowRow(
                horizontalArrangement = Arrangement.spacedBy(8.dp),
                verticalArrangement = Arrangement.spacedBy(4.dp)
            ) {
                categorias.forEach { categoria ->
                    ChipCategoria(
                        categoria = categoria,
                        seleccionada = categoria.id == categoriaId,
                        onClick = { categoriaId = categoria.id }
                    )
                }
            }

            Text("Fecha", style = MaterialTheme.typography.titleMedium)
            FlowRow(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                FilterChip(
                    selected = fecha == hoy,
                    onClick = { diaEpoca = hoy.toEpochDay() },
                    label = { Text("Hoy") }
                )
                FilterChip(
                    selected = fecha == hoy.minusDays(1),
                    onClick = { diaEpoca = hoy.minusDays(1).toEpochDay() },
                    label = { Text("Ayer") }
                )
                FilterChip(
                    selected = fecha != hoy && fecha != hoy.minusDays(1),
                    onClick = { mostrarCalendario = true },
                    label = { Text(Formato.fechaCorta(fecha)) },
                    leadingIcon = { Icon(Icons.Default.DateRange, contentDescription = null) }
                )
            }

            Text("Forma de pago", style = MaterialTheme.typography.titleMedium)
            FlowRow(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                MetodoPago.entries.forEach { opcion ->
                    FilterChip(
                        selected = opcion == metodo,
                        onClick = { metodoNombre = opcion.name },
                        label = { Text(opcion.etiqueta) }
                    )
                }
            }

            OutlinedTextField(
                value = nota,
                onValueChange = { nota = it.take(120) },
                modifier = Modifier.fillMaxWidth(),
                label = { Text("Detalle (opcional)") },
                placeholder = { Text("Ej: supermercado de la semana") },
                singleLine = true
            )

            Button(
                onClick = {
                    val guardado = gasto?.copy(
                        monto = valor,
                        categoriaId = categoriaId,
                        fecha = fecha,
                        nota = nota.trim(),
                        metodo = metodo
                    ) ?: Gasto(
                        monto = valor,
                        categoriaId = categoriaId,
                        fecha = fecha,
                        nota = nota.trim(),
                        metodo = metodo
                    )
                    if (gasto == null) Repositorio.agregarGasto(guardado)
                    else Repositorio.actualizarGasto(guardado)
                    onCerrar()
                },
                enabled = valido,
                modifier = Modifier.fillMaxWidth().height(52.dp)
            ) {
                Text(
                    if (valido) "Guardar ${Formato.monto(valor, simbolo)}" else "Guardar gasto",
                    style = MaterialTheme.typography.titleMedium
                )
            }

            if (gasto != null) {
                TextButton(
                    onClick = { confirmarBorrado = true },
                    modifier = Modifier.fillMaxWidth(),
                    colors = ButtonDefaults.textButtonColors(
                        contentColor = MaterialTheme.colorScheme.error
                    )
                ) {
                    Icon(Icons.Default.Delete, contentDescription = null)
                    Spacer(Modifier.width(8.dp))
                    Text("Eliminar gasto")
                }
            }
        }
    }

    if (mostrarCalendario) {
        val estadoFecha = rememberDatePickerState(
            initialSelectedDateMillis = fecha.atStartOfDay(ZoneOffset.UTC).toInstant().toEpochMilli()
        )
        DatePickerDialog(
            onDismissRequest = { mostrarCalendario = false },
            confirmButton = {
                TextButton(onClick = {
                    estadoFecha.selectedDateMillis?.let { millis ->
                        diaEpoca = Instant.ofEpochMilli(millis)
                            .atZone(ZoneOffset.UTC).toLocalDate().toEpochDay()
                    }
                    mostrarCalendario = false
                }) { Text("Listo") }
            },
            dismissButton = {
                TextButton(onClick = { mostrarCalendario = false }) { Text("Cancelar") }
            }
        ) {
            DatePicker(state = estadoFecha)
        }
    }

    if (confirmarBorrado && gasto != null) {
        AlertDialog(
            onDismissRequest = { confirmarBorrado = false },
            title = { Text("¿Eliminar este gasto?") },
            text = { Text("Se borrará ${Formato.monto(gasto.monto, simbolo)} del ${Formato.fechaCorta(gasto.fecha)}.") },
            confirmButton = {
                TextButton(onClick = {
                    Repositorio.eliminarGasto(gasto.id)
                    confirmarBorrado = false
                    onCerrar()
                }) { Text("Eliminar", color = MaterialTheme.colorScheme.error) }
            },
            dismissButton = {
                TextButton(onClick = { confirmarBorrado = false }) { Text("Cancelar") }
            }
        )
    }
}

@Composable
private fun ChipCategoria(
    categoria: Categoria,
    seleccionada: Boolean,
    onClick: () -> Unit
) {
    val color = Color(categoria.color)
    FilterChip(
        selected = seleccionada,
        onClick = onClick,
        label = { Text("${categoria.emoji} ${categoria.nombre}") },
        colors = FilterChipDefaults.filterChipColors(
            selectedContainerColor = color.copy(alpha = 0.25f),
            selectedLabelColor = MaterialTheme.colorScheme.onSurface
        ),
        border = FilterChipDefaults.filterChipBorder(
            enabled = true,
            selected = seleccionada,
            borderColor = color.copy(alpha = 0.45f),
            selectedBorderColor = color,
            selectedBorderWidth = 1.5.dp
        )
    )
}
