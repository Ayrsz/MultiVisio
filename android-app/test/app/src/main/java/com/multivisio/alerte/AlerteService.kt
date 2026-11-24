package com.multivisio.alerte

import android.util.Log
import com.google.firebase.messaging.FirebaseMessagingService
import com.google.firebase.messaging.RemoteMessage

/**
 * Android appelle ce service à chaque fois qu'un message Firebase arrive,
 * même si l'appli est fermée.
 */
class AlerteService : FirebaseMessagingService() {

    override fun onMessageReceived(message: RemoteMessage) {
        // Les infos envoyées par le script Python (voir ai-service/alerte_drone.py)
        val donnees = message.data
        Log.d("MultiVisio", "Alerte reçue : $donnees")

        val alerte = Alerte(
            heure = donnees["heure"] ?: "?",
            camera = donnees["camera"] ?: "caméra",
            confiance = donnees["confiance"] ?: "?",
        )
        Historique.ajouter(this, alerte)
        Notifications.afficher(this, alerte.texte())
    }

    override fun onNewToken(token: String) {
        // Pas utile ici : on passe par le sujet "drones", pas par le token.
        Log.d("MultiVisio", "Nouveau token : $token")
    }
}
