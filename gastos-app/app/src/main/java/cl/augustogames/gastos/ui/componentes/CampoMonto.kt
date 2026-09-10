package cl.augustogames.gastos.ui.componentes

import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.AnnotatedString
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.input.OffsetMapping
import androidx.compose.ui.text.input.TransformedText
import androidx.compose.ui.text.input.VisualTransformation
import androidx.compose.ui.text.style.TextAlign

/** Muestra los dígitos escritos agrupados de a tres: 12500 → 12.500 */
internal object SeparadorMiles : VisualTransformation {
    override fun filter(text: AnnotatedString): TransformedText {
        val digitos = text.text
        val formateado = if (digitos.isEmpty()) "" else
            digitos.reversed().chunked(3).joinToString(".").reversed()
        val mapeo = object : OffsetMapping {
            override fun originalToTransformed(offset: Int): Int {
                if (digitos.isEmpty()) return 0
                val aLaDerecha = digitos.length - offset.coerceIn(0, digitos.length)
                val separadores = if (aLaDerecha <= 0) 0 else (aLaDerecha - 1) / 3
                return (formateado.length - aLaDerecha - separadores).coerceIn(0, formateado.length)
            }

            override fun transformedToOriginal(offset: Int): Int =
                formateado.take(offset.coerceIn(0, formateado.length))
                    .count { it.isDigit() }
                    .coerceIn(0, digitos.length)
        }
        return TransformedText(AnnotatedString(formateado), mapeo)
    }
}

/** Campo numérico de dinero: solo dígitos, con separador de miles y símbolo de moneda. */
@Composable
fun CampoMonto(
    texto: String,
    onCambio: (String) -> Unit,
    simbolo: String,
    etiqueta: String,
    modifier: Modifier = Modifier,
    grande: Boolean = false,
    marcador: String? = null
) {
    val estilo = if (grande) MaterialTheme.typography.headlineSmall
    else MaterialTheme.typography.bodyLarge
    OutlinedTextField(
        value = texto,
        onValueChange = { nuevo -> onCambio(nuevo.filter { it.isDigit() }.trimStart('0').take(11)) },
        modifier = modifier,
        label = { Text(etiqueta) },
        placeholder = marcador?.let { { Text(it) } },
        prefix = { Text(simbolo, style = estilo) },
        textStyle = estilo.copy(textAlign = TextAlign.End),
        singleLine = true,
        visualTransformation = SeparadorMiles,
        keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number)
    )
}
