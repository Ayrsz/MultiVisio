
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

class DroneFragment : Fragment() {

    companion object {

        private const val ARG_HEURE = "heure"
        private const val ARG_CAMERA = "camera"
        private const val ARG_CONFIANCE = "confiance"

        fun newInstance(
            heure: String,
            camera: String,
            confiance: String
        ): DroneFragment {

            return DroneFragment().apply {
                arguments = Bundle().apply {
                    putString(ARG_HEURE, heure)
                    putString(ARG_CAMERA, camera)
                    putString(ARG_CONFIANCE, confiance)
                }
            }
        }
    }

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
            text = "SUIVI DU DRONE"
            textSize = 26f
            setTextColor(Color.rgb(20, 34, 56))
            setTypeface(null, Typeface.BOLD)
        }

        contenu.addView(titre)

        val camera = arguments?.getString(ARG_CAMERA)
        val heure = arguments?.getString(ARG_HEURE)
        val confiance = arguments?.getString(ARG_CONFIANCE)

        val selection = if (camera != null) {
            """
            Alerte sélectionnée

            Caméra : $camera
            Heure : $heure
            Confiance IA : $confiance %
            """.trimIndent()
        } else {
            """
            Aucun drone sélectionné.

            Pour commencer le suivi, sélectionne une alerte
            dans l'onglet Alertes.
            """.trimIndent()
        }

        contenu.addView(
            creerCarte("INFORMATIONS DU DRONE", selection)
        )

        contenu.addView(
            creerCarte(
                "IMAGE DU DRONE",
                "🚁\n\nLa photographie du drone sera affichée ici."
            )
        )

        contenu.addView(
            creerCarte(
                "POSITION GPS ET CARTE SATELLITE",
                """
                📍

                Carte Google Maps à intégrer.

                Latitude : en attente
                Longitude : en attente

                Trajectoire GPS : en attente
                """.trimIndent()
            )
        )

        contenu.addView(
            creerCarte(
                "TÉLÉMÉTRIE",
                """
                Altitude : --
                Vitesse : --
                Dernière position : --
                """.trimIndent()
            )
        )

        val scrollView = ScrollView(contexte)
        scrollView.addView(contenu)

        return scrollView
    }

    private fun creerCarte(titre: String, texte: String): TextView {

        return TextView(requireContext()).apply {
            this.text = "$titre\n\n$texte"

            textSize = 16f
            setTextColor(Color.rgb(38, 54, 75))
            setPadding(dp(18), dp(20), dp(18), dp(20))

            background = GradientDrawable().apply {
                setColor(Color.WHITE)
                cornerRadius = dp(16).toFloat()
                setStroke(dp(1), Color.rgb(220, 228, 238))
            }

            elevation = dp(3).toFloat()
            gravity = Gravity.CENTER_VERTICAL

            val parametres = LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT,
                LinearLayout.LayoutParams.WRAP_CONTENT
            )

            parametres.bottomMargin = dp(16)
            layoutParams = parametres
        }
    }

    private fun dp(valeur: Int): Int {
        return (
                valeur * requireContext().resources.displayMetrics.density
                ).toInt()
    }
}
