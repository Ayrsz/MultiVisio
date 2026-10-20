package com.multivisio.alerte

import android.Manifest
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Build
import androidx.core.app.NotificationCompat
import androidx.core.app.NotificationManagerCompat
import androidx.core.content.ContextCompat

/** Tout ce qui concerne l'affichage des notifications, regroupé au même endroit. */
object Notifications {

    const val SUJET = "drones"            // doit être le même que dans alerte_drone.py
    private const val CANAL = "alertes_drone"
    private const val PREFS = "multivisio"
    private const val CLE_DERNIERE = "derniere_alerte"

    /** Android 8+ exige un "canal" de notification. Importance haute = son + bandeau. */
    fun creerCanal(context: Context) {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val canal = NotificationChannel(
                CANAL,
                context.getString(R.string.canal_nom),
                NotificationManager.IMPORTANCE_HIGH
            )
            context.getSystemService(NotificationManager::class.java)
                .createNotificationChannel(canal)
        }
    }

    fun afficher(context: Context, texte: String) {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU &&
            ContextCompat.checkSelfPermission(context, Manifest.permission.POST_NOTIFICATIONS)
            != PackageManager.PERMISSION_GRANTED
        ) {
            return // l'utilisateur a refusé les notifications
        }
        creerCanal(context)

        // Toucher la notification ouvre l'appli
        val ouvrirAppli = PendingIntent.getActivity(
            context, 0,
            Intent(context, MainActivity::class.java),
            PendingIntent.FLAG_IMMUTABLE
        )

        val notification = NotificationCompat.Builder(context, CANAL)
            .setSmallIcon(R.drawable.ic_drone)
            .setContentTitle(context.getString(R.string.notif_titre))
            .setContentText(texte)
            .setPriority(NotificationCompat.PRIORITY_HIGH)
            .setCategory(NotificationCompat.CATEGORY_ALARM)
            .setContentIntent(ouvrirAppli)
            .setAutoCancel(true)
            .build()

        // Un numéro différent à chaque fois pour ne pas écraser l'alerte précédente
        NotificationManagerCompat.from(context)
            .notify(System.currentTimeMillis().toInt(), notification)
    }

    fun enregistrerAlerte(context: Context, texte: String) {
        context.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
            .edit().putString(CLE_DERNIERE, texte).apply()
    }

    fun derniereAlerte(context: Context): String? =
        context.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
            .getString(CLE_DERNIERE, null)
}
