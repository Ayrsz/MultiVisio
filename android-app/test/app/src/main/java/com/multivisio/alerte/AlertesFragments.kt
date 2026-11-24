
package com.multivisio.alerte

import android.Manifest
import android.content.SharedPreferences
import android.content.pm.PackageManager
import android.os.Build
import android.os.Bundle
import android.text.format.DateUtils
import android.view.View
import android.widget.ArrayAdapter
import android.widget.Button
import android.widget.ListView
import android.widget.TextView
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AppCompatActivity
import androidx.appcompat.widget.SwitchCompat
import androidx.core.content.ContextCompat
import androidx.fragment.app.Fragment
import com.google.firebase.messaging.FirebaseMessaging
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

class AlertesFragment : Fragment(R.layout.fragment_alerte) {

    private var texteEtat: TextView? = null
    private var texteVide: TextView? = null
    private var adaptateur: ArrayAdapter<String>? = null

    private val ecouteur =
        SharedPreferences.OnSharedPreferenceChangeListener { _, cle ->

            if (cle == Historique.CLE_HISTORIQUE || cle == null) {
                afficherHistorique()
            }
        }

    private val demandePermission =
        registerForActivityResult(
            ActivityResultContracts.RequestPermission()
        ) { accepte ->

            if (!accepte) {
                texteEtat?.text =
                    getString(R.string.etat_notifs_refusees)
            }
        }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)

        val contexte = requireContext()

        texteEtat = view.findViewById(R.id.texteEtat)
        texteVide = view.findViewById(R.id.texteVide)

        val interrupteur =
            view.findViewById<SwitchCompat>(R.id.interrupteurAlertes)

        val liste =
            view.findViewById<ListView>(R.id.listeAlertes)

        // Adaptateur de l'historique
        adaptateur = ArrayAdapter(
            contexte,
            android.R.layout.simple_list_item_1,
            mutableListOf<String>()
        )

        liste.adapter = adaptateur

        // Notifications Android
        Notifications.creerCanal(contexte)
        demanderPermissionNotifications()

        // État mémorisé de l'interrupteur
        interrupteur.isChecked =
            Historique.prefs(contexte)
                .getBoolean(CLE_ACTIVE, true)

        changerAbonnement(interrupteur.isChecked)

        interrupteur.setOnCheckedChangeListener { _, active ->

            Historique.prefs(contexte)
                .edit()
                .putBoolean(CLE_ACTIVE, active)
                .apply()

            changerAbonnement(active)
        }

        // Créer une fausse alerte pour tester
        view.findViewById<Button>(R.id.boutonTest)
            .setOnClickListener {

                val maintenant = SimpleDateFormat(
                    "HH:mm:ss",
                    Locale.FRANCE
                ).format(Date())

                val alerte = Alerte(
                    heure = maintenant,
                    camera = "test",
                    confiance = "99"
                )

                Historique.ajouter(requireContext(), alerte)

                Notifications.afficher(
                    requireContext(),
                    alerte.texte()
                )
            }

        // Effacer l'historique
        view.findViewById<Button>(R.id.boutonEffacer)
            .setOnClickListener {

                Historique.effacer(requireContext())
                afficherHistorique()
            }

        // Cliquer sur une alerte ouvre la page Drone
        liste.setOnItemClickListener { _, _, position, _ ->

            val alertes = Historique.lire(requireContext())

            val alerte = alertes.getOrNull(position)

            if (alerte != null) {
                (activity as? MainActivity)?.ouvrirDrone(alerte)
            }
        }

        afficherHistorique()
    }

    override fun onStart() {
        super.onStart()

        context?.let {
            Historique.prefs(it)
                .registerOnSharedPreferenceChangeListener(ecouteur)
        }

        afficherHistorique()
    }

    override fun onStop() {
        context?.let {
            Historique.prefs(it)
                .unregisterOnSharedPreferenceChangeListener(ecouteur)
        }

        super.onStop()
    }

    private fun changerAbonnement(active: Boolean) {

        texteEtat?.text = getString(R.string.etat_connexion)

        val messaging = FirebaseMessaging.getInstance()

        val tache = if (active) {
            messaging.subscribeToTopic(Notifications.SUJET)
        } else {
            messaging.unsubscribeFromTopic(Notifications.SUJET)
        }

        tache.addOnCompleteListener {

            if (!isAdded) return@addOnCompleteListener

            val texte = when {
                !it.isSuccessful -> R.string.etat_erreur
                active -> R.string.etat_pret
                else -> R.string.etat_coupe
            }

            texteEtat?.text = getString(texte)
        }
    }

    private fun afficherHistorique() {

        val contexte = context ?: return
        val adapter = adaptateur ?: return

        val alertes = Historique.lire(contexte)

        adapter.clear()

        adapter.addAll(
            alertes.map {
                it.texte() + "\n" + ilYA(it.recueLe)
            }
        )

        texteVide?.visibility =
            if (alertes.isEmpty()) View.VISIBLE else View.GONE
    }

    private fun ilYA(date: Long): String {

        return DateUtils.getRelativeTimeSpanString(
            date,
            System.currentTimeMillis(),
            DateUtils.MINUTE_IN_MILLIS
        ).toString()
    }

    private fun demanderPermissionNotifications() {

        if (
            Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU &&
            ContextCompat.checkSelfPermission(
                requireContext(),
                Manifest.permission.POST_NOTIFICATIONS
            ) != PackageManager.PERMISSION_GRANTED
        ) {
            demandePermission.launch(
                Manifest.permission.POST_NOTIFICATIONS
            )
        }
    }

    companion object {
        private const val CLE_ACTIVE = "alertes_actives"
    }
}
