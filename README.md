# Guide de l'utilisateur Mission Flash

## 1. Vue d'ensemble :
Mission Flash est une application d'automatisation conçue pour faciliter la saisie de données dans le logiciel de GMAO Mission. Elle permet d'exécuter des macros personnalisées par l'utilisateur pour automatiser et accélérer les tâches répétitives.

---

## 2. Configuration :

### Prérequis obligatoires
* Pack linguistique Anglais (États-Unis) installé sur Windows :
    * Accédez aux paramètres de Windows → Heure et Langue → Langue
    * Sélectionnez "Ajouter une langue"
    * Sélectionnez "Anglais (United-States)"
    * Cliquez sur installer en laissant les paramèters par défaut.

### Installation
1. Décompressez l'Archive  `.zip` correspondant à la dernière version (Numéro de version et packages disponibles sur [Github](https://github.com/litedragondev/Mission-Flash))
2. Une fois l'Archive décompressée, vous pouvez lancer `launch.bat`
3. Une fenêtre de confirmation du type "Windows a protégé votre PC" peut s'ouvrir. Cliquez sur "Exécuter quand même"

---

## 3. Interface Utilisateur :
L'application dispose de 3 onglets principaux :

#### 1. Onglet "Macro Personnalisée"
Interface de création de macros personnalisées avec un système d'étapes modulaire.

#### 2. Onglet "Macros Sauvegardées"
Gestion et exécution des macros sauvegardées depuis l'éditeur

#### 3. Onglet "Paramètres"
Gestion de paramètres de sécurité.


---

## 4. Création d'une macro personnalisée

### Étapes de base :
1. Accédez à l'onglet "Macro Personnalisée"
2. Remplissez les informations de base :
    * **Nom de la macro :** Nom unique de la macro
    * **Description :** Brève description de la macro
    *  **Délai entre les étapes :** Temps d'attente général entre chaque étape (*En secondes*)
3. Ajoutez des étapes

### Types d'actions disponibles

#### 🖱️ Cliquer

* **Usage** : Effectue un clic à des coordonnées précises
* **Configuration** :
    * Cliquez su "Calibrer les coordonnées"
    * Positionnez votre souris sur l'élément cible
    * Appuyez sur `CTRL` pour valider les coordonnées
        * Si les coordonnées sont incorrectes, vous pouvez les recalibrer via "Calibrer les coordonnées".
    * Choisissez le type de clic : "Gauche" ou "Droit"
*  **Test** : Utilisez le bouton "Test" pour vérifier le positionnement. **⚠️ Le bouton test exécute un clic. Assurez-vous que le clic ne soit pas configuré sur un bouton de suppression.**

#### ⌨️ Saisie

* **Usage** : Tape du texte à la position actuelle du curseur
* **Configuration** : Entrez le texte à saisir dans le champ prévu

#### 🔧 Touche spécifique

* **Usage** : Simule des combinaisons de touches
* **Configuration** :
    * Cochez la touche que vous voulez simuler : `Ctrl`, `Alt`, `Shift`, `Tab`, `Entrée`, `Échap` ou `Flèches directionnelles`
    * Utilisez le champ *"Autre"* pour faire des combos (`Ctrl + V`)

#### ⏱️ Attendre

* **Usage** : Marque une pose dans l'exécution
* **Configuration** : Spécifiez le temps d'attente en secondes dans le champ prévu à cet effet

#### ❓ Confirmer ?

* **Usage** : Affiche une boîte de dialogue de confirmation personnalisable
* **Configuration** : Saisissez le message personnalisé si nécessaire
* **Comportement** : L'exécution s'arrête si vous cliquez "Non"

#### 📝 Saisir valeur

* **Usage** : Demande une saisie utilisateur pendant l'exécution sous forme de boîte de dialogue
* **Configuration** :
    * *Message* : Texte affiché à l'utilisateur
    * *Variable* : Nom unique de variable où sera stocké la valeur
    * *Type* : "Court" (une ligne simple) ou "Long" (Zone de texte multiligne)

#### 📋 Utiliser variable

* **Usage** : Utilise une variable saisie précédemment
* **Configuration** : Sélectionnez la variable à utiliser dans la liste déroulante

#### 🔄️ Début de la boucle

* **Usage** : Marque le point de départ d'une boucle
* **Configuration** : Aucune configuration requise

#### 🔁 Boucle

* **Usage** : Répète les actions depuis le "Début de la boucle" (si présente) ou depuis le début de la macro
* **Configuration** :
    * *Nombre de répétitions* : Nombre de boucles de macro exécutées
    * *Type* : "Fixe" (Nombre de répétitions défini par le champ) ou "Avec Confirmation" (Répète la macro autant que l'utilisateur le souhaite)
*  **Important** : 
  * Une seule boucle par macro
  * Doit être placée en dernière position
  * Désactive l'ajout de nouvelles étapes

### Options par étapes
* **Label** : Nom descriptif de l'étape
* **Activée** : Active ou passe l'étape sans l'exécuter
* **Délai (s)** : Défini le délai individuel. Si le champ reste vide, l'étape appliquera le délai par défaut (0.5s) sinon, le délai par défaut est ignoré

---

## 5. Gestion des macros

### Sauvegarde

1. Configurez votre macro dans l'onglet "Macro Personnalisée"
2. Cliquez sur "Sauvegarder"
3. La macro apparaît dans l'onglet "Macro Sauvegardées"

### Exécution
1. **Depuis l'onglet "Macro Personnalisée" :** Cliquez sur "Exécuter"
2. **Depuis l'onglet "Macros Sauvegardées" :**
   * Séléctionnez une macro dans la liste
   * Cliquez sur "Exécuter"

### Modification
1. Dans l'onglet "Macros Sauvegardées" séléctionnez la macro à modifier
2. Cliquez sur "Modifier"
3. L'onglet "Macro Personnnalisée" se charge avec la configuration

### Suppression
1. Sélectionnez la macro dans la liste des Macors Sauvegardées
2. Cliquez sur "Supprimer"
3. Confirmez la suppression

---

## 6. Exécution des macros

---
### DISCLAIMER : CE SCRIPT PEUT SUPPRIMER DES ÉLÉMENTS INVOLONTAIREMENT ET DE MANIÈRE INCONTRÔLABLE. VEUILLEZ PROCÉDER AVEC PRÉCAUTION. EN TANT QUE DÉVELOPPEUR, JE NE SUIS PAS RESPONSABLE DES DÉGÂTS CAUSÉS PAR UNE MAUVAISE UTILISATION DE L'OUTIL.

---

### Préparation :
1. **Désactivez Verr. Maj**
2. **Positionnez correctement la fenêtre cible.** Il est conseillé de ne pas toucher à la fenêtre entre le calibrage et l'exécution

### Processus d'exécution
1. Cliquez sur "Exécuter" ou "Lancer la macro"
2. **Boîte d'avertissement :** Lisez attentivement puis cliquez sur OK
3. **NE TOUCHEZ PLUS AUX CONTRÔLES DE L'ORDINATEUR :** Ne touchez ni à la souris ni au clavier pendant l'exécution

### Arrêt d'urgence

* **Méthode principale** : Cliquez sur "Arrêter" dans la boîte d'avertissement alors restée ouverte.
* **Méthode secondaire** : Faites la combinaison `Alt+F4` pour arrêter l'exécution

---

## 7. Support et maintenance

### Signalement de bugs
Utilisez le lien "Signaler un bug" dans l'interface pour rapporter les problèmes rencontrés.

### Fichier de configuration
* `macros.json` : Macros sauvegardées

Ce fichier peut être sauvegardé pour conserver les macros ou les transférer d'un appareil à un autre. Pour effectuer un transfert, copiez le fichier de macros dans le dossier `/bin/` du script sur la machine de destination. Une fois le transfert fait, redémarrez le script pour mettre à jour les macros.