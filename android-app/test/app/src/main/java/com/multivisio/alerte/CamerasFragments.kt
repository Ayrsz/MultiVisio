
package com.multivisio.alerte

import android.graphics.Color
import android.graphics.Typeface
import android.graphics.drawable.GradientDrawable
import android.os.Bundle
import android.view.Gravity
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.LinearLayout
import android.widget.ScrollView
import android.widget.TextView
import androidx.fragment.app.Fragment

class CamerasFragment : Fragment() {

    override fun onCreateView(
        inflater: LayoutInflater,
        container: ViewGroup?,
        savedInstanceState: Bundle?
    ): View {

        val contexte = requireContext()

        val contenu = LinearLayout(contexte).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(dp(18), dp(20), dp(18), dp(24))
        }

        val titre = TextView(contexte).apply {
            text = "CAMÉRAS"
            textSize = 26f
            setTypeface(null, Typeface.BOLD)
            setTextColor(Color.rgb(20, 34, 56))
        }

        contenu.addView(titre)

        val sousTitre = TextView(contexte).apply {
            text = "Surveillance des trois flux vidéo"
            textSize = 14f
            setTextColor(Color.rgb(105, 120, 142))
            setPadding(0, dp(5), 0, dp(20))
        }

        contenu.addView(sousTitre)

        // Création des trois emplacements vidéo
        for (numero in 1..3) {

            val carte = TextView(contexte).apply {
                text = """
                    CAMÉRA 0$numero

                    📹

                    Flux vidéo en attente de connexion

                    Le lecteur vidéo sera intégré ici.
                """.trimIndent()

                textSize = 16f
                setTextColor(Color.rgb(38, 54, 75))
                setPadding(dp(18), dp(20), dp(18), dp(20))
                gravity = Gravity.CENTER

                background = GradientDrawable().apply {
                    setColor(Color.WHITE)
                    cornerRadius = dp(16).toFloat()
                    setStroke(dp(1), Color.rgb(220, 228, 238))
                }

                elevation = dp(3).toFloat()
            }

            val parametres = LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT,
                dp(210)
            )

            parametres.bottomMargin = dp(16)

            contenu.addView(carte, parametres)
        }

        val scrollView = ScrollView(contexte)
        scrollView.addView(contenu)

        return scrollView
    }

    private fun dp(valeur: Int): Int {
        return (valeur * requireContext().resources.displayMetrics.density).toInt()
    }
}
