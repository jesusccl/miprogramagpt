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
import cl.augustogames.gastos.data.Movimiento
import cl.augustogames.gastos.data.Repositorio
import cl.augustogames.gastos.data.TipoMovimiento
import cl.augustogames.gastos.data.TotalCategoria
import cl.augustogames.gastos.ui.Formato
import cl.augustogames.gastos.ui.componentes.BarraProgreso
import cl.augustogames.gastos.ui.componentes.BurbujaCategoria
import cl.augustogames.gastos.ui.componentes.EstadoVacio
import cl.augustogames.gastos.ui.componentes.FilaMovimiento
import cl.augustogames.gastos.ui.componentes.GraficoDona
import cl.augustogames.gastos.ui.componentes.SelectorMes
import cl.augustogames.gastos.ui.componentes.Tarjeta
import cl.augustogames.gastos.ui.theme.LocalColoresExtra
import java.time.LocalDate
import java.time.YearMonth
import kotlin.math.roundToInt

@Composable
fun PantallaResumen(
    mes: YearMonth,
    onCambiarMes: (YearMonth) -> Unit,
    onVerTodos: () -> Unit,
    onEditar: (Movimiento) -> Unit,
    modifier: Modifier = Modifier
) {
    val colores = LocalColoresExtra.current
    val simbolo = Repositorio.ajustes.simbolo
    val delMes = Repositorio.movimientos.filter { it.mes == mes }
    val gastos = delMes.filter { it.tipo == TipoMovimiento.GASTO }
    val ingresos = delMes.filter { it.tipo == TipoMovimiento.INGRESO }
    val balance = Repositorio.balanceDe(mes)

    val mesAnterior = mes.minusMonths(1)
    val gastoAnterior = Repositorio.totalDe(mesAnterior, TipoMovimiento.GASTO)
    val gastosPorCategoria = Repositorio.totalesPorCategoria(gastos)
    val ingresosPorCategoria = Repositorio.totalesPorCategoria(ingresos)
    val presupuestoTotal = Repositorio.categoriasDe(TipoMovimiento.GASTO).sumOf { it.presupuesto }

    val hoy = LocalDate.now()
    val gastoHoy = Repositorio.gastoDelDia(hoy)
    val diasConGasto = gastos.map { it.fecha }.distinct().size
    val promedioDiario = if (diasConGasto > 0) balance.gastos / diasConGasto else 0L

    LazyColumn(
        modifier = modifier,
        contentPadding = PaddingValues(start = 16.dp, end = 16.dp, top = 4.dp, bottom = 130.dp),
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
                    GraficoDona(porciones = gastosPorCategoria) {
                        Column(horizontalAlignment = Alignment.CenterHorizontally) {
                            Text(
                                "Gastos del mes",
                                style = MaterialTheme.typography.labelMedium,
                                color = MaterialTheme.colorScheme.onSurfaceVariant
                            )
                            Text(
                                Formato.monto(balance.gastos, simbolo),
                                style = MaterialTheme.typography.headlineSmall,
                                textAlign = TextAlign.Center
                            )
                            Text(
                                "${gastos.size} ${if (gastos.size == 1) "gasto" else "gastos"}",
                                style = MaterialTheme.typography.bodySmall,
                                color = MaterialTheme.colorScheme.onSurfaceVariant
                            )
                        }
                    }

                    Spacer(Modifier.height(12.dp))
                    ComparacionMesAnterior(balance.gastos, gastoAnterior, mesAnterior)

                    Spacer(Modifier.height(16.dp))
                    HorizontalDivider()
                    Spacer(Modifier.height(12.dp))

                    Row(modifier = Modifier.fillMaxWidth()) {
                        Numero(
                            titulo = "Ingresos",
                            valor = "+${Formato.monto(balance.ingresos, simbolo)}",
                            color = colores.ingreso,
                            modifier = Modifier.weight(1f)
                        )
                        Numero(
                            titulo = if (balance.enVerde) "Te queda" else "Te falta",
                            valor = Formato.monto(kotlin.math.abs(balance.balance), simbolo),
                            color = if (balance.enVerde) colores.ingreso
                            else MaterialTheme.colorScheme.error,
                            modifier = Modifier.weight(1f)
                        )
                    }

                    if (balance.ingresos > 0) {
                        Spacer(Modifier.height(14.dp))
                        BarraProgreso(
                            progreso = balance.proporcionGastada,
                            color = if (balance.enVerde) colores.ingreso
                            else MaterialTheme.colorScheme.error,
                            alto = 10
                        )
                        Text(
                            text = "Llevas gastado el ${(balance.proporcionGastada * 100).roundToInt()}% " +
                                "de lo que entró este mes",
                            style = MaterialTheme.typography.bodySmall,
                            color = MaterialTheme.colorScheme.onSurfaceVariant,
                            textAlign = TextAlign.Center,
                            modifier = Modifier.padding(top = 8.dp)
                        )
                    }

                    if (presupuestoTotal > 0) {
                        Spacer(Modifier.height(16.dp))
                        val excedido = balance.gastos > presupuestoTotal
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
                                Formato.monto(presupuestoTotal, simbolo),
                                style = MaterialTheme.typography.bodyMedium
                            )
                        }
                        BarraProgreso(
                            progreso = balance.gastos.toFloat() / presupuestoTotal,
                            color = if (excedido) MaterialTheme.colorScheme.error
                            else MaterialTheme.colorScheme.primary,
                            alto = 10
                        )
                        Text(
                            text = if (excedido)
                                "Te pasaste por ${Formato.monto(balance.gastos - presupuestoTotal, simbolo)}"
                            else "Te quedan ${Formato.monto(presupuestoTotal - balance.gastos, simbolo)} de presupuesto",
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
                Tarjeta(modifier = Modifier.weight(1f)) {
                    Numero("Gastado hoy", Formato.monto(gastoHoy, simbolo))
                }
                Tarjeta(modifier = Modifier.weight(1f)) {
                    Numero("Promedio por día", Formato.monto(promedioDiario, simbolo))
                }
            }
        }

        item {
            Tarjeta(titulo = "En qué se te fue") {
                if (gastosPorCategoria.isEmpty()) {
                    Text(
                        "Todavía no hay gastos en ${Formato.mesAnio(mes).lowercase()}.",
                        style = MaterialTheme.typography.bodyMedium,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                } else {
                    gastosPorCategoria.forEachIndexed { indice, fila ->
                        if (indice > 0) HorizontalDivider(Modifier.padding(vertical = 4.dp))
                        FilaResumenCategoria(fila, simbolo)
                    }
                }
            }
        }

        if (ingresosPorCategoria.isNotEmpty()) {
            item {
                Tarjeta(titulo = "De dónde vino la plata") {
                    ingresosPorCategoria.forEachIndexed { indice, fila ->
                        if (indice > 0) HorizontalDivider(Modifier.padding(vertical = 4.dp))
                        FilaResumenCategoria(fila, simbolo, esIngreso = true)
                    }
                }
            }
        }

        if (delMes.isNotEmpty()) {
            item {
                Tarjeta(
                    titulo = "Últimos movimientos",
                    accion = { TextButton(onClick = onVerTodos) { Text("Ver todos") } }
                ) {
                    delMes.take(5).forEach { movimiento ->
                        FilaMovimiento(
                            movimiento = movimiento,
                            simbolo = simbolo,
                            mostrarFecha = true,
                            onClick = { onEditar(movimiento) }
                        )
                    }
                }
            }
        } else {
            item {
                EstadoVacio(
                    emoji = "🧾",
                    titulo = "Sin movimientos este mes",
                    detalle = "Con el botón «Gasto» anotas lo que sale y con el 💰 lo que entra."
                )
            }
        }
    }
}

@Composable
private fun ComparacionMesAnterior(gastos: Long, gastosAnteriores: Long, mesAnterior: YearMonth) {
    val nombreMes = Formato.mesAnio(mesAnterior).substringBefore(" ").lowercase()
    val texto = when {
        gastosAnteriores == 0L && gastos == 0L -> "Sin gastos en $nombreMes tampoco"
        gastosAnteriores == 0L -> "No hay gastos en $nombreMes para comparar"
        else -> {
            val variacion = ((gastos - gastosAnteriores) * 100.0 / gastosAnteriores).roundToInt()
            when {
                variacion > 0 -> "$variacion% más que en $nombreMes"
                variacion < 0 -> "${-variacion}% menos que en $nombreMes"
                else -> "Igual que en $nombreMes"
            }
        }
    }
    val color = when {
        gastosAnteriores == 0L -> MaterialTheme.colorScheme.onSurfaceVariant
        gastos > gastosAnteriores -> MaterialTheme.colorScheme.error
        gastos < gastosAnteriores -> LocalColoresExtra.current.ingreso
        else -> MaterialTheme.colorScheme.onSurfaceVariant
    }
    Text(texto, style = MaterialTheme.typography.bodyMedium, color = color)
}

@Composable
private fun Numero(
    titulo: String,
    valor: String,
    color: Color = Color.Unspecified,
    modifier: Modifier = Modifier
) {
    Column(modifier) {
        Text(
            titulo,
            style = MaterialTheme.typography.labelMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant
        )
        Text(
            valor,
            style = MaterialTheme.typography.titleLarge,
            color = if (color == Color.Unspecified) MaterialTheme.colorScheme.onSurface else color,
            maxLines = 1,
            overflow = TextOverflow.Ellipsis
        )
    }
}

@Composable
private fun FilaResumenCategoria(
    fila: TotalCategoria,
    simbolo: String,
    esIngreso: Boolean = false
) {
    val colores = LocalColoresExtra.current
    val color = Color(fila.categoria.color)
    val tope = fila.categoria.presupuesto
    val excedido = !esIngreso && tope > 0 && fila.total > tope
    val metaLograda = esIngreso && tope > 0 && fila.total >= tope

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
                        append(" · ${fila.cantidad} ${if (fila.cantidad == 1) "movimiento" else "movimientos"}")
                        if (tope > 0) {
                            append(if (esIngreso) " · meta " else " · tope ")
                            append(Formato.monto(tope, simbolo))
                        }
                    },
                    style = MaterialTheme.typography.bodySmall,
                    color = when {
                        excedido -> MaterialTheme.colorScheme.error
                        metaLograda -> colores.ingreso
                        else -> MaterialTheme.colorScheme.onSurfaceVariant
                    }
                )
            }
            Text(
                text = if (esIngreso) "+${Formato.monto(fila.total, simbolo)}"
                else Formato.monto(fila.total, simbolo),
                style = MaterialTheme.typography.titleMedium,
                color = if (esIngreso) colores.ingreso else MaterialTheme.colorScheme.onSurface
            )
        }
        Spacer(Modifier.height(8.dp))
        BarraProgreso(
            progreso = if (tope > 0) fila.total.toFloat() / tope else fila.porcentaje,
            color = when {
                excedido -> MaterialTheme.colorScheme.error
                esIngreso -> colores.ingreso
                else -> color
            }
        )
    }
}
