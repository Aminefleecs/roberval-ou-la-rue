# Roberval ou la rue 🛏️🚨

> « On remet des chambres en ligne bientôt. »
> — le Crous, au téléphone. Bientôt quand ? Mystère.

Plutôt que de rafraîchir la page du Crous 400 fois par jour, ce petit script
le fait à ma place, toutes les 2 minutes, sans jamais se lasser ni aller en TD.

Dès qu'une chambre de la **résidence Roberval** (Compiègne) apparaît sur
[trouverunlogement.lescrous.fr](https://trouverunlogement.lescrous.fr) :

- 🗣️ le Mac crie « Chambre Roberval disponible au Crous » ;
- 🔔 une notification macOS s'affiche ;
- 🌐 la page du logement s'ouvre toute seule ;
- 📱 le téléphone sonne (via [ntfy](https://ntfy.sh)), même loin du Mac.

Les autres nouveaux logements à Compiègne déclenchent juste une notif discrète,
au cas où le plan B deviendrait tentant.

## Installation

Rien à installer à part le Python de macOS (bibliothèque standard uniquement).

```sh
git clone https://github.com/Aminefleecs/roberval-ou-la-rue.git
cd roberval-ou-la-rue
echo "un-nom-de-canal-secret-et-long" > ntfy_topic.txt   # optionnel, pour le téléphone
./install.sh
```

Pour le téléphone : installe l'app **ntfy**, abonne-toi au même nom de canal,
puis vérifie que ça sonne :

```sh
python3 watch.py --test-phone
```

`python3 watch.py --test-notif` fait la même chose côté Mac (voix comprise,
préviens tes colocs).

## Une fois la chambre obtenue

```sh
./uninstall.sh
```

## Comment ça marche

Le site du Crous charge ses résultats depuis `POST /api/fr/search/<id>`.
Le script envoie la même requête sur un rectangle autour de Compiègne, garde
en mémoire les logements déjà vus (`seen.json`) et ne crie que pour les
nouveaux. Si un logement disparaît puis revient, il re-crie : c'est souvent
une réservation qui a sauté, donc la meilleure occasion.

## Limites honnêtes

- Le Mac doit être allumé et réveillé : en veille, le guetteur dort aussi.
- Le site peut changer du jour au lendemain ; si le Crous ne répond plus
  pendant 30 min, le script prévient.
- Une requête toutes les 2 minutes, pas plus : on reste poli avec le serveur.
- Ça prévient, ça ne réserve pas. Le clic final reste à toi, et vite.
