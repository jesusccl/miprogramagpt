package cl.augustogames.gastos.ui.componentes

import androidx.compose.foundation.Canvas
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.size
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.unit.dp
import cl.augustogames.gastos.data.TotalCategoria

/**
 * Anillo con la repartición del gasto por categoría.
 * En el centro se muestra el contenido que se le pase (normalmente el total).
 */
@Composable
fun GraficoDona(
    porciones: List<TotalCategoria>,
    modifier: Modifier = Modifier,
    diametro: Int = 190,
    colorVacio: Color = Color(0xFF9E9E9E),
    centro: @Composable () -> Unit
) {
    Box(
        modifier = modifier.size(diametro.dp),
        contentAlignment = Alignment.Center
    ) {
        Canvas(Modifier.size(diametro.dp)) {
            val grosor = size.minDimension * 0.15f
            val lado = size.minDimension - grosor
            val esquina = Offset((size.width - lado) / 2f, (size.height - lado) / 2f)
            val medidas = Size(lado, lado)
            val trazo = Stroke(width = grosor, cap = StrokeCap.Butt)

            if (porciones.isEmpty()) {
                drawArc(
                    color = colorVacio.copy(alpha = 0.20f),
                    startAngle = 0f,
                    sweepAngle = 360f,
                    useCenter = false,
                    topLeft = esquina,
                    size = medidas,
                    style = trazo
                )
                return@Canvas
            }

            // Con una sola categoría se dibuja el anillo completo, sin separación.
            val separacion = if (porciones.size > 1) 2.5f else 0f
            var angulo = -90f
            porciones.forEach { porcion ->
                val barrido = porcion.porcentaje * 360f
                drawArc(
                    color = Color(porcion.categoria.color),
                    startAngle = angulo + separacion / 2f,
                    sweepAngle = (barrido - separacion).coerceAtLeast(0.6f),
                    useCenter = false,
                    topLeft = esquina,
                    size = medidas,
                    style = trazo
                )
                angulo += barrido
            }
        }
        centro()
    }
}
