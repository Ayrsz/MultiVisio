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
        // Les infos envoyées par le script Python (voir alerte_drone.py)
        val donnees = message.data
        val confiance = donnees["confiance"] ?: "?"
        val heure = donnees["heure"] ?: "?"
        val camera = donnees["camera"] ?: "caméra"

        Log.d("MultiVisio", "Alerte reçue : $donnees")

        val texte = "Drone repéré par $camera à $heure (confiance $confiance %)"
        Notifications.enregistrerAlerte(this, texte)
        Notifications.afficher(this, texte)
    }

    override fun onNewToken(token: String) {
        // Pas utile ici : on passe par le sujet "drones", pas par le token.
        Log.d("MultiVisio", "Nouveau token : $token")
    }
}
