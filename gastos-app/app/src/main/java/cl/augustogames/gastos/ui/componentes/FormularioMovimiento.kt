package cl.augustogames.gastos.ui.componentes

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ExperimentalLayoutApi
import androidx.compose.foundation.layout.FlowRow
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.imePadding
import androidx.compose.foundation.layout.navigationBarsPadding
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
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
import androidx.compose.material3.SegmentedButton
import androidx.compose.material3.SegmentedButtonDefaults
import androidx.compose.material3.SingleChoiceSegmentedButtonRow
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
import cl.augustogames.gastos.data.MetodoPago
import cl.augustogames.gastos.data.Movimiento
import cl.augustogames.gastos.data.Repositorio
import cl.augustogames.gastos.data.TipoMovimiento
import cl.augustogames.gastos.ui.Formato
import cl.augustogames.gastos.ui.theme.LocalColoresExtra
import java.time.Instant
import java.time.LocalDate
import java.time.ZoneOffset

private val MONTOS_RAPIDOS = listOf(1_000L, 2_000L, 5_000L, 10_000L, 20_000L)

/**
 * Hoja para crear o editar un movimiento (gasto o ingreso).
 *
 * @param movimiento null para crear uno nuevo; si viene con datos, se edita ese.
 * @param tipoInicial con qué pestaña se abre el formulario al crear.
 * @param fechaSugerida fecha con la que se abre el formulario al crear.
 */
@OptIn(ExperimentalMaterial3Api::class, ExperimentalLayoutApi::class)
@Composable
fun FormularioMovimiento(
    movimiento: Movimiento?,
    tipoInicial: TipoMovimiento,
    fechaSugerida: LocalDate,
    onCerrar: () -> Unit
) {
    val estadoHoja = rememberModalBottomSheetState(skipPartiallyExpanded = true)
    val colores = LocalColoresExtra.current
    val simbolo = Repositorio.ajustes.simbolo

    // Se guarda con rememberSaveable (y en tipos simples) para no perder lo escrito
    // si el teléfono se rota o Android recrea la pantalla.
    var tipoNombre by rememberSaveable {
        mutableStateOf((movimiento?.tipo ?: tipoInicial).name)
    }
    var monto by rememberSaveable {
        mutableStateOf(movimiento?.monto?.takeIf { it > 0 }?.toString() ?: "")
    }
    var categoriaId by rememberSaveable { mutableStateOf(movimiento?.categoriaId.orEmpty()) }
    var diaEpoca by rememberSaveable {
        mutableStateOf((movimiento?.fecha ?: fechaSugerida).toEpochDay())
    }
    var nota by rememberSaveable { mutableStateOf(movimiento?.nota.orEmpty()) }
    var metodoNombre by rememberSaveable {
        mutableStateOf((movimiento?.metodo ?: MetodoPago.EFECTIVO).name)
    }
    var mostrarCalendario by rememberSaveable { mutableStateOf(false) }
    var confirmarBorrado by rememberSaveable { mutableStateOf(false) }

    val tipo = TipoMovimiento.desde(tipoNombre)
    val esIngreso = tipo == TipoMovimiento.INGRESO
    val fecha = LocalDate.ofEpochDay(diaEpoca)
    val categorias = Repositorio.categoriasDe(tipo)
    val metodos = MetodoPago.para(tipo)
    val metodo = MetodoPago.desde(metodoNombre).let { if (it in metodos) it else MetodoPago.EFECTIVO }

    // Al cambiar de gasto a ingreso (o al revés) la categoría elegida ya no sirve.
    val categoriaElegida = categorias.firstOrNull { it.id == categoriaId }
        ?: categorias.firstOrNull()
    val valor = monto.toLongOrNull() ?: 0L
    val valido = valor > 0 && categoriaElegida != null
    val hoy = LocalDate.now()

    val colorAcento = if (esIngreso) colores.ingreso else MaterialTheme.colorScheme.primary

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
                text = if (movimiento == null) "Nuevo movimiento"
                else "Editar ${tipo.etiqueta.lowercase()}",
                style = MaterialTheme.typography.titleLarge
            )

            SingleChoiceSegmentedButtonRow(Modifier.fillMaxWidth()) {
                TipoMovimiento.entries.forEachIndexed { indice, opcion ->
                    SegmentedButton(
                        selected = tipo == opcion,
                        onClick = { tipoNombre = opcion.name },
                        shape = SegmentedButtonDefaults.itemShape(indice, TipoMovimiento.entries.size),
                        colors = SegmentedButtonDefaults.colors(
                            activeContainerColor = if (opcion == TipoMovimiento.INGRESO)
                                colores.ingresoSuave else MaterialTheme.colorScheme.primaryContainer,
                            activeContentColor = if (opcion == TipoMovimiento.INGRESO)
                                colores.ingreso else MaterialTheme.colorScheme.onPrimaryContainer
                        ),
                        label = {
                            Text(if (opcion == TipoMovimiento.INGRESO) "Ingreso 💰" else "Gasto 🧾")
                        }
                    )
                }
            }

            CampoMonto(
                texto = monto,
                onCambio = { monto = it },
                simbolo = simbolo,
                etiqueta = if (esIngreso) "Cuánto entró" else "Cuánto gastaste",
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
                        seleccionada = categoria.id == categoriaElegida?.id,
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

            Text(
                if (esIngreso) "Cómo lo recibiste" else "Forma de pago",
                style = MaterialTheme.typography.titleMedium
            )
            FlowRow(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                metodos.forEach { opcion ->
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
                placeholder = {
                    Text(
                        if (esIngreso) "Ej: sueldo de septiembre"
                        else "Ej: supermercado de la semana"
                    )
                },
                singleLine = true
            )

            Button(
                onClick = {
                    val idCategoria = categoriaElegida?.id ?: return@Button
                    val guardado = movimiento?.copy(
                        monto = valor,
                        categoriaId = idCategoria,
                        fecha = fecha,
                        nota = nota.trim(),
                        metodo = metodo,
                        tipo = tipo
                    ) ?: Movimiento(
                        monto = valor,
                        categoriaId = idCategoria,
                        fecha = fecha,
                        nota = nota.trim(),
                        metodo = metodo,
                        tipo = tipo
                    )
                    if (movimiento == null) Repositorio.agregarMovimiento(guardado)
                    else Repositorio.actualizarMovimiento(guardado)
                    onCerrar()
                },
                enabled = valido,
                colors = ButtonDefaults.buttonColors(
                    containerColor = colorAcento,
                    contentColor = if (esIngreso) colores.sobreIngreso
                    else MaterialTheme.colorScheme.onPrimary
                ),
                modifier = Modifier.fillMaxWidth().height(52.dp)
            ) {
                Text(
                    if (valido) "Guardar ${Formato.monto(valor, simbolo)}"
                    else "Guardar ${tipo.etiqueta.lowercase()}",
                    style = MaterialTheme.typography.titleMedium
                )
            }

            if (movimiento != null) {
                TextButton(
                    onClick = { confirmarBorrado = true },
                    modifier = Modifier.fillMaxWidth(),
                    colors = ButtonDefaults.textButtonColors(
                        contentColor = MaterialTheme.colorScheme.error
                    )
                ) {
                    Icon(Icons.Default.Delete, contentDescription = null)
                    Spacer(Modifier.width(8.dp))
                    Text("Eliminar ${movimiento.tipo.etiqueta.lowercase()}")
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

    if (confirmarBorrado && movimiento != null) {
        AlertDialog(
            onDismissRequest = { confirmarBorrado = false },
            title = { Text("¿Eliminar este ${movimiento.tipo.etiqueta.lowercase()}?") },
            text = {
                Text(
                    "Se borrará ${Formato.monto(movimiento.monto, simbolo)} " +
                        "del ${Formato.fechaCorta(movimiento.fecha)}."
                )
            },
            confirmButton = {
                TextButton(onClick = {
                    Repositorio.eliminarMovimiento(movimiento.id)
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
