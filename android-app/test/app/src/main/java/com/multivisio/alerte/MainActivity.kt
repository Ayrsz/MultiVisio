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
import com.google.firebase.messaging.FirebaseMessaging
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

/**
 * L'écran principal. Il permet de :
 *  1. activer / couper les alertes (abonnement au sujet Firebase "drones") ;
 *  2. voir l'historique des alertes reçues ;
 *  3. envoyer une alerte de test, sans PC ni caméra ;
 *  4. effacer l'historique.
 */
class MainActivity : AppCompatActivity() {

    private lateinit var texteEtat: TextView
    private lateinit var interrupteur: SwitchCompat
    private lateinit var liste: ListView
    private lateinit var texteVide: TextView
    private lateinit var adaptateur: ArrayAdapter<String>

    // Rafraîchit la liste dès qu'une alerte arrive, même si l'écran est ouvert
    private val ecouteur = SharedPreferences.OnSharedPreferenceChangeListener { _, cle ->
        if (cle == Historique.CLE_HISTORIQUE || cle == null) afficherHistorique()
    }

    // Ce qui se passe quand l'utilisateur répond à la demande d'autorisation
    private val demandePermission =
        registerForActivityResult(ActivityResultContracts.RequestPermission()) { accepte ->
            if (!accepte) texteEtat.text = getString(R.string.etat_notifs_refusees)
        }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        texteEtat = findViewById(R.id.texteEtat)
        interrupteur = findViewById(R.id.interrupteurAlertes)
        liste = findViewById(R.id.listeAlertes)
        texteVide = findViewById(R.id.texteVide)

        adaptateur = ArrayAdapter(this, android.R.layout.simple_list_item_1, mutableListOf<String>())
        liste.adapter = adaptateur

        Notifications.creerCanal(this)
        demanderPermissionNotifications()

        // L'interrupteur se souvient de son dernier état (activé par défaut)
        interrupteur.isChecked = Historique.prefs(this).getBoolean(CLE_ACTIVE, true)
        changerAbonnement(interrupteur.isChecked)
        interrupteur.setOnCheckedChangeListener { _, active ->
            Historique.prefs(this).edit().putBoolean(CLE_ACTIVE, active).apply()
            changerAbonnement(active)
        }

        findViewById<Button>(R.id.boutonTest).setOnClickListener {
            val maintenant = SimpleDateFormat("HH:mm:ss", Locale.FRANCE).format(Date())
            val alerte = Alerte(heure = maintenant, camera = "test", confiance = "99")
            Historique.ajouter(this, alerte)
            Notifications.afficher(this, alerte.texte())
        }

        findViewById<Button>(R.id.boutonEffacer).setOnClickListener {
            Historique.effacer(this)
        }
    }

    override fun onStart() {
        super.onStart()
        Historique.prefs(this).registerOnSharedPreferenceChangeListener(ecouteur)
        afficherHistorique()
    }

    override fun onStop() {
        super.onStop()
        Historique.prefs(this).unregisterOnSharedPreferenceChangeListener(ecouteur)
    }

    /** S'abonne (ou se désabonne) au sujet "drones" sur lequel le PC envoie ses alertes. */
    private fun changerAbonnement(active: Boolean) {
        texteEtat.text = getString(R.string.etat_connexion)
        val messaging = FirebaseMessaging.getInstance()
        val tache = if (active) messaging.subscribeToTopic(Notifications.SUJET)
                    else messaging.unsubscribeFromTopic(Notifications.SUJET)
        tache.addOnCompleteListener {
            texteEtat.text = getString(
                when {
                    !it.isSuccessful -> R.string.etat_erreur
                    active -> R.string.etat_pret
                    else -> R.string.etat_coupe
                }
            )
        }
    }

    private fun afficherHistorique() {
        val alertes = Historique.lire(this)
        adaptateur.clear()
        adaptateur.addAll(alertes.map { it.texte() + "\n" + ilYA(it.recueLe) })
        texteVide.visibility = if (alertes.isEmpty()) View.VISIBLE else View.GONE
    }

    /** "il y a 5 minutes", "hier"... */
    private fun ilYA(date: Long): String =
        DateUtils.getRelativeTimeSpanString(date, System.currentTimeMillis(), DateUtils.MINUTE_IN_MILLIS).toString()

    private fun demanderPermissionNotifications() {
        // Avant Android 13, la permission est accordée automatiquement
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU &&
            ContextCompat.checkSelfPermission(this, Manifest.permission.POST_NOTIFICATIONS)
            != PackageManager.PERMISSION_GRANTED
        ) {
            demandePermission.launch(Manifest.permission.POST_NOTIFICATIONS)
        }
    }

    companion object {
        private const val CLE_ACTIVE = "alertes_actives"
    }
}
