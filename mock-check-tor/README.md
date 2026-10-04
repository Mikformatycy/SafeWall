# Lokalna makieta strony Tor Check

Statyczna kopia pliku HTML dostarczonego przez użytkownika, przeznaczona do prezentacji wyglądu. Nie wykonuje testu Tora, a widoczny adres IP pochodzi z zapisanego HTML. Nie jest stroną Tor Project ani dowodem działania ochrony. Podczas prezentacji należy opisać ją jako makietę.

Docelowy lokalny adres: `http://check.torproject.local/`. Oryginalny `check.torproject.org` pozostaje bez zmian. Do HTTP nie jest potrzebny certyfikat; osobny wariant HTTPS opisano niżej.

Pliki strony są w `site/`. Grafika jest lokalna; odnośniki do innych stron Tor Project nadal prowadzą do internetu. Formularz języka nie tłumaczy statycznego zapisu.

Podgląd lokalny: `python3 -m http.server 8765 --bind 127.0.0.1 --directory site` (z tego katalogu), następnie `http://127.0.0.1:8765/`.

Pierwotny plan zakładał wdrożenie po odzyskaniu SSH; poniższa historia opisuje wykonane później wdrożenie. Domena `.local` wymaga sprawdzenia rozwiązywania przez mDNS na iPhonie; sam wpis DNS w dnsmasq może nie wystarczyć. Należy uruchomić lokalny serwer i udostępnić port wyłącznie w prywatnym LAN, zachowując obecną konfigurację zapory. Nie przechwytujemy HTTPS ani ruchu do prawdziwej domeny.

## Zakres repozytorium

Publikowane są wyłącznie źródła makiety i skrypt zmiany domeny. Certyfikaty, profil instalacyjny CA i raport urządzenia pozostają lokalne. Instrukcje poniżej opisują historyczną instalację; nie uruchamiają usług po sklonowaniu. Zapisany adres IP w publicznym HTML jest przykładowym adresem dokumentacyjnym.

## Wdrożenie

Uruchomiono na Pi usługę `safewall-mock.service`, pliki `/srv/safewall-mock`, HTTP port 80 dostępny tylko z prywatnego Ethernetu i USB administracyjnego. Nazwa `check.torproject.local` wskazuje 192.168.76.2 przez Avahi i DNS LAN. Potwierdzono HTTP strony i grafiki z Maca przez USB oraz odpowiedź DNS. Test telefonu pozostaje do wykonania po podłączeniu Ethernetu. Kopię zmienionych konfiguracji wskazuje deployment-result.txt.

Wyłączenie strony: `sudo systemctl disable --now safewall-mock`. Pełne cofnięcie wymaga odtworzenia trzech plików z zapisanej kopii (o ile od tego czasu nie były zmieniane), przeładowania zapory i restartu Avahi oraz pi-lan-dnsmasq. Nie zmieniano oryginalnej domeny Tor Project ani konfiguracji TLS.

Dodano pomocniczy adres 192.168.76.2/24 do profilu LAN, aby Avahi mogło publikować osobną nazwę bez konfliktu rekordu odwrotnego z nazwą Pi. Przy pełnym cofnięciu usuń ten dodatkowy adres z profilu NetworkManagera.

Avahi: wyłączono automatyczne publish-addresses i zdefiniowano statycznie nazwę Pi dla USB/LAN oraz nazwę makiety. Kopia ustawień: /var/backups/safewall-mock-avahi-daemon.conf. Przy cofnięciu odtwórz również ten plik.

## HTTPS

Uruchomiono `safewall-mock-tls.service` na porcie 443, dostępnym wyłącznie z prywatnego LAN i USB. Lokalny samopodpisany urząd CA: SafeWall Local CA (365 dni); certyfikat serwera podpisany przez to CA (30 dni), SAN check.torproject.local, 192.168.76.2, 10.12.194.1. Klucze prywatne są wyłącznie na Pi w /etc/safewall-mock, uprawnienia 0600. Serwer bez uprawnień root dostaje tylko klucz serwera przez systemd LoadCredential. CA nie jest kluczem serwera. Nie zmieniano zaufania systemowego Maca.

Na iPhonie otwórz http://check.torproject.local/SafeWall-CA.mobileconfig, zainstaluj profil SafeWall Local CA w Ustawienia → Ogólne → VPN i zarządzanie urządzeniem, potem włącz zaufanie w Ogólne → To urządzenie → Ustawienia zaufania certyfikatów. Strona: https://check.torproject.local. Profil zawiera wyłącznie publiczny certyfikat CA, bez VPN, MDM ani kluczy prywatnych.

Zweryfikowano HTTPS z walidacją łańcucha CA i nazwy hosta, stronę, grafikę i pobranie profilu. Instalacja na iPhonie wymaga działania użytkownika. HTTPS potwierdza lokalne połączenie z serwerem, nie użycie Tora.

Po prezentacji usuń profil SafeWall Local CA z iPhone’a, jeśli nie jest już potrzebny. Wyłączenie HTTPS: systemctl disable --now safewall-mock-tls. Kopie sprzed TLS: /var/backups/safewall-mock-before-tls.nft oraz /var/backups/safewall-mock-http-before-tls.service.

Instrukcja Apple: https://support.apple.com/en-ie/102390

## Zmiana domeny jedną komendą

Na Pi: `sudo safewall-domain check.torproject.local3`. Powrót: `sudo safewall-domain check.torproject.local`. Skrypt zmienia DNS, ustawia mDNS tylko dla końcówki .local, wystawia certyfikat serwera z tym samym CA i restartuje usługi. Sprawdza DNS i HTTPS. Kopie: /var/backups/safewall-domain-*. Po błędzie wdrożenia przywraca pliki. Nie zmienia adresacji ani profilu CA na telefonie.

Końcówki inne niż .local wymagają DNS Pi 192.168.76.1 ustawionego dla Ethernetu iPhone’a. VPN lub własny szyfrowany DNS mogą omijać ten serwer. Zalecane prywatne nazwy: .local, .test lub home.arpa. Skrypt nie pozwala podmienić torproject.org.

Przetestowano zmianę .local → .local3 i powrót, z walidacją DNS, certyfikatu i HTTP. Pozostawiono check.torproject.local. Skrypt: /usr/local/sbin/safewall-domain na Pi; kopia w tym folderze.
