package com.multivisio.alerte

import android.content.Context
import org.json.JSONArray
import org.json.JSONObject

/** Une alerte reçue (ou de test). */
data class Alerte(
    val heure: String,
    val camera: String,
    val confiance: String,
    val recueLe: Long = System.currentTimeMillis(),
) {
    /** Le texte affiché dans la notification et dans l'historique. */
    fun texte() = "Drone repéré par $camera à $heure (confiance $confiance %)"
}

/**
 * Garde les dernières alertes sur le téléphone, pour les afficher dans l'appli.
 * Elles sont rangées dans les "SharedPreferences" (un petit fichier privé à l'appli),
 * au format JSON.
 */
object Historique {

    const val PREFS = "multivisio"
    const val CLE_HISTORIQUE = "historique"
    private const val MAX_ALERTES = 50   // on oublie les plus anciennes

    fun ajouter(context: Context, alerte: Alerte) {
        val liste = (listOf(alerte) + lire(context)).take(MAX_ALERTES)
        val json = JSONArray()
        liste.forEach {
            json.put(
                JSONObject()
                    .put("heure", it.heure)
                    .put("camera", it.camera)
                    .put("confiance", it.confiance)
                    .put("recueLe", it.recueLe)
            )
        }
        prefs(context).edit().putString(CLE_HISTORIQUE, json.toString()).apply()
    }

    /** Les alertes, de la plus récente à la plus ancienne. */
    fun lire(context: Context): List<Alerte> {
        val brut = prefs(context).getString(CLE_HISTORIQUE, null) ?: return emptyList()
        return try {
            val json = JSONArray(brut)
            (0 until json.length()).map { i ->
                val o = json.getJSONObject(i)
                Alerte(
                    heure = o.optString("heure", "?"),
                    camera = o.optString("camera", "caméra"),
                    confiance = o.optString("confiance", "?"),
                    recueLe = o.optLong("recueLe"),
                )
            }
        } catch (e: Exception) {
            emptyList() // fichier abîmé : on repart de zéro
        }
    }

    fun effacer(context: Context) {
        prefs(context).edit().remove(CLE_HISTORIQUE).apply()
    }

    fun prefs(context: Context) =
        context.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
}
