package cl.augustogames.gastos.ui.pantallas

import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.rememberScrollState
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Clear
import androidx.compose.material.icons.filled.Search
import androidx.compose.material3.FilterChip
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.SegmentedButton
import androidx.compose.material3.SegmentedButtonDefaults
import androidx.compose.material3.SingleChoiceSegmentedButtonRow
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import cl.augustogames.gastos.data.Movimiento
import cl.augustogames.gastos.data.Repositorio
import cl.augustogames.gastos.data.TipoMovimiento
import cl.augustogames.gastos.ui.Formato
import cl.augustogames.gastos.ui.componentes.EstadoVacio
import cl.augustogames.gastos.ui.componentes.FilaMovimiento
import cl.augustogames.gastos.ui.componentes.SelectorMes
import cl.augustogames.gastos.ui.componentes.Tarjeta
import cl.augustogames.gastos.ui.theme.LocalColoresExtra
import java.time.YearMonth
import kotlin.math.abs

/** Qué se está mirando en el historial: todo, solo gastos o solo ingresos. */
private enum class Filtro(val etiqueta: String, val tipo: TipoMovimiento?) {
    TODO("Todo", null),
    GASTOS("Gastos", TipoMovimiento.GASTO),
    INGRESOS("Ingresos", TipoMovimiento.INGRESO)
}

@Composable
fun PantallaHistorial(
    mes: YearMonth,
    onCambiarMes: (YearMonth) -> Unit,
    onEditar: (Movimiento) -> Unit,
    modifier: Modifier = Modifier
) {
    var busqueda by rememberSaveable { mutableStateOf("") }
    var filtroCategoria by rememberSaveable { mutableStateOf<String?>(null) }
    var filtro by rememberSaveable { mutableStateOf(Filtro.TODO) }

    val colores = LocalColoresExtra.current
    val simbolo = Repositorio.ajustes.simbolo
    val delMes = Repositorio.movimientos.filter { it.mes == mes }
    val porTipo = delMes.filter { filtro.tipo == null || it.tipo == filtro.tipo }
    val categoriasPresentes = Repositorio.categorias.filter { categoria ->
        porTipo.any { it.categoriaId == categoria.id }
    }
    val texto = busqueda.trim().lowercase()
    val filtrados = porTipo.filter { movimiento ->
        val coincideCategoria = filtroCategoria == null || movimiento.categoriaId == filtroCategoria
        val coincideTexto = texto.isBlank() ||
            movimiento.nota.lowercase().contains(texto) ||
            Repositorio.categoriaODefecto(movimiento.categoriaId, movimiento.tipo)
                .nombre.lowercase().contains(texto) ||
            movimiento.monto.toString().contains(texto)
        coincideCategoria && coincideTexto
    }

    val gastosFiltrados = filtrados.filter { !it.esIngreso }.sumOf { it.monto }
    val ingresosFiltrados = filtrados.filter { it.esIngreso }.sumOf { it.monto }
    val porDia = filtrados.groupBy { it.fecha }.toList().sortedByDescending { it.first }

    LazyColumn(
        modifier = modifier,
        contentPadding = PaddingValues(start = 16.dp, end = 16.dp, top = 4.dp, bottom = 130.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp)
    ) {
        item { SelectorMes(mes = mes, onCambiar = onCambiarMes) }

        item {
            SingleChoiceSegmentedButtonRow(Modifier.fillMaxWidth()) {
                Filtro.entries.forEachIndexed { indice, opcion ->
                    SegmentedButton(
                        selected = filtro == opcion,
                        onClick = {
                            filtro = opcion
                            filtroCategoria = null
                        },
                        shape = SegmentedButtonDefaults.itemShape(indice, Filtro.entries.size),
                        label = { Text(opcion.etiqueta) }
                    )
                }
            }
        }

        item {
            OutlinedTextField(
                value = busqueda,
                onValueChange = { busqueda = it },
                modifier = Modifier.fillMaxWidth(),
                placeholder = { Text("Buscar por detalle o categoría") },
                leadingIcon = { Icon(Icons.Default.Search, contentDescription = null) },
                trailingIcon = {
                    if (busqueda.isNotEmpty()) {
                        IconButton(onClick = { busqueda = "" }) {
                            Icon(Icons.Default.Clear, contentDescription = "Limpiar búsqueda")
                        }
                    }
                },
                singleLine = true
            )
        }

        if (categoriasPresentes.isNotEmpty()) {
            item {
                Row(
                    modifier = Modifier.fillMaxWidth().horizontalScroll(rememberScrollState()),
                    horizontalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    FilterChip(
                        selected = filtroCategoria == null,
                        onClick = { filtroCategoria = null },
                        label = { Text("Todas") }
                    )
                    categoriasPresentes.forEach { categoria ->
                        FilterChip(
                            selected = filtroCategoria == categoria.id,
                            onClick = {
                                filtroCategoria =
                                    if (filtroCategoria == categoria.id) null else categoria.id
                            },
                            label = { Text("${categoria.emoji} ${categoria.nombre}") }
                        )
                    }
                }
            }
        }

        item {
            val neto = ingresosFiltrados - gastosFiltrados
            Row(
                modifier = Modifier.fillMaxWidth().padding(horizontal = 4.dp),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    "${filtrados.size} ${if (filtrados.size == 1) "movimiento" else "movimientos"}",
                    style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
                Text(
                    text = when (filtro) {
                        Filtro.GASTOS -> Formato.monto(gastosFiltrados, simbolo)
                        Filtro.INGRESOS -> "+${Formato.monto(ingresosFiltrados, simbolo)}"
                        Filtro.TODO -> Formato.montoConSigno(abs(neto), neto >= 0, simbolo)
                    },
                    style = MaterialTheme.typography.titleMedium,
                    color = when {
                        filtro == Filtro.INGRESOS -> colores.ingreso
                        filtro == Filtro.TODO && neto >= 0 && ingresosFiltrados > 0 -> colores.ingreso
                        else -> MaterialTheme.colorScheme.onSurface
                    }
                )
            }
        }

        if (porDia.isEmpty()) {
            item {
                EstadoVacio(
                    emoji = if (delMes.isEmpty()) "🧾" else "🔍",
                    titulo = if (delMes.isEmpty()) "Nada registrado en ${Formato.mesAnio(mes)}"
                    else "Nada coincide con la búsqueda",
                    detalle = if (delMes.isEmpty())
                        "Anota tu primer movimiento del mes con los botones de abajo."
                    else "Prueba con otro texto, otra categoría u otro filtro."
                )
            }
        }

        items(items = porDia, key = { (dia, _) -> dia.toString() }) { (dia, lista) ->
            val gastosDia = lista.filter { !it.esIngreso }.sumOf { it.monto }
            val ingresosDia = lista.filter { it.esIngreso }.sumOf { it.monto }
            val netoDia = ingresosDia - gastosDia
            Tarjeta {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text(Formato.etiquetaDia(dia), style = MaterialTheme.typography.titleSmall)
                    Text(
                        text = when {
                            ingresosDia == 0L -> Formato.monto(gastosDia, simbolo)
                            gastosDia == 0L -> "+${Formato.monto(ingresosDia, simbolo)}"
                            else -> Formato.montoConSigno(abs(netoDia), netoDia >= 0, simbolo)
                        },
                        style = MaterialTheme.typography.labelLarge,
                        color = if (ingresosDia > 0 && netoDia >= 0) colores.ingreso
                        else MaterialTheme.colorScheme.onSurfaceVariant
                    )
                }
                lista.forEachIndexed { indice, movimiento ->
                    if (indice > 0) HorizontalDivider()
                    FilaMovimiento(
                        movimiento = movimiento,
                        simbolo = simbolo,
                        onClick = { onEditar(movimiento) }
                    )
                }
            }
        }
    }
}
