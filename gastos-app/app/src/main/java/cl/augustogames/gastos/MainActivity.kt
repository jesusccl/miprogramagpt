package cl.augustogames.gastos

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import cl.augustogames.gastos.data.Repositorio
import cl.augustogames.gastos.ui.AppGastos
import cl.augustogames.gastos.ui.theme.MisGastosTheme

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        Repositorio.inicializar(applicationContext)
        setContent {
            MisGastosTheme(tema = Repositorio.ajustes.tema) {
                AppGastos()
            }
        }
    }
}
