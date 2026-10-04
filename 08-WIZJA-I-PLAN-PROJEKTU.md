# SafeWall — wizja i zakres dalszego rozwoju

Aktualizacja: 4 października 2026. Dashboard demo, koncepcja CAD i materiały projektu już istnieją. Użytkownik potwierdził Tora na nowszym nagraniu; pliki routera nadal opisują wcześniejszy NAT. Bieżący status: [docs/STATUS.md](docs/STATUS.md). Dalsze wpisy zachowują historię decyzji; najnowszy montaż filmu to v22. Dokument dla komisji: [draft](projekt/Draft-projektu.md), [PDF](projekt/Draft-projektu.pdf).

## Cel i scenariusz
Telefon korzysta z internetu wyłącznie po kablu USB-C–Ethernet. Użytkownik włącza tryb samolotowy oraz wyłącza Wi-Fi i Bluetooth w ustawieniach. Własny modem routera zapewnia LTE. Osobny USB-C Pi–Mac służy do SSH, nie do dostarczania internetu klientowi. Docelowo zestaw ma własny akumulator.

Celem jest ograniczenie lokalnego śledzenia radiowego telefonu, filtrowanie wybranych domen telemetrycznych i chroniona ścieżka przez Tor. Nie deklarujemy niewykrywalności, anonimowości wobec operatora ani wyłączenia wszelkich emisji bez pomiarów. Modem pozostaje nadajnikiem identyfikowanym przez SIM i urządzenie; operator może go lokalizować. Adres MAC Ethernet pozostaje w lokalnym segmencie.

## Etapy i warunki odbioru
| Etap | Zakres | Dowód działania |
|---|---|---|
| 1. Łącze | Stabilizacja LTE, kontrolowany test innej SIM / modemu | Ukończone pobrania i powtarzalny pomiar szybkości bez timeoutów |
| 2. Tor | TCP i DNS, opcjonalne mosty, blokada bezpośredniego wyjścia | Wyjście Tor, brak wycieków DNS/IPv6/UDP, po zatrzymaniu Tora brak internetu |
| 3. Panel | Stan LTE/Tor, statystyki DNS, reguły, wyjątki | Zapytanie do testowej blokowanej domeny zwiększa właściwy licznik |
| 4. Komunikacja | SMS i rozmowy operatora; osobno szyfrowana komunikacja internetowa | Test SMS, toru audio i wsparcia operatora; oddzielna weryfikacja szyfrowania E2EE |
| 5. Sprzęt | PCB, bateria/UPS, CAD i dyskretna obudowa | Stabilne zasilanie pod obciążeniem, temperatura, antena, czas pracy |

## Tor i filtrowanie
Pliki `config/` odtwarzają wcześniejszy NAT do modemu. Późniejsze nagranie i informacja użytkownika o Torze wymagają uzgodnienia z aktualną konfiguracją urządzenia; nie wykonano niezależnego audytu. Tryb chroniony nie może automatycznie wracać do bezpośredniego LTE po awarii Tora. Panel lokalny i administracja USB powinny pozostać dostępne. Zwykły UDP/QUIC nie ma być przepuszczany poza Tor; część aplikacji może przestać działać. Ruch DNS z LAN ma przechodzić przez lokalny filtr i dalej przez chronioną ścieżkę. IPv6 blokujemy do czasu zaprojektowania i sprawdzenia obsługi.

Mosty (bridges), np. z obfs4, są opcją na blokowanie dostępu do Tora, nie gwarancją anonimowości ani przyspieszeniem. Zapora nie zastępuje zabezpieczeń Tor Browser; konta, odciski przeglądarki i aplikacje nadal mogą identyfikować użytkownika.

## Panel i dane
Panel dostępny z prywatnego LAN, zabezpieczony uwierzytelnieniem, bez wystawiania na WAN. Widoki: połączenie LTE i parametry radia; stan Tora i mostów; liczba zapytań DNS i blokad; lista reguł/wyjątków; SMS i ewentualnie rozmowy. Licznik blokad oznacza zablokowane zapytania, nie liczbę udaremnionych prób śledzenia. Filtr nie rozpoznaje całej zaszyfrowanej telemetrii; szyfrowany DNS aplikacji może omijać filtrowanie domen.

Preferowane są lokalne sumaryczne statystyki, krótka lub wyłączona historia domen, przycisk kasowania danych. Panel nie pokazuje PIN-u ani sekretów. Panel istnieje jako lokalny prototyp z danymi demo; [uruchamianie](dashboard/README.md). Połączenie z Pi, filtrem DNS i rzeczywistymi pomiarami pozostaje do wykonania.

## SMS i rozmowy
Zwykłe SMS-y i rozmowy komórkowe nie są przenoszone przez Tor i nie stają się E2EE dzięki panelowi. Ich obsługa wymaga sprawdzenia komend modemu, wsparcia VoLTE/operatora oraz fizycznego lub USB toru audio. Szyfrowana komunikacja ma stanowić oddzielną funkcję opartą na sprawdzonym protokole i zgodnym kliencie po obu stronach. Nie projektujemy własnej kryptografii. Rozmowy internetowe często potrzebują UDP; zgodność, opóźnienia i ewentualne ograniczenia w trybie Tor są otwartym zadaniem.

## Miniaturyzacja i forma
Użytkownik chce kompaktowego urządzenia o dyskretnym wyglądzie zwykłego akcesorium (np. powerbanku). Plan: PCB po sprawdzeniu architektury, obudowa CAD, mocowanie anteny i złączy, odciążenie kabli, chłodzenie i bezpieczne zasilanie. Obudowa nie oznacza maskowania emisji LTE. Model Waveshare UPS pozostaje nieustalony, zasilanie bateryjne nie jest uruchomione.

## Źródła
- Apple: https://support.apple.com/en-gb/108785 — tryb samolotowy może pozostawić Bluetooth aktywny.
- Tor Project: https://support.torproject.org/tor-browser/security/using-tb-safely/ — granice ochrony i HTTPS.
- Tor Project: https://support.torproject.org/relays/legal-and-abuse/ddos/ — brak transportu zwykłego UDP.
- Tor Project: https://support.torproject.org/tor-browser/circumvention/unblocking-tor/ — mosty i transporty maskujące.

## Nowa informacja diagnostyczna
Według użytkownika ten sam PiTalk około roku wcześniej działał z normalną prędkością na T-Mobile i Play przez USB na Windowsie. Nie jest to bieżący pomiar. Użytkownik może zdobyć SIM Plusa; test nie został jeszcze wykonany. Na czas przygotowania zgłoszenia wstrzymano zmiany konfiguracji sprzętu.

## Uwagi mentorów i wnioski do prezentacji — 4 października 2026

Zapis na podstawie relacji użytkownika. To materiał do przygotowania prezentacji, nie nowe wyniki testów.

1. **Oprzeć opowieść na przykładzie organizacji.** Pomysł użytkownika po rozmowach: wybrać konkretną organizację lub typ organizacji i pokazać jej problem, użytkownika oraz sytuację, w której SafeWall ma być przydatny. Organizacja pozostaje do wyboru; sam przykład nie oznacza współpracy ani potwierdzonego zapotrzebowania.
2. **Wyjaśnić wartość projektu ponad sam kabel.** Jedna z mentorek sprowadziła projekt do kabla. Do dopracowania: sposób przedstawienia problemu i korzyści, tak aby odbiorca rozumiał rolę całego urządzenia. W prezentacji połączyć przewód z celem wyłączenia radiów telefonu oraz planowanymi funkcjami bramy: Torem, filtrowaniem i panelem. Oddzielać funkcje sprawdzone od planowanych.
3. **Odpowiedzieć na zarzut „żyjemy w dobie bezprzewodowości”.** Według relacji użytkownika ta sama mentorka zakwestionowała połączenie kablowe w takim kontekście. Kluczowy cel do zachowania w narracji: **chcemy ograniczać emisję radiową z samego telefonu**. Przewód jest świadomym wyborem wynikającym z tego celu; wygodę podłączenia warto dopracować. Osobny modem LTE nadal nadaje — nie przedstawiać całego zestawu jako pozbawionego emisji radiowej.
4. **Pokazać przenośność w liczbach.** Dodatkowy pomysł użytkownika: na prezentacji podać wagę zestawu i czas pracy na baterii. Uzupełnić je wymiarami, aby określenie „przenośne” miało konkretną podstawę. Lista pomiarów poniżej.

**Propozycja zdania do prezentacji:** „Projektujemy SafeWall, aby telefon mógł korzystać z internetu przy wyłączonych Wi-Fi, Bluetooth i łączności komórkowej. Dlatego łączymy go przewodem z osobną bramą, której modem zapewnia dostęp do LTE.”

**Najbliższy krok:** wybrać jedną organizację lub typ organizacji i zapisać jeden konkretny scenariusz użycia.

### Metryki przenośności do prezentacji

| Metryka | Co zmierzyć i pokazać | Stan |
|---|---|---|
| Masa zestawu [g] | Cały zestaw noszony przez użytkownika: router, modem, antena, bateria, obudowa, wymagane przewody i adaptery; bez telefonu. Przy pomiarze obecnego prototypu wymienić brakujące elementy. | Do zważenia |
| Wymiary [cm] | Długość × szerokość × wysokość złożonego urządzenia; uwzględnić wystającą antenę i złącza lub opisać je osobno. Można dodać zdjęcie obok telefonu jako skalę. | Do zmierzenia |
| Czas pracy na baterii [h:min] | Od pełnego naładowania do utraty działania zestawu. Osobno test aktywnego korzystania z internetu i test bezczynności z utrzymanym połączeniem LTE. | Do przetestowania po uruchomieniu zasilania bateryjnego |

Przy czasie pracy zapisać model i pojemność baterii, scenariusz obciążenia, stan Tora i filtrów oraz to, czy zestaw zasila także telefon. Wynik podawać dla sprawdzonej konfiguracji. Szacunki i cele dla przyszłej wersji oznaczać wprost; czas pracy pozostaje niezmierzony.

**Szablon slajdu „Przenośność w liczbach”:** „Masa zestawu: … g · Wymiary: … × … × … cm · Czas pracy: … h … min przy …”. Pola uzupełnić po pomiarach.

**Pierwszy krok do metryk:** zważyć obecny zestaw i zanotować, jakie elementy obejmuje pomiar.

### Kolejna rozmowa z mentorem — wygląd, rozpoznawalność i porównanie z VPN

Zapis dalszych uwag użytkownika z 4 października 2026. Dotyczą rozmowy z innym mentorem niż wcześniejsza uwaga o „samym kablu”. Obserwacje i hipotezy z rozmowy nie są wynikami badań ani potwierdzonymi możliwościami urządzenia.

1. **Wygląd zwykłego powerbanku.** Użytkownik i mentor rozważali, jak nadać urządzeniu dyskretną, znajomą formę. Powerbank jest proponowanym punktem odniesienia. Gruby, wystający moduł z tyłu telefonu może zwracać uwagę, a osoba postronna nie musi wiedzieć, czym jest. Użytkownik zauważa, że powerbanki mocowane przez MagSafe stały się częściej spotykane; ich forma może być inspiracją. Jest to obserwacja użytkownika, nie zweryfikowany trend rynkowy. Samo podobieństwo obudowy nie przesądza o obsłudze MagSafe ani ładowania bezprzewodowego.
2. **Wygląd oceniać w lokalnym kontekście.** Użytkownik wskazał także kraje o niższych dochodach: nietypowe lub rzucające się w oczy akcesorium może przyciągać uwagę. Do sprawdzenia w wybranym kraju i grupie użytkowników, czy proponowana forma wygląda zwyczajnie. Nie zakładać, że znajomy wygląd powerbanku będzie równie rozpoznawalny wszędzie.
3. **Hipoteza rozpoznawania konstrukcji w X-ray.** Podczas rozmowy padło pytanie, czy przy kontroli z użyciem skanera X-ray można byłoby rozpoznać urządzenie po płytce PCB, przebiegu ścieżek i rozmieszczeniu komponentów, np. z pomocą AI. Obawa: po uzyskaniu jednego egzemplarza jako wzorca służby mogłyby wiedzieć, czego szukać w kolejnych, identycznych urządzeniach. To scenariusz zagrożenia zgłoszony w rozmowie; nie potwierdzono możliwości rozpoznawania tych szczegółów ani skuteczności takiej identyfikacji.
4. **Generowanie wariantów konstrukcji przez AI/LLM — pomysł badawczy.** Użytkownik proponuje rozważyć generowanie różnych wariantów przebiegu ścieżek, projektu płytek PCB, rozmieszczenia komponentów i obudowy. Motywacją jest powyższa obawa o powtarzalny wygląd konstrukcji. Na tym etapie wystarczy zapisać lub zaplanować ten kierunek; użytkownik nie wymaga wdrożenia go w prototypie. Wykonalność techniczna oraz wpływ wariantów na rozpoznawalność pozostają do zbadania. Nie jest to deklaracja niewykrywalności w X-ray; wygląd zewnętrzny i rozpoznawalność wnętrza to osobne zagadnienia.
5. **Pytanie mentora: czym SafeWall różni się od zwykłego szyfrowania i od NordVPN-a?** Zachować oba porównania jako pytania do prezentacji. Do przygotowania: krótkie zestawienie problemu rozwiązywanego przez szyfrowanie komunikacji, usługę VPN i docelowy SafeWall. W odpowiedzi uwzględnić cel ograniczania emisji radiów samego telefonu, rolę osobnej bramy i planowane funkcje Tora oraz filtrowania. Rozdzielić funkcje działające od planowanych; szczegółowe porównanie z NordVPN-em wymaga sprawdzenia aktualnej oferty.

### Porównanie z telefonami satelitarnymi — kolejna uwaga mentora

Zapis rozmowy z 4 października 2026. Według relacji użytkownika mentor wskazał telefon satelitarny jako potencjalnie lepsze rozwiązanie, argumentując, że wystarczy widoczność nieba. Użytkownik chce przygotować odpowiedź na ten argument: wskazuje specjalistyczny charakter sprzętu, przypuszczalnie wysoki koszt i wątpliwość dotyczącą dostępu organizacji do sieci satelitów.

**Uściślenia do wykorzystania w prezentacji:**

1. **Organizacja nie potrzebuje własnych satelitów.** Może kupić urządzenie i usługę istniejącego operatora. Iridium opisuje partnerów sprzedających zarówno sprzęt, jak i dostęp do jego sieci. Argumentem do porównania jest koszt i zależność od dostawcy usługi, a nie konieczność budowy własnej konstelacji. [Iridium — partnerzy i dostawcy usług](https://www.iridium.com/partners).
2. **Widoczność nieba jest rzeczywistym warunkiem, ale sama nie wystarcza.** Potrzebne są zgodne urządzenie i aktywna usługa. Przykładowo Iridium opisuje dla GO! exec potrzebę niezasłoniętego widoku nieba; budynki, gęste drzewa i góry mogą pogarszać połączenie. Nie sprowadzać tego do gwarancji działania w każdym miejscu, z którego widać fragment nieba. [Iridium — warunki pracy GO! exec](https://ifp.iridium.com/go-exec-faqs/), [Iridium — plany usług głosowych](https://www.iridium.com/services/voice).
3. **Porównać scenariusze użycia.** Łączność satelitarna ma istotną przewagę tam, gdzie nie ma działającej sieci komórkowej. Obecna architektura SafeWall wymaga LTE i dostępu do internetu przez operatora komórkowego. Jej celem jest korzystanie ze zwykłego telefonu z wyłączonymi radiami, przez osobną bramę z planowanymi funkcjami ochrony prywatności. Wniosek dla prezentacji: oceniać oba rozwiązania względem konkretnej potrzeby organizacji. [Iridium — łączność poza zasięgiem sieci naziemnych](https://www.iridium.com/services/voice); architektura SafeWall: sekcja „Cel i scenariusz” powyżej.

**Koszt — argument do policzenia.** Zachować uwagę użytkownika o specjalistycznym sprzęcie i możliwej barierze cenowej. Porównać konkretny telefon satelitarny i plan usługi z pełnym zestawem SafeWall oraz usługą LTE: sprzęt, wymagane akcesoria, aktywacja, abonament lub prepaid i opłaty za użycie w tym samym okresie. Iridium oferuje różne modele rozliczeń; nie ustalono tutaj konkretnych cen ani przewagi kosztowej SafeWall. [Iridium — plany usług](https://www.iridium.com/services/voice).

**Propozycja odpowiedzi mentorowi:** „Telefon satelitarny ma przewagę, gdy nie ma sieci komórkowej. SafeWall projektujemy do korzystania z istniejącego LTE przez osobną bramę, przy wyłączonych radiach telefonu. Dla wybranej organizacji chcemy porównać koszt całego zestawu, wygodę oraz potrzebne funkcje ochrony prywatności.”

## Pomysł na demo wideo — od animacji składania do prawdziwego prototypu

Pomysł użytkownika zapisany 4 października 2026. Zakres tego wpisu: scenariusz do późniejszego wykonania. Użytkownik mówi o działającym prototypie i chce pokazać płynne przejście od modelu cyfrowego do fizycznego urządzenia oraz jego użycia z telefonem.

**Główna sekwencja:** części urządzenia składają się jak klocki → złożony model 3D płynnie przekształca się w prawdziwy prototyp (morph transition) → podłączenie przewodem do telefonu → ekran telefonu z pozytywnym wynikiem testu Tora.

### Materiały odnalezione w projekcie

Użytkownik wskazał folder „Physical Video”; odpowiadające opisowi materiały znaleziono w `physical-design/`. Sprawdzono parametry plików i wybrane kadry:

- Film fizycznego prototypu (plik lokalny: `physical-design/IMG_0965.MOV`) — 20,1 s, pionowo 720 × 1280, 30 kl./s. Wybrane kadry pokazują obracany w dłoni prototyp: stos płytek, ogniwa i zewnętrzną antenę, na tle sali wydarzenia. Materiał referencyjny dla wyglądu i ujęcia prawdziwego urządzenia.
- Render składania v04 (plik lokalny: `physical-design/visualization/Product-assembly-v04.mp4`) — 5 s, poziomo 1920 × 1080, 24 kl./s. Części rozstawione warstwami składają się w zamkniętą obudowę przypominającą powerbank. Dostępna jest też scena Blendera (plik lokalny: `physical-design/visualization/Product-keynote-v04.blend`).

Użytkownik rozważa Blender, FreeCAD lub Fusion 360; wybór narzędzia pozostaje otwarty. Istniejące materiały mogą posłużyć jako punkt wyjścia.

### Proponowany przebieg — około 30 sekund

Czasy są propozycją montażową, nie ustalonym wymaganiem użytkownika.

| Czas | Obraz | Co ma przekazać |
|---|---|---|
| 0–5 s | Rozłożone elementy modelu 3D kolejno trafiają na miejsce; urządzenie składa się jak z klocków. | Budowa i wizja urządzenia. |
| 5–8 s | Model zatrzymuje się w wybranym położeniu i płynnie przechodzi w fizyczny prototyp w podobnym kadrze. | Przejście od projektu do sprzętu, który można wziąć do ręki. |
| 8–17 s | Ujęcie prawdziwego zestawu: telefon z wyłączonymi radiami, podłączenie adaptera i przewodu do urządzenia. | Jak użytkownik korzysta z SafeWall. |
| 17–30 s | Zbliżenie na telefon, otwarcie lub odświeżenie strony Tor Check; po uzyskaniu pozytywnego wyniku chwila na przeczytanie komunikatu i zobaczenie zielonego potwierdzenia. | Widoczny wynik konkretnego testu połączenia. |

### Założenia przejścia render → film

Najpierw wybrać docelowy kadr prawdziwego prototypu, a następnie dopasować do niego końcową pozycję modelu: kąt kamery, wielkość w kadrze, położenie i kierunek ruchu. Ujednolicić orientację obrazu i klatkaż materiału wynikowego; obecny film jest pionowy, a render poziomy. Nowe ujęcie prototypu w poziomie pozwoli uniknąć ciasnego kadrowania, jeśli demo będzie wyświetlane na poziomym slajdzie.

Obudowa powerbanku z renderu i odsłonięty prototyp mają różną geometrię. Rozważyć pokazanie wnętrza lub zanikanie obudowy tuż przed morphem, aby przejście prowadziło do widocznego stosu płytek. Podpisy „Wizja produktu” i „Działający prototyp” mogą jasno nazwać oba etapy. Efekt ma płynnie połączyć animację i nagranie z życia.

### Finał z telefonem

Właściwa strona to [Tor Check — check.torproject.org](https://check.torproject.org/) (w wypowiedzi padło „check.project.org”). Docelowo nagrać rzeczywisty pozytywny wynik na telefonie podłączonym do SafeWall. Samo obejrzenie filmu sprzętu nie potwierdza działania Tora; ten fragment wymaga osobnego sprawdzenia i nagrania. Zielony komunikat dotyczy połączenia sprawdzanego przez stronę, nie pełnej anonimowości ani wszystkich aplikacji telefonu.

W projekcie istnieje również [lokalna makieta Tor Check](mock-check-tor/README.md), która nie wykonuje testu Tora. Jeżeli posłuży do prób montażowych, oznaczyć takie ujęcie jako „Makieta interfejsu”; w demonstracji rzeczywistego działania użyć wyniku prawdziwego testu.

**Pierwszy krok przy realizacji filmu:** wybrać jedną klatkę fizycznego prototypu jako docelowy kadr przejścia.

### Aktualizacja scenariusza i lektora — 2026-10-04, v12

Użytkownik zatwierdził pełny polski voiceover i zlecił jego wygenerowanie w Eleven v4. Obowiązujący tekst, zachowany słowo w słowo, jest w [VOICEOVER-APPROVED-v12.txt](physical-design/visualization/VOICEOVER-APPROVED-v12.txt). [FILM-PLAN-v12.txt](physical-design/visualization/FILM-PLAN-v12.txt) oraz [voiceover-plan-v12.json](physical-design/visualization/voiceover-plan-v12.json) zastępują wcześniejsze propozycje czasu i kolejności filmu. Wygenerowany pełny lektor trwa **73,28 s**; pomiar zastępuje wcześniejszy szacunek 75–80 s. Gotowe MP3 (plik lokalny: `physical-design/visualization/voiceover-v12/SafeWall-voiceover-pl-v12.mp3`), WAV (plik lokalny: `physical-design/visualization/voiceover-v12/SafeWall-voiceover-pl-v12.wav`) i [timing montażowy](physical-design/visualization/voiceover-v12/README.txt). Automatyczna transkrypcja potwierdziła zgodność wszystkich słów z tekstem zatwierdzonym; ocena intonacji pozostaje do odsłuchu. Pełnego filmu jeszcze nie wyrenderowano.

Film zaczyna się deszczowym thrillerowym plenerem i zdaniem „Ktoś powierzył ci swoją historię”. Następnie przedstawia SafeWall oraz dziennikarzy, aktywistów i organizacje społeczne. Wyjaśnienie Tora i roli osobnej bramy poprzedza widoczność telefonu, dokładną etykietę „iPhone (Piotrek)”, wyłączenie radiów i kabel. Ostatnia zaakceptowana korekta lektora to „niechronionego połączenia”; w tym kontekście chodzi o ochronę trasy przez Tor, nie o brak HTTPS.

MagSafe pokazujemy wyłącznie animacją, bez dopisywania nazwy do lektora. Warstwy obudowy zamykają się równocześnie z easingiem, potem następuje przejście do Raspberry Pi/LTE, kabla i rzeczywistego materiału. Nie pokazujemy testu awarii Tora. Głównym demo będzie zmiana wyniku prawdziwego check.torproject.org po podłączeniu bramy i odświeżeniu strony w tej samej przeglądarce; wymaga to wcześniejszego wdrożenia Tora. Etykietę telefonu pokazujemy w kontekście wykrywania przez AirDrop przy udostępnianiu wszystkim, nie jako zawartość każdego pakietu.

SafeWall pada przy przedstawieniu produktu i na końcu. Dotychczasowe niebrandowane obudowy oraz zapisane premium shadery zostają zachowane. Preview pozostaje 960×540 / 24 fps bez premium shaderów. Seedance nie dostarcza ludzkiego głosu; polski lektor ElevenLabs i efekty są oddzielnymi ścieżkami. Ustalenia reżyserii głosu, dokładny prompt, parametry i źródła są w voiceover-v12 (plik lokalny: `physical-design/visualization/voiceover-v12/ELEVEN-V4-DIRECTION-AND-SOURCES.txt`).


### Nowe nagranie demo i przygotowanie BytePlus — v13

Użytkownik dostarczył `Documents/IMG_4626.MOV` i opisał je jako podłączenie oraz odświeżenie przy aktywnym Torze. W materiale widać przejście od czerwonego komunikatu do zielonego potwierdzenia. Obrócona kopia (plik lokalny: `physical-design/references/live-demo-v13/IMG_4626-upright.mp4`) ma 848×464 i około 9 s; oryginału nie zmieniono. To dowód obserwowanego wyniku w nagraniu i informacja użytkownika o działaniu; nie wykonano w tej operacji audytu konfiguracji wdrożonej na Pi. Wcześniejsze uwagi o stanie NAT w plikach repo pozostają odrębnym stanem do uzgodnienia z wdrożeniem.

Nowa [klatka wejścia](physical-design/references/live-demo-v13/entry-00.0s.png) zastępuje poprzednie zdjęcie jako referencja końca animacji: Pi po lewej, antena w lewo, telefon po prawej, RJ45 jeszcze niewpięty. Morph poprzedza rzeczywiste wpięcie i odświeżenie; potrzebne będzie retargetowanie Blendera do tej geometrii. [Opis i timing materiału](physical-design/references/live-demo-v13/README.txt).

Dostawca Seedance 2.5 to BytePlus ModelArk. [Gotowy pakiet pierwszej próby](physical-design/visualization/seedance-byteplus-v13/START-HERE.txt) zawiera prompt dopasowany do lektora oraz dwa obrazy: wygląd produktu i nowo wyrenderowany kadr przejścia do Blendera. Ustawienia: Reference, 16 s (około 14 s w montażu), 16:9, Draft 480p, Audio OFF. Generacja nie została uruchomiona. Ostateczny styk obrazu Seedance z Blenderem trzeba ocenić i dopasować po otrzymaniu pierwszej próby.


### Dopisek o powerbanku i wybór lektora — v14

Zatwierdzono zdanie „Z zewnątrz przypomina zwykły powerbank.”, umieszczone po przedstawieniu SafeWall i grupy odbiorców. [Aktualny pełny tekst v14](physical-design/visualization/VOICEOVER-APPROVED-v14.txt) zachowuje pozostałą treść v12. Przed ponowną generacją całej ścieżki użytkownik wybierze męski głos na podstawie próbek pierwszych dwóch słów „Ktoś powierzył”, po polsku, w Eleven v4. Pakiet próbek (plik lokalny: `physical-design/visualization/voice-auditions-v14/README.txt`). Timing nowego głosu wymaga ponownego pomiaru; dotychczasowe 73,28 s dotyczy pliku v12 bez nowego zdania.


### Dłuższy odsłuch porównawczy — v15

Użytkownik poprosił o całe otwarcie zamiast dwóch słów oraz minimum 5 s dla każdej próbki. Próbki v15 (plik lokalny: `physical-design/visualization/voice-auditions-v15/README.txt`) zastępują krótkie porównanie v14; zachowujemy pięć głosów: Brian, George, Daniel, Eric i Adam. Tekst: „Ktoś powierzył ci swoją historię. Teraz chcesz ją przekazać dalej — i chronić osobę, która ci zaufała.” Zatwierdzony pełny scenariusz z dopiskiem o powerbanku pozostaje w VOICEOVER-APPROVED-v14.txt.


### Daniel — pełny lektor v16

Użytkownik wybrał Daniela (próbka 03 z v15) i zlecił wygenerowanie całej ścieżki. Tekst pozostaje zgodny słowo w słowo z [zatwierdzoną wersją v14](physical-design/visualization/VOICEOVER-APPROVED-v14.txt), łącznie ze zdaniem o wyglądzie powerbanku. Model Eleven v4, język polski; jeden ciągły take. [Pakiet lektora v16](physical-design/visualization/voiceover-v16/README.txt) zawiera wskazówki głosu, parametry i po ukończeniu — zmierzone czasy.

Gotowy lektor Daniela — MP3 (plik lokalny: `physical-design/visualization/voiceover-v16/SafeWall-voiceover-pl-daniel-v16.mp3`) trwa **79,44 s**. Zapisano również WAV do montażu (plik lokalny: `physical-design/visualization/voiceover-v16/SafeWall-voiceover-pl-daniel-v16.wav`), napisy SRT oraz aktualny [timing](physical-design/visualization/voiceover-v16/edit-timings.json). Niezależna transkrypcja finalnego pliku potwierdziła wszystkie 158 słów (159 tokenów leksykalnych). Kontrola wymowy wymagała dogrywki akapitu o kablu; skład i parametry zapisano w dokumentacji v16. Pełny nowy film nadal czeka na montaż.


### Seedance w jakości docelowej — v17

Użytkownik wybrał **720p, 16:9** dla docelowego wstępu w BytePlus. [Aktualny pakiet v17](physical-design/visualization/seedance-byteplus-v17/START-HERE.txt) zastępuje próbę v13: zwykła generacja Reference, Draft OFF, Audio OFF. Proponowana długość 18 s daje zapas do cięcia przy **15,48 s**, kiedy w nagraniu Daniela zaczyna się przedstawienie SafeWall. Prompt używa dwóch istniejących referencji: wyglądu produktu i kompozycji styku z Blenderem. Wygenerowany wynik trzeba ocenić i dopasować do animacji; zadania BytePlus nie uruchomiono.


### Seedance — efekty otoczenia bez głosu, v17b

Użytkownik doprecyzował, że Seedance ma dostarczyć SFX: deszcz, kroki, szelest ubrania, zamknięcie notatnika i odłożenie urządzenia. Aktualne ustawienie to **Audio ON**, z wyraźnym zakazem głosu, szeptów, komunikatów dworcowych i muzyki w prompcie. Lektor Daniela pozostaje osobną ścieżką. Poprawiono pakiet projektu, ZIP oraz folder `SafeWall-Seedance-720p` na Pulpicie. Ta decyzja zastępuje wcześniejsze Audio OFF; obraz i timing pozostają bez zmian.


### Pełny podgląd filmu — v18

Pobrany przez użytkownika klip Seedance połączono z nowymi ujęciami Blendera, animowanym schematem Tora, AirDrop i prawdziwym materiałem `IMG_4626.MOV`. Gotowy podgląd MP4 (plik lokalny: `physical-design/visualization/launch-preview-v18/SafeWall-launch-preview-v18.mp4`) trwa **79,75 s**, ma **960×540 / 24 fps** i pełny głos Daniela. Równoczesne zamknięcie warstw trwa 5 s; nowe CG wyrenderowano w Workbench bez shaderów premium. Rzeczywisty test Tora jest pokazany w naturalnym tempie. Zachowano SFX Seedance, bez dodatkowego głosu i muzyki. [Opis, timing i ograniczenia podglądu](physical-design/visualization/launch-preview-v18/README.txt). Przejścia są roboczymi przenikaniami dopasowanych kadrów; końcowe wykończenie i shadery nie są częścią tej wersji.


### Kierunek wizualny po podglądzie v18 — pakiet v19

Użytkownik odrzucił płaskie plansze objaśniające i dopuścił Seedance jako alternatywę dla Blendera. Następny montaż ma pokazywać przestrzenne animacje z ruchem kamery, bez plansz HTML i bez ich odpowiedników w postaci płaskich paneli 3D.

Przygotowany [pakiet v19](physical-design/visualization/seedance-inserts-v19/START-HERE.txt) zawiera trzy propozycje do BytePlus: podróż przez przekaźniki Tora (23 s), widoczność telefonu w pobliżu (9 s), finał prototyp → koncepcja obudowy (12 s). Są to zamienniki odcinków 25,50–48,25 s, 48,00–56,25 s i 68,50–79,75 s; nakładki wynikają z przejść montażowych. Gotowy lektor Daniela i całkowity czas około 80 s pozostają bazą. Dokładne składanie warstw, MagSafe i przejście do rzeczywistego demo zostają w Blenderze.

Seedance: Reference, 720p, 16:9, zwykła generacja, Audio ON wyłącznie dla SFX; bez głosu i muzyki. Proste matowe materiały odpowiadają etapowi preview. Dokładny napis „iPhone (Piotrek)” z kontekstem „AirDrop · Wszyscy” oraz finałowy znak 4A dodamy później w przestrzeni ujęcia, bez osobnych plansz. Obudowa pozostaje niebrandowana. Generator nie ma tworzyć strony Tor Check ani sceny awarii połączenia.

**Stan:** gotowe prompty, referencje i ustawienia. Nie zlecono generacji BytePlus ani nie wyrenderowano nowego filmu v19. Ostatnim gotowym montażem nadal jest v18; jego płaskie fragmenty czekają na zastąpienie. Najpierw ocenić wygenerowany klip Tora, dopiero potem generować pozostałe w tym samym stylu.


### Gotowy montaż Blendera i ustalone skróty — v20

Użytkownik wybrał Blender do zastąpienia wszystkich płaskich plansz; pakiet Seedance v19 pozostaje niewykorzystaną propozycją. Gotowy film v20 (plik lokalny: `physical-design/visualization/launch-preview-v20/SafeWall-launch-preview-v20.mp4`) trwa **71,00 s**, ma 960×540 i 24 fps. To preview Workbench z prostymi materiałami. [Opis montażu](physical-design/visualization/launch-preview-v20/README.txt), projekt montażowy Blendera (plik lokalny: `physical-design/visualization/launch-preview-v20/SafeWall-edit-v20.blend`) oraz [raport kontroli](physical-design/visualization/launch-preview-v20/validation.json).

Zgodnie z zatwierdzoną pełniejszą wersją zachowano historię, cenzurę, odbiorców, powerbank, osobną bramę oraz „iPhone (Piotrek)”. Zmieniono zdanie na „SafeWall ma kierować połączenia przez anonimizującą sieć Tor.”, usunięto objaśnienie przekaźników, narrację o podłączeniu i sprawdzaniu przeglądarki oraz zdanie o dalszych krokach. [Obowiązujący tekst v20](physical-design/visualization/VOICEOVER-APPROVED-v20.txt). Daniel: ponownie wykorzystane właściwe fragmenty v16 oraz jedna dogrywka w Eleven v4. Niezależna transkrypcja kompletnej ścieżki potwierdziła wszystkie 121 tokenów.

Nowe sceny 3D pokazują ruch przez przestrzenne przekaźniki i osobną bramę, wykrywanie telefonu oraz finał z obudową, przestrzenną nazwą i logo 4A z SVG. Nazwa i znak są obok urządzenia; obudowa nadal nie jest brandowana. Składanie „kanapki” i MagSafe pozostają w filmie. Prawdziwe demo trwa od 57,75 do 66,71 s, zachowuje wszystkie 215 klatek przy 24 fps i nie zostało przyspieszone. Wyniku strony nie podmieniano. Finał nie zawiera już listy kolejnych kroków.

Czas 71 s obejmuje pełniejsze otwarcie i przestrzeń na obejrzenie rzeczywistego podłączenia bez objaśniającego lektora. Wcześniejsze 40 s było propozycją z większymi cięciami, które użytkownik odrzucił. Szacunek 65 s przed montażem nie obejmował tej przestrzeni na demo. Sceny premium oraz wcześniejsze filmy zachowano.


### Serwery, emitowana nazwa telefonu i gotowe outro — v21

Gotowy preview v21 (plik lokalny: `physical-design/visualization/launch-preview-v21/SafeWall-launch-preview-v21.mp4`): **72,67 s, 960×540, 24 fps**. Na prośbę użytkownika zakończenie z Blendera zastąpiono pełnym poziomym klipem z `marketing/outro`, bez przyspieszania; dodatkowe 1,67 s wynikają wyłącznie z długości tego zakończenia. Jest to wskazany przez użytkownika wyjątek od wcześniejszego kierunku bez plansz.

Trzy węzły przedstawia model szafy serwerowej [Compute Rack — 3DAssets.dev](https://3dassets.dev/assets/data-centre-infiltration-kit-data-centre-infiltration--49b6521a), opublikowany przez autora jako CC0. [Źródło, oryginał i hash modelu](physical-design/references/server-rack-v21/source.json) są zapisane lokalnie. W Blenderze użyto trzech egzemplarzy w skali ilustracyjnej. W ujęciu telefonu 23 animowane instancje „iPhone (Piotrek)” kolejno wychodzą z urządzenia i rozchodzą się na kilku trajektoriach. Przy telefonie pozostaje kontekst „AirDrop · Wszyscy”.

Zachowano cały tekst i głos Daniela z v20, pełne rzeczywiste demo, składanie oraz MagSafe. Porównanie PCM potwierdziło, że miks v20 pozostał identyczny w swoim dotychczasowym zakresie; dodano tylko ciszę na dłuższy koniec outro. [Opis i czasy v21](physical-design/visualization/launch-preview-v21/README.txt), edytowalny montaż Blendera (plik lokalny: `physical-design/visualization/launch-preview-v21/SafeWall-edit-v21.blend`), [raport weryfikacji](physical-design/visualization/launch-preview-v21/validation.json). Oryginalny plik outro i scena premium pozostały niezmienione.


### Krótsze demo, nazwa SafeWall i prostszy podpis — v22

Gotowy preview v22 (plik lokalny: `physical-design/visualization/launch-preview-v22/SafeWall-launch-preview-v22.mp4`): **69,92 s, 960×540, 24 fps**. Z podpisu w scenie telefonu usunięto „· Wszyscy”; pozostało samo „AirDrop”. W lektorze „Osobna brama” zastąpiono „SafeWall”. Daniel dograł całe zdanie z zasadą „internet przez Tor albo brak połączenia”; pozostałe słowa zatwierdzonego tekstu nie zmieniły się.

Rzeczywiste demo skrócono z 8,96 do 6,21 s przez przycięcie początku i końca oraz przyspieszenie do 1,35×. Zachowano podłączenie, odświeżenie i około dwóch sekund zielonego wyniku Tor Check. Klatki przeglądarki nie były retuszowane, a ich zgodność ze źródłem sprawdzono hashami. Końcowy lektor i istniejące outro z `marketing/outro` przesunięto o 2,75 s wcześniej; zachowują własne tempo.

[Aktualny tekst](physical-design/visualization/VOICEOVER-APPROVED-v22.txt), [opis montażu](physical-design/visualization/launch-preview-v22/README.txt), edytowalny projekt Blendera (plik lokalny: `physical-design/visualization/launch-preview-v22/SafeWall-edit-v22.blend`), [weryfikacja](physical-design/visualization/launch-preview-v22/validation.json). Nadal używamy podglądu Workbench, bez renderowania materiałów premium. Wcześniejsze wersje pozostają jako archiwum.
