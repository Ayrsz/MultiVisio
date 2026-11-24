
package com.multivisio.alerte

import android.graphics.Color
import android.os.Bundle
import android.widget.LinearLayout
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity
import androidx.fragment.app.Fragment

class MainActivity : AppCompatActivity() {

    private lateinit var navAlertes: LinearLayout
    private lateinit var navCameras: LinearLayout
    private lateinit var navDrone: LinearLayout

    private lateinit var labelAlertes: TextView
    private lateinit var labelCameras: TextView
    private lateinit var labelDrone: TextView

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        // Récupération des trois boutons de navigation
        navAlertes = findViewById(R.id.navAlertes)
        navCameras = findViewById(R.id.navCameras)
        navDrone = findViewById(R.id.navDrone)

        labelAlertes = findViewById(R.id.labelAlertes)
        labelCameras = findViewById(R.id.labelCameras)
        labelDrone = findViewById(R.id.labelDrone)

        // Navigation entre les trois pages
        navAlertes.setOnClickListener {
            afficherEcran(AlertesFragment(), R.id.navAlertes)
        }

        navCameras.setOnClickListener {
            afficherEcran(CamerasFragment(), R.id.navCameras)
        }

        navDrone.setOnClickListener {
            afficherEcran(DroneFragment(), R.id.navDrone)
        }

        // Premier lancement : afficher les alertes
        if (savedInstanceState == null) {
            afficherEcran(AlertesFragment(), R.id.navAlertes)
        } else {
            selectionnerOnglet(R.id.navAlertes)
        }
    }

    private fun afficherEcran(fragment: Fragment, onglet: Int) {
        supportFragmentManager.beginTransaction()
            .replace(R.id.conteneurFragments, fragment)
            .commit()

        selectionnerOnglet(onglet)
    }

    private fun selectionnerOnglet(ongletActif: Int) {

        val items = listOf(
            Triple(navAlertes, labelAlertes, R.id.navAlertes),
            Triple(navCameras, labelCameras, R.id.navCameras),
            Triple(navDrone, labelDrone, R.id.navDrone)
        )

        items.forEach { (conteneur, label, id) ->

            val actif = id == ongletActif

            conteneur.setBackgroundColor(
                if (actif) Color.rgb(39, 59, 86)
                else Color.TRANSPARENT
            )

            label.setTextColor(
                if (actif) Color.WHITE
                else Color.rgb(170, 183, 202)
            )
        }
    }

    // Cette fonction est appelée lorsqu'on clique sur une alerte
    fun ouvrirDrone(alerte: Alerte) {

        val fragment = DroneFragment.newInstance(
            heure = alerte.heure,
            camera = alerte.camera,
            confiance = alerte.confiance
        )

        afficherEcran(fragment, R.id.navDrone)
    }
}
