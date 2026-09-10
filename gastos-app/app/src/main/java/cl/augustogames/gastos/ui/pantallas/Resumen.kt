package cl.augustogames.gastos.ui.pantallas

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import cl.augustogames.gastos.data.Gasto
import cl.augustogames.gastos.data.Repositorio
import cl.augustogames.gastos.data.TotalCategoria
import cl.augustogames.gastos.ui.Formato
import cl.augustogames.gastos.ui.componentes.BarraProgreso
import cl.augustogames.gastos.ui.componentes.BurbujaCategoria
import cl.augustogames.gastos.ui.componentes.EstadoVacio
import cl.augustogames.gastos.ui.componentes.FilaGasto
import cl.augustogames.gastos.ui.componentes.GraficoDona
import cl.augustogames.gastos.ui.componentes.SelectorMes
import cl.augustogames.gastos.ui.componentes.Tarjeta
import java.time.LocalDate
import java.time.YearMonth
import kotlin.math.roundToInt

@Composable
fun PantallaResumen(
    mes: YearMonth,
    onCambiarMes: (YearMonth) -> Unit,
    onVerTodos: () -> Unit,
    onEditarGasto: (Gasto) -> Unit,
    modifier: Modifier = Modifier
) {
    val simbolo = Repositorio.ajustes.simbolo
    val gastosMes = Repositorio.gastos.filter { it.mes == mes }
    val total = gastosMes.sumOf { it.monto }
    val mesAnterior = mes.minusMonths(1)
    val totalAnterior = Repositorio.gastos.filter { it.mes == mesAnterior }.sumOf { it.monto }
    val porCategoria = Repositorio.totalesPorCategoria(gastosMes)
    val presupuestoTotal = Repositorio.categorias.sumOf { it.presupuesto }
    val hoy = LocalDate.now()
    val totalHoy = Repositorio.gastos.filter { it.fecha == hoy }.sumOf { it.monto }
    val diasConGasto = gastosMes.map { it.fecha }.distinct().size
    val promedioDiario = if (diasConGasto > 0) total / diasConGasto else 0L

    LazyColumn(
        modifier = modifier,
        contentPadding = PaddingValues(start = 16.dp, end = 16.dp, top = 4.dp, bottom = 104.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp)
    ) {
        item {
            SelectorMes(mes = mes, onCambiar = onCambiarMes)
        }

        item {
            Tarjeta {
                Column(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalAlignment = Alignment.CenterHorizontally
                ) {
                    GraficoDona(porciones = porCategoria) {
                        Column(horizontalAlignment = Alignment.CenterHorizontally) {
                            Text(
                                "Total del mes",
                                style = MaterialTheme.typography.labelMedium,
                                color = MaterialTheme.colorScheme.onSurfaceVariant
                            )
                            Text(
                                Formato.monto(total, simbolo),
                                style = MaterialTheme.typography.headlineSmall,
                                textAlign = TextAlign.Center
                            )
                            Text(
                                "${gastosMes.size} ${if (gastosMes.size == 1) "gasto" else "gastos"}",
                                style = MaterialTheme.typography.bodySmall,
                                color = MaterialTheme.colorScheme.onSurfaceVariant
                            )
                        }
                    }

                    Spacer(Modifier.height(12.dp))
                    ComparacionMesAnterior(total, totalAnterior, mesAnterior)

                    if (presupuestoTotal > 0) {
                        Spacer(Modifier.height(16.dp))
                        val usado = (total.toFloat() / presupuestoTotal).coerceAtLeast(0f)
                        val excedido = total > presupuestoTotal
                        Row(
                            modifier = Modifier.fillMaxWidth().padding(bottom = 6.dp),
                            horizontalArrangement = Arrangement.SpaceBetween
                        ) {
                            Text(
                                "Presupuesto del mes",
                                style = MaterialTheme.typography.bodyMedium,
                                color = MaterialTheme.colorScheme.onSurfaceVariant
                            )
                            Text(
                                "${Formato.monto(total, simbolo)} de ${Formato.monto(presupuestoTotal, simbolo)}",
                                style = MaterialTheme.typography.bodyMedium
                            )
                        }
                        BarraProgreso(
                            progreso = usado,
                            color = if (excedido) MaterialTheme.colorScheme.error
                            else MaterialTheme.colorScheme.primary,
                            alto = 10
                        )
                        Text(
                            text = if (excedido)
                                "Te pasaste por ${Formato.monto(total - presupuestoTotal, simbolo)}"
                            else "Te quedan ${Formato.monto(presupuestoTotal - total, simbolo)}",
                            style = MaterialTheme.typography.bodySmall,
                            color = if (excedido) MaterialTheme.colorScheme.error
                            else MaterialTheme.colorScheme.onSurfaceVariant,
                            modifier = Modifier.padding(top = 6.dp)
                        )
                    }
                }
            }
        }

        item {
            Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                Estadistica("Hoy", Formato.monto(totalHoy, simbolo), Modifier.weight(1f))
                Estadistica("Promedio por día", Formato.monto(promedioDiario, simbolo), Modifier.weight(1f))
            }
        }

        item {
            Tarjeta(titulo = "En qué se te fue") {
                if (porCategoria.isEmpty()) {
                    Text(
                        "Todavía no hay gastos en ${Formato.mesAnio(mes)}.",
                        style = MaterialTheme.typography.bodyMedium,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                } else {
                    porCategoria.forEachIndexed { indice, fila ->
                        if (indice > 0) HorizontalDivider(Modifier.padding(vertical = 4.dp))
                        FilaResumenCategoria(fila, simbolo)
                    }
                }
            }
        }

        if (gastosMes.isNotEmpty()) {
            item {
                Tarjeta(
                    titulo = "Últimos movimientos",
                    accion = { TextButton(onClick = onVerTodos) { Text("Ver todos") } }
                ) {
                    gastosMes.take(5).forEach { gasto ->
                        FilaGasto(
                            gasto = gasto,
                            simbolo = simbolo,
                            mostrarFecha = true,
                            onClick = { onEditarGasto(gasto) }
                        )
                    }
                }
            }
        } else {
            item {
                EstadoVacio(
                    emoji = "🧾",
                    titulo = "Sin gastos este mes",
                    detalle = "Toca el botón «Gasto» para registrar el primero: alimentación, bencina, deudas o la categoría que quieras."
                )
            }
        }
    }
}

@Composable
private fun ComparacionMesAnterior(total: Long, totalAnterior: Long, mesAnterior: YearMonth) {
    val nombreMes = Formato.mesAnio(mesAnterior).substringBefore(" ").lowercase()
    val texto = when {
        totalAnterior == 0L && total == 0L -> "Sin gastos en $nombreMes tampoco"
        totalAnterior == 0L -> "No hay gastos en $nombreMes para comparar"
        else -> {
            val variacion = ((total - totalAnterior) * 100.0 / totalAnterior).roundToInt()
            when {
                variacion > 0 -> "$variacion% más que en $nombreMes"
                variacion < 0 -> "${-variacion}% menos que en $nombreMes"
                else -> "Igual que en $nombreMes"
            }
        }
    }
    val color = when {
        totalAnterior == 0L -> MaterialTheme.colorScheme.onSurfaceVariant
        total > totalAnterior -> MaterialTheme.colorScheme.error
        total < totalAnterior -> Color(0xFF2E9E5B)
        else -> MaterialTheme.colorScheme.onSurfaceVariant
    }
    Text(texto, style = MaterialTheme.typography.bodyMedium, color = color)
}

@Composable
private fun Estadistica(titulo: String, valor: String, modifier: Modifier = Modifier) {
    Tarjeta(modifier = modifier) {
        Text(
            titulo,
            style = MaterialTheme.typography.labelMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant
        )
        Text(valor, style = MaterialTheme.typography.titleLarge)
    }
}

@Composable
private fun FilaResumenCategoria(fila: TotalCategoria, simbolo: String) {
    val color = Color(fila.categoria.color)
    val presupuesto = fila.categoria.presupuesto
    val excedido = presupuesto > 0 && fila.total > presupuesto

    Column(Modifier.fillMaxWidth().padding(vertical = 8.dp)) {
        Row(
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            BurbujaCategoria(fila.categoria.emoji, color, tamano = 38)
            Column(Modifier.weight(1f)) {
                Text(
                    fila.categoria.nombre,
                    style = MaterialTheme.typography.bodyLarge,
                    maxLines = 1,
                    overflow = TextOverflow.Ellipsis
                )
                Text(
                    buildString {
                        append("${(fila.porcentaje * 100).roundToInt()}%")
                        append(" · ${fila.cantidad} ${if (fila.cantidad == 1) "gasto" else "gastos"}")
                        if (presupuesto > 0) append(" · tope ${Formato.monto(presupuesto, simbolo)}")
                    },
                    style = MaterialTheme.typography.bodySmall,
                    color = if (excedido) MaterialTheme.colorScheme.error
                    else MaterialTheme.colorScheme.onSurfaceVariant
                )
            }
            Text(Formato.monto(fila.total, simbolo), style = MaterialTheme.typography.titleMedium)
        }
        Spacer(Modifier.height(8.dp))
        BarraProgreso(
            progreso = if (presupuesto > 0) fila.total.toFloat() / presupuesto else fila.porcentaje,
            color = if (excedido) MaterialTheme.colorScheme.error else color
        )
    }
}
