package com.multivisio.alerte

import android.Manifest
import android.content.pm.PackageManager
import android.os.Build
import android.os.Bundle
import android.widget.TextView
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AppCompatActivity
import androidx.core.content.ContextCompat
import com.google.firebase.messaging.FirebaseMessaging

/**
 * L'écran principal. Il fait 3 choses :
 *  1. demander le droit d'afficher des notifications ;
 *  2. s'abonner au "sujet" Firebase "drones" (le script Python envoie ses alertes à ce sujet) ;
 *  3. afficher la dernière alerte reçue.
 */
class MainActivity : AppCompatActivity() {

    private lateinit var texteEtat: TextView
    private lateinit var texteDerniereAlerte: TextView

    // Ce qui se passe quand l'utilisateur répond à la demande d'autorisation
    private val demandePermission =
        registerForActivityResult(ActivityResultContracts.RequestPermission()) { accepte ->
            if (!accepte) {
                texteEtat.text = getString(R.string.etat_notifs_refusees)
            }
        }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        texteEtat = findViewById(R.id.texteEtat)
        texteDerniereAlerte = findViewById(R.id.texteDerniereAlerte)

        Notifications.creerCanal(this)
        demanderPermissionNotifications()

        // S'abonner aux alertes drone
        FirebaseMessaging.getInstance().subscribeToTopic(Notifications.SUJET)
            .addOnCompleteListener { tache ->
                texteEtat.text = if (tache.isSuccessful) {
                    getString(R.string.etat_pret)
                } else {
                    getString(R.string.etat_erreur)
                }
            }
    }

    override fun onResume() {
        super.onResume()
        // À chaque retour sur l'écran, on affiche la dernière alerte enregistrée
        texteDerniereAlerte.text = Notifications.derniereAlerte(this)
            ?: getString(R.string.aucune_alerte)
    }

    private fun demanderPermissionNotifications() {
        // Avant Android 13, la permission est accordée automatiquement
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU &&
            ContextCompat.checkSelfPermission(this, Manifest.permission.POST_NOTIFICATIONS)
            != PackageManager.PERMISSION_GRANTED
        ) {
            demandePermission.launch(Manifest.permission.POST_NOTIFICATIONS)
        }
    }
}
