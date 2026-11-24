
package com.multivisio.alerte

import android.util.Log
import com.google.firebase.messaging.FirebaseMessagingService
import com.google.firebase.messaging.RemoteMessage

class AlerteService : FirebaseMessagingService() {

    override fun onMessageReceived(message: RemoteMessage) {
        super.onMessageReceived(message)

        val donnees = message.data

        val heure = donnees["heure"] ?: "Heure inconnue"
        val camera = donnees["camera"] ?: "Caméra inconnue"
        val confiance = donnees["confiance"] ?: "0"

        val alerte = Alerte(
            heure = heure,
            camera = camera,
            confiance = confiance
        )

        Historique.ajouter(this, alerte)

        Notifications.afficher(this, alerte.texte())
    }

    override fun onNewToken(token: String) {
        super.onNewToken(token)
        Log.d("AlerteService", "Nouveau token Firebase reçu")
    }
}
