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
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import cl.augustogames.gastos.data.Gasto
import cl.augustogames.gastos.data.Repositorio
import cl.augustogames.gastos.ui.Formato
import cl.augustogames.gastos.ui.componentes.EstadoVacio
import cl.augustogames.gastos.ui.componentes.FilaGasto
import cl.augustogames.gastos.ui.componentes.SelectorMes
import cl.augustogames.gastos.ui.componentes.Tarjeta
import java.time.YearMonth

@Composable
fun PantallaGastos(
    mes: YearMonth,
    onCambiarMes: (YearMonth) -> Unit,
    onEditarGasto: (Gasto) -> Unit,
    modifier: Modifier = Modifier
) {
    var busqueda by rememberSaveable { mutableStateOf("") }
    var filtroCategoria by rememberSaveable { mutableStateOf<String?>(null) }

    val simbolo = Repositorio.ajustes.simbolo
    val gastosMes = Repositorio.gastos.filter { it.mes == mes }
    val categoriasDelMes = Repositorio.categorias.filter { categoria ->
        gastosMes.any { it.categoriaId == categoria.id }
    }
    val texto = busqueda.trim().lowercase()
    val filtrados = gastosMes.filter { gasto ->
        val coincideCategoria = filtroCategoria == null || gasto.categoriaId == filtroCategoria
        val coincideTexto = texto.isBlank() ||
            gasto.nota.lowercase().contains(texto) ||
            Repositorio.categoriaODefecto(gasto.categoriaId).nombre.lowercase().contains(texto) ||
            gasto.monto.toString().contains(texto)
        coincideCategoria && coincideTexto
    }
    val totalFiltrado = filtrados.sumOf { it.monto }
    val porDia = filtrados.groupBy { it.fecha }.toList().sortedByDescending { it.first }

    LazyColumn(
        modifier = modifier,
        contentPadding = PaddingValues(start = 16.dp, end = 16.dp, top = 4.dp, bottom = 104.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp)
    ) {
        item { SelectorMes(mes = mes, onCambiar = onCambiarMes) }

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

        if (categoriasDelMes.isNotEmpty()) {
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
                    categoriasDelMes.forEach { categoria ->
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
            Row(
                modifier = Modifier.fillMaxWidth().padding(horizontal = 4.dp),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    "${filtrados.size} ${if (filtrados.size == 1) "gasto" else "gastos"}",
                    style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
                Text(
                    Formato.monto(totalFiltrado, simbolo),
                    style = MaterialTheme.typography.titleMedium
                )
            }
        }

        if (porDia.isEmpty()) {
            item {
                EstadoVacio(
                    emoji = if (gastosMes.isEmpty()) "🧾" else "🔍",
                    titulo = if (gastosMes.isEmpty()) "Nada registrado en ${Formato.mesAnio(mes)}"
                    else "Ningún gasto coincide",
                    detalle = if (gastosMes.isEmpty())
                        "Agrega tu primer gasto del mes con el botón «Gasto»."
                    else "Prueba con otro texto o quita el filtro de categoría."
                )
            }
        }

        items(items = porDia, key = { (dia, _) -> dia.toString() }) { (dia, lista) ->
            Tarjeta {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text(Formato.etiquetaDia(dia), style = MaterialTheme.typography.titleSmall)
                    Text(
                        Formato.monto(lista.sumOf { it.monto }, simbolo),
                        style = MaterialTheme.typography.labelLarge,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                }
                lista.forEachIndexed { indice, gasto ->
                    if (indice > 0) HorizontalDivider()
                    FilaGasto(
                        gasto = gasto,
                        simbolo = simbolo,
                        onClick = { onEditarGasto(gasto) }
                    )
                }
            }
        }
    }
}
