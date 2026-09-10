package cl.augustogames.gastos.ui.theme

import android.app.Activity
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Typography
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.SideEffect
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalView
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.sp
import androidx.core.view.WindowCompat
import cl.augustogames.gastos.data.Tema

private val Violeta = Color(0xFF6D3BF5)
private val VioletaClaro = Color(0xFFCFC0FF)
private val Turquesa = Color(0xFF1FB6C9)
private val Coral = Color(0xFFFF6B6B)

private val EsquemaClaro = lightColorScheme(
    primary = Violeta,
    onPrimary = Color.White,
    primaryContainer = Color(0xFFE7DEFF),
    onPrimaryContainer = Color(0xFF20005C),
    secondary = Turquesa,
    onSecondary = Color.White,
    secondaryContainer = Color(0xFFC9F2F7),
    onSecondaryContainer = Color(0xFF00363C),
    tertiary = Coral,
    onTertiary = Color.White,
    background = Color(0xFFF7F5FF),
    onBackground = Color(0xFF1B1A22),
    surface = Color(0xFFFFFFFF),
    onSurface = Color(0xFF1B1A22),
    surfaceVariant = Color(0xFFEDE9F7),
    onSurfaceVariant = Color(0xFF4A4658),
    outline = Color(0xFFCBC5DA),
    outlineVariant = Color(0xFFE3DFF0),
    error = Color(0xFFBA1A1A),
    onError = Color.White
)

private val EsquemaOscuro = darkColorScheme(
    primary = VioletaClaro,
    onPrimary = Color(0xFF33108C),
    primaryContainer = Color(0xFF4A22C4),
    onPrimaryContainer = Color(0xFFEADDFF),
    secondary = Color(0xFF6EDCEC),
    onSecondary = Color(0xFF00363C),
    secondaryContainer = Color(0xFF004F57),
    onSecondaryContainer = Color(0xFFC9F2F7),
    tertiary = Color(0xFFFF8F8F),
    onTertiary = Color(0xFF5F1414),
    background = Color(0xFF0F0D1C),
    onBackground = Color(0xFFE7E3F3),
    surface = Color(0xFF171528),
    onSurface = Color(0xFFE7E3F3),
    surfaceVariant = Color(0xFF232038),
    onSurfaceVariant = Color(0xFFB5AFC9),
    outline = Color(0xFF4B4663),
    outlineVariant = Color(0xFF2C2942),
    error = Color(0xFFFFB4AB),
    onError = Color(0xFF690005)
)

private val Tipografia = Typography().let { base ->
    base.copy(
        displaySmall = base.displaySmall.copy(fontWeight = FontWeight.Bold),
        headlineMedium = base.headlineMedium.copy(fontWeight = FontWeight.Bold),
        titleLarge = base.titleLarge.copy(fontWeight = FontWeight.Bold),
        titleMedium = base.titleMedium.copy(fontWeight = FontWeight.SemiBold),
        labelLarge = TextStyle(fontWeight = FontWeight.SemiBold, fontSize = 14.sp)
    )
}

@Composable
fun MisGastosTheme(tema: Tema, contenido: @Composable () -> Unit) {
    val oscuro = when (tema) {
        Tema.SISTEMA -> isSystemInDarkTheme()
        Tema.CLARO -> false
        Tema.OSCURO -> true
    }
    val esquema = if (oscuro) EsquemaOscuro else EsquemaClaro

    val vista = LocalView.current
    if (!vista.isInEditMode) {
        val contexto = LocalContext.current
        SideEffect {
            val ventana = (contexto as? Activity)?.window ?: return@SideEffect
            WindowCompat.getInsetsController(ventana, vista).apply {
                isAppearanceLightStatusBars = !oscuro
                isAppearanceLightNavigationBars = !oscuro
            }
        }
    }

    MaterialTheme(colorScheme = esquema, typography = Tipografia, content = contenido)
}
