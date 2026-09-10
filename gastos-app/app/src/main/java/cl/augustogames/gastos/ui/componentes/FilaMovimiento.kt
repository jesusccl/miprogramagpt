package cl.augustogames.gastos.ui.componentes

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import cl.augustogames.gastos.data.Movimiento
import cl.augustogames.gastos.data.Repositorio
import cl.augustogames.gastos.ui.Formato
import cl.augustogames.gastos.ui.theme.LocalColoresExtra

/**
 * Una línea de la lista: categoría, detalle y monto.
 * Los ingresos se muestran en verde y con un "+" adelante.
 */
@Composable
fun FilaMovimiento(
    movimiento: Movimiento,
    simbolo: String,
    onClick: () -> Unit,
    mostrarFecha: Boolean = false,
    conSigno: Boolean = true,
    modifier: Modifier = Modifier
) {
    val categoria = Repositorio.categoriaODefecto(movimiento.categoriaId, movimiento.tipo)
    val detalle = buildList {
        if (movimiento.nota.isNotBlank()) add(movimiento.nota)
        add(movimiento.metodo.etiqueta)
        if (mostrarFecha) add(Formato.fechaCorta(movimiento.fecha))
    }.joinToString(" · ")

    Row(
        modifier = modifier
            .fillMaxWidth()
            .clickable(onClick = onClick)
            .padding(vertical = 10.dp),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(12.dp)
    ) {
        BurbujaCategoria(categoria.emoji, Color(categoria.color))
        Column(Modifier.weight(1f)) {
            Text(
                categoria.nombre,
                style = MaterialTheme.typography.bodyLarge,
                maxLines = 1,
                overflow = TextOverflow.Ellipsis
            )
            Text(
                detalle,
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
                maxLines = 1,
                overflow = TextOverflow.Ellipsis
            )
        }
        Text(
            text = if (conSigno) Formato.montoConSigno(movimiento.monto, movimiento.esIngreso, simbolo)
            else Formato.monto(movimiento.monto, simbolo),
            style = MaterialTheme.typography.titleMedium,
            color = if (movimiento.esIngreso) LocalColoresExtra.current.ingreso
            else MaterialTheme.colorScheme.onSurface
        )
    }
}
