#!/bin/zsh
cd -- "${0:A:h}" || exit 1
if ! command -v node >/dev/null 2>&1; then
  print 'Brak Node.js. Otwórz Podglad.html, aby obejrzeć wersję demonstracyjną.'
  read -r '?Naciśnij Enter, aby zamknąć.'
  exit 1
fi
print 'SafeWall: podgląd w Safari z automatycznym odświeżaniem.'
print 'Zatrzymanie serwera: Ctrl+C'
node server.mjs --dev --open-safari
launch_status=$?
if (( launch_status != 0 )); then
  print 'Nie udało się uruchomić serwera. Sprawdź komunikat powyżej.'
  read -r '?Naciśnij Enter, aby zamknąć.'
fi
exit "$launch_status"
