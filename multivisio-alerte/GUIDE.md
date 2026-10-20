# Appli MultiVisio Alerte : guide de démarrage

Le but : quand l'IA (le script Python sur le PC) voit un drone, ton téléphone
Android sonne et affiche « ⚠️ Drone détecté ! », même si l'appli est fermée.

## Comment ça marche

```
ESP32-CAM ──image──▶ PC (Python + YOLO) ──« drone ! »──▶ Firebase (Google) ──▶ Téléphone Android
```

- **Firebase Cloud Messaging** est un service gratuit de Google qui livre des
  notifications aux téléphones. C'est ce qu'utilisent WhatsApp, Instagram, etc.
- Le téléphone s'abonne à un « sujet » appelé `drones`. Le script Python
  envoie son alerte à ce sujet, et tous les téléphones abonnés la reçoivent.
  Pas besoin de connaître l'adresse du téléphone, et ça marche même si le PC
  et le téléphone ne sont pas sur le même Wi-Fi.

## Ce qu'il y a dans le dossier

| Dossier / fichier | À quoi il sert |
|---|---|
| `android-app/` | Le projet à ouvrir dans Android Studio |
| `android-app/app/src/main/java/.../MainActivity.kt` | L'écran de l'appli |
| `android-app/app/src/main/java/.../AlerteService.kt` | Reçoit l'alerte, même appli fermée |
| `android-app/app/src/main/java/.../Notifications.kt` | Affiche la notification |
| `python/alerte_drone.py` | La fonction `envoyer_alerte()` côté PC |
| `python/envoyer_alerte_test.py` | Envoie une fausse alerte pour tester |
| `python/detect_et_alerte.py` | Ton `detect_camera.py` + l'envoi de l'alerte |

---

## Étape 1 : finir l'installation d'Android Studio

1. Au premier lancement, choisis **Standard** dans l'assistant, puis
   **Next** jusqu'au bout.
2. Accepte les licences (clique sur chaque ligne à gauche, puis **Accept**).
3. Laisse-le télécharger le « SDK » (les outils Android). C'est long, c'est normal.

## Étape 2 : ouvrir le projet

1. Copie le dossier `multivisio-alerte` sur ton PC (par exemple dans
   `Documents\MultiVisio`).
2. Dans Android Studio : **File > Open**, puis choisis le dossier
   **`android-app`** (pas le dossier au-dessus).
3. Clique **Trust Project** si on te le demande.
4. En bas, une barre de progression « Gradle sync » tourne : Android Studio
   télécharge ce dont l'appli a besoin. À la fin, **une erreur
   « google-services.json is missing » est normale** : on le crée à l'étape 3.

## Étape 3 : créer le projet Firebase

1. Va sur https://console.firebase.google.com avec un compte Google.
2. **Créer un projet** → nom : `MultiVisio` → tu peux désactiver Google
   Analytics → **Créer**.
3. Sur la page du projet, clique sur l'icône **Android** pour ajouter une appli.
4. **Nom du package Android** : tape exactement `com.multivisio.alerte`
   (sinon ça ne marchera pas). Le reste est facultatif. **Enregistrer l'appli**.
5. Télécharge **`google-services.json`** et mets-le dans
   `android-app\app\` (à côté du fichier `build.gradle.kts` de ce dossier).
6. Les étapes suivantes de la console (« Ajouter le SDK ») sont **déjà
   faites** dans le projet : clique **Suivant** puis **Accéder à la console**.
7. Retour dans Android Studio : clique sur l'icône d'éléphant
   **Sync Project with Gradle Files** (en haut à droite). L'erreur disparaît.

## Étape 4 : lancer l'appli sur un téléphone

**Avec ton téléphone (le plus simple)** :

1. Sur le téléphone : **Paramètres > À propos du téléphone**, touche
   7 fois **Numéro de build** → « Vous êtes développeur ».
2. **Paramètres > Options pour les développeurs** → active
   **Débogage USB**.
3. Branche le téléphone au PC en USB et accepte « Autoriser le débogage ».
4. Dans Android Studio, ton téléphone apparaît en haut. Clique sur **▶ Run**.

**Ou avec un téléphone virtuel (émulateur)** : **Device Manager > +** →
choisis un modèle avec le logo **Google Play** (obligatoire pour recevoir les
notifications Firebase) → ▶ Run.

Au lancement, accepte « Autoriser les notifications ». L'écran doit afficher
**« Prêt : tu recevras une alerte… »**.

## Étape 5 : donner au PC le droit d'envoyer des alertes

1. Console Firebase → ⚙️ **Paramètres du projet** → onglet
   **Comptes de service** → **Générer une nouvelle clé privée**.
2. Un fichier `.json` se télécharge. Renomme-le **`cle-firebase.json`** et
   mets-le dans le dossier `python\`.
3. ⚠️ Cette clé est **secrète** : ne la mets jamais sur GitHub ni dans un
   message (le fichier `.gitignore` l'exclut déjà).

## Étape 6 : premier test (sans caméra)

Dans un terminal, dans le dossier `python\` :

```bash
pip install -r requirements.txt
python envoyer_alerte_test.py
```

Le terminal affiche « Alerte envoyée » et le téléphone sonne 🎉. Teste aussi
avec l'appli fermée : la notification doit arriver quand même.

## Étape 7 : brancher l'IA

Copie `alerte_drone.py`, `detect_et_alerte.py` et `cle-firebase.json` dans
`Test_IA\` (à côté de `best_1h.pt`), puis :

```bash
pip install firebase-admin
python detect_et_alerte.py
```

Quand YOLO voit un drone, une alerte part. Pour ne pas spammer le téléphone,
il y a au maximum **une alerte toutes les 30 secondes**
(`DELAI_ENTRE_ALERTES` dans `alerte_drone.py`).

---

## Problèmes fréquents

| Symptôme | Solution |
|---|---|
| `File google-services.json is missing` | Étape 3.5 : le fichier doit être dans `android-app\app\` |
| `No matching client found for package name` | Le nom de package dans Firebase n'est pas `com.multivisio.alerte` : recrée l'appli Android dans la console |
| L'écran dit « Impossible de s'abonner » | Pas d'Internet, ou émulateur sans Google Play |
| Le script dit `FileNotFoundError: cle-firebase.json` | Étape 5 : la clé doit être à côté de `alerte_drone.py` |
| Rien n'arrive sur un téléphone Xiaomi / Huawei / Oppo | Dans les réglages de l'appli, autorise le « démarrage automatique » et désactive l'économie de batterie |
| Gradle propose de « mettre à jour » des versions | Tu peux accepter, ça ne casse rien |

## Pour plus tard

- **Version sans Internet** : si le PC et le téléphone sont toujours sur le
  même Wi-Fi, on pourrait se passer de Firebase (le téléphone interroge
  directement le PC). C'est plus simple à installer, mais ça ne marche plus
  dès qu'on quitte ce Wi-Fi, et l'appli doit rester ouverte.
- Idées d'améliorations : envoyer la photo du drone, un historique des
  alertes, un bouton « couper les alertes ».
