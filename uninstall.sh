#!/bin/sh
# À lancer une fois la chambre obtenue. Bravo.
LABEL="com.roberval-ou-la-rue"
launchctl bootout "gui/$(id -u)/$LABEL" 2>/dev/null || true
rm -f "$HOME/Library/LaunchAgents/$LABEL.plist"
echo "Guetteur relevé de ses fonctions. Bonne installation à Roberval."
