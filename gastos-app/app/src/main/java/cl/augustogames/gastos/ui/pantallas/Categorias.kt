package cl.augustogames.gastos.ui.pantallas

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ExperimentalLayoutApi
import androidx.compose.foundation.layout.FlowRow
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Add
import androidx.compose.material.icons.filled.Check
import androidx.compose.material.icons.filled.Edit
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.SegmentedButton
import androidx.compose.material3.SegmentedButtonDefaults
import androidx.compose.material3.SingleChoiceSegmentedButtonRow
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import cl.augustogames.gastos.data.Categoria
import cl.augustogames.gastos.data.PALETA_CATEGORIAS
import cl.augustogames.gastos.data.Repositorio
import cl.augustogames.gastos.data.TipoMovimiento
import cl.augustogames.gastos.data.emojisSugeridos
import cl.augustogames.gastos.data.idCategoriaComodin
import cl.augustogames.gastos.ui.Formato
import cl.augustogames.gastos.ui.componentes.BarraProgreso
import cl.augustogames.gastos.ui.componentes.BurbujaCategoria
import cl.augustogames.gastos.ui.componentes.CampoMonto
import cl.augustogames.gastos.ui.componentes.Tarjeta
import cl.augustogames.gastos.ui.theme.LocalColoresExtra
import java.time.YearMonth

@Composable
fun PantallaCategorias(mes: YearMonth, modifier: Modifier = Modifier) {
    var tipoNombre by rememberSaveable { mutableStateOf(TipoMovimiento.GASTO.name) }
    var idEnEdicion by rememberSaveable { mutableStateOf<String?>(null) }
    var creando by rememberSaveable { mutableStateOf(false) }

    val tipo = TipoMovimiento.desde(tipoNombre)
    val simbolo = Repositorio.ajustes.simbolo
    val delMes = Repositorio.movimientos.filter { it.mes == mes }
    val categorias = Repositorio.categorias.filter { it.tipo == tipo }
    val enEdicion = idEnEdicion?.let { id -> Repositorio.categorias.firstOrNull { it.id == id } }

    LazyColumn(
        modifier = modifier,
        contentPadding = PaddingValues(start = 16.dp, end = 16.dp, top = 4.dp, bottom = 32.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp)
    ) {
        item {
            SingleChoiceSegmentedButtonRow(Modifier.fillMaxWidth()) {
                TipoMovimiento.entries.forEachIndexed { indice, opcion ->
                    SegmentedButton(
                        selected = tipo == opcion,
                        onClick = { tipoNombre = opcion.name },
                        shape = SegmentedButtonDefaults.itemShape(indice, TipoMovimiento.entries.size),
                        label = { Text(opcion.plural) }
                    )
                }
            }
        }

        item {
            Text(
                if (tipo == TipoMovimiento.INGRESO)
                    "La meta mensual es opcional: sirve para ver cuánto llevas de lo que esperas recibir."
                else "Los presupuestos son mensuales. Deja el tope en cero si esa categoría no lo necesita.",
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
                modifier = Modifier.padding(horizontal = 4.dp, vertical = 4.dp)
            )
        }

        item {
            Button(
                onClick = { creando = true },
                modifier = Modifier.fillMaxWidth().height(48.dp)
            ) {
                Icon(Icons.Default.Add, contentDescription = null)
                Spacer(Modifier.size(8.dp))
                Text(
                    if (tipo == TipoMovimiento.INGRESO) "Nueva categoría de ingreso"
                    else "Nueva categoría de gasto"
                )
            }
        }

        items(items = categorias, key = { it.id }) { categoria ->
            val acumulado = delMes.filter { it.categoriaId == categoria.id }.sumOf { it.monto }
            TarjetaCategoria(
                categoria = categoria,
                acumulado = acumulado,
                simbolo = simbolo,
                mes = mes,
                onEditar = { idEnEdicion = categoria.id }
            )
        }

        item {
            OutlinedButton(
                onClick = { Repositorio.restablecerCategorias() },
                modifier = Modifier.fillMaxWidth()
            ) {
                Text("Recuperar categorías por defecto")
            }
        }
    }

    if (creando) {
        DialogoCategoria(categoria = null, tipo = tipo, simbolo = simbolo) { creando = false }
    }

    enEdicion?.let { categoria ->
        DialogoCategoria(categoria = categoria, tipo = categoria.tipo, simbolo = simbolo) {
            idEnEdicion = null
        }
    }
}

@Composable
private fun TarjetaCategoria(
    categoria: Categoria,
    acumulado: Long,
    simbolo: String,
    mes: YearMonth,
    onEditar: () -> Unit
) {
    val colores = LocalColoresExtra.current
    val esIngreso = categoria.tipo == TipoMovimiento.INGRESO
    val color = Color(categoria.color)
    val tope = categoria.presupuesto
    val excedido = !esIngreso && tope > 0 && acumulado > tope
    val metaLograda = esIngreso && tope > 0 && acumulado >= tope

    Tarjeta {
        Row(
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            BurbujaCategoria(categoria.emoji, color)
            Column(Modifier.weight(1f)) {
                Text(
                    categoria.nombre,
                    style = MaterialTheme.typography.titleSmall,
                    maxLines = 1,
                    overflow = TextOverflow.Ellipsis
                )
                Text(
                    if (tope > 0)
                        "${Formato.monto(acumulado, simbolo)} de ${Formato.monto(tope, simbolo)}"
                    else "${Formato.monto(acumulado, simbolo)} en ${Formato.mesAnio(mes).lowercase()}",
                    style = MaterialTheme.typography.bodySmall,
                    color = when {
                        excedido -> MaterialTheme.colorScheme.error
                        metaLograda -> colores.ingreso
                        else -> MaterialTheme.colorScheme.onSurfaceVariant
                    }
                )
            }
            IconButton(onClick = onEditar) {
                Icon(Icons.Default.Edit, contentDescription = "Editar ${categoria.nombre}")
            }
        }
        if (tope > 0) {
            Spacer(Modifier.height(10.dp))
            BarraProgreso(
                progreso = acumulado.toFloat() / tope,
                color = when {
                    excedido -> MaterialTheme.colorScheme.error
                    esIngreso -> colores.ingreso
                    else -> color
                }
            )
        }
    }
}

@OptIn(ExperimentalLayoutApi::class)
@Composable
private fun DialogoCategoria(
    categoria: Categoria?,
    tipo: TipoMovimiento,
    simbolo: String,
    onCerrar: () -> Unit
) {
    val emojis = emojisSugeridos(tipo)
    var nombre by rememberSaveable { mutableStateOf(categoria?.nombre.orEmpty()) }
    var emoji by rememberSaveable { mutableStateOf(categoria?.emoji ?: emojis.first()) }
    var color by rememberSaveable { mutableStateOf(categoria?.color ?: PALETA_CATEGORIAS.first()) }
    var tope by rememberSaveable {
        mutableStateOf(categoria?.presupuesto?.takeIf { it > 0 }?.toString() ?: "")
    }
    var confirmarBorrado by rememberSaveable { mutableStateOf(false) }

    val comodin = idCategoriaComodin(tipo)
    val esBorrable = categoria != null && categoria.id != comodin
    val enUso = categoria != null && Repositorio.movimientos.any { it.categoriaId == categoria.id }

    AlertDialog(
        onDismissRequest = onCerrar,
        title = {
            Text(
                if (categoria == null) "Nueva categoría de ${tipo.etiqueta.lowercase()}"
                else "Editar categoría"
            )
        },
        text = {
            Column(
                modifier = Modifier.verticalScroll(rememberScrollState()),
                verticalArrangement = Arrangement.spacedBy(14.dp)
            ) {
                OutlinedTextField(
                    value = nombre,
                    onValueChange = { nombre = it.take(28) },
                    label = { Text("Nombre") },
                    placeholder = {
                        Text(if (tipo == TipoMovimiento.INGRESO) "Ej: Sueldo" else "Ej: Bencina")
                    },
                    singleLine = true,
                    modifier = Modifier.fillMaxWidth()
                )

                CampoMonto(
                    texto = tope,
                    onCambio = { tope = it },
                    simbolo = simbolo,
                    etiqueta = if (tipo == TipoMovimiento.INGRESO) "Meta mensual (opcional)"
                    else "Tope mensual (opcional)",
                    marcador = "0",
                    modifier = Modifier.fillMaxWidth()
                )

                Text("Ícono", style = MaterialTheme.typography.labelLarge)
                OutlinedTextField(
                    value = emoji,
                    onValueChange = { emoji = it.take(4) },
                    label = { Text("Emoji") },
                    singleLine = true,
                    modifier = Modifier.fillMaxWidth()
                )
                FlowRow(
                    modifier = Modifier.heightIn(max = 140.dp),
                    horizontalArrangement = Arrangement.spacedBy(6.dp),
                    verticalArrangement = Arrangement.spacedBy(6.dp)
                ) {
                    emojis.forEach { opcion ->
                        Box(
                            modifier = Modifier
                                .size(40.dp)
                                .clip(CircleShape)
                                .background(
                                    if (opcion == emoji) Color(color).copy(alpha = 0.25f)
                                    else MaterialTheme.colorScheme.surfaceVariant
                                )
                                .clickable { emoji = opcion },
                            contentAlignment = Alignment.Center
                        ) {
                            Text(opcion, style = MaterialTheme.typography.titleMedium)
                        }
                    }
                }

                Text("Color", style = MaterialTheme.typography.labelLarge)
                FlowRow(
                    horizontalArrangement = Arrangement.spacedBy(8.dp),
                    verticalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    PALETA_CATEGORIAS.forEach { opcion ->
                        Box(
                            modifier = Modifier
                                .size(34.dp)
                                .clip(CircleShape)
                                .background(Color(opcion))
                                .border(
                                    width = if (opcion == color) 3.dp else 0.dp,
                                    color = MaterialTheme.colorScheme.onSurface,
                                    shape = CircleShape
                                )
                                .clickable { color = opcion },
                            contentAlignment = Alignment.Center
                        ) {
                            if (opcion == color) {
                                Icon(
                                    Icons.Default.Check,
                                    contentDescription = null,
                                    tint = Color.White
                                )
                            }
                        }
                    }
                }

                if (esBorrable) {
                    TextButton(
                        onClick = { confirmarBorrado = true },
                        colors = ButtonDefaults.textButtonColors(
                            contentColor = MaterialTheme.colorScheme.error
                        )
                    ) { Text("Eliminar categoría") }
                }
            }
        },
        confirmButton = {
            TextButton(
                enabled = nombre.isNotBlank(),
                onClick = {
                    val guardada = categoria?.copy(
                        nombre = nombre.trim(),
                        emoji = emoji.ifBlank { "📦" },
                        color = color,
                        presupuesto = tope.toLongOrNull() ?: 0L
                    ) ?: Categoria(
                        nombre = nombre.trim(),
                        emoji = emoji.ifBlank { "📦" },
                        color = color,
                        presupuesto = tope.toLongOrNull() ?: 0L,
                        tipo = tipo
                    )
                    Repositorio.guardarCategoria(guardada)
                    onCerrar()
                }
            ) { Text("Guardar") }
        },
        dismissButton = { TextButton(onClick = onCerrar) { Text("Cancelar") } },
        shape = RoundedCornerShape(24.dp)
    )

    if (confirmarBorrado && categoria != null) {
        val nombreComodin = Repositorio.categoria(comodin)?.nombre ?: "Otros"
        AlertDialog(
            onDismissRequest = { confirmarBorrado = false },
            title = { Text("¿Eliminar «${categoria.nombre}»?") },
            text = {
                Text(
                    if (enUso) "Los movimientos que tenía quedarán en «$nombreComodin»."
                    else "No tiene movimientos registrados, se puede borrar sin problema."
                )
            },
            confirmButton = {
                TextButton(onClick = {
                    Repositorio.eliminarCategoria(categoria.id)
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
