# Beschreibung picoCosmo


Diese Software dient zur Aufzeichnung und Analyse kurzer Pulse, die in Detektoren zum Nachweis von Myonen aus der Kosmischen Strahlung entstehen, z.B. den Szintillatorplatten des CosMO-Experimtens des Netzwerks Teilchenwelt, <http://www.Teilchenwelt.de>, oder im Kamiokanne-Experiment (ein Wasser-Cherenkov-Detektor mit
Auslese mittels einer Photoröhre).

Die Daten werden mit einem modernen USB-Oszilloskop
(PicoScope der Firma PichoTechnology) aufgenommen.
Ein Puffer-Manager sammelt und verteilt die aufgezeichneten
Pulsformen an Consumer-Prozesse, die
sie in Echtzeit anzeigen oder die Daten analysieren.

Die Analyse der aufgezeichneten Pulsformen verläuft in drei Schritten:

1. #### Validierung der Trigger-Schwelle des Oszilloskops
   Dazu wird der Signalverlauf um den Triggerzeitpunkt mit einem
   Musterpuls verglichen und das Signal akzeptiert, wenn die Form gut  
   übereinstimmt und eine Mindestpulshöhe überschritten wird.

2. #### Suche nach Koinzidenzen
   Als nächstes werden Pulse auf allen aktiven Kanälen in der Nähe
   des Triggerzeitpunkts gesucht. Bei mehr als einem
   angeschlossenen Detektor wird ein aufgezeichnetes
   Ereignis akzeptiert, wenn mindestens zwei in
   zeitlicher Koinzidenz auftreten. 

3. #### Suche nach verzögerten Pulsen
   Im optionalen dritten Schritt werden weitere Pulse auf allen
   aktiven Kanälen gesucht und die Zeitdifferenz zum
   Triggerzeitpunkt festgehalten. Solche Pulse treten auf,
   wenn ein Myon aus der kosmischen Strahlung nach Durchgang
   durch den bzw. die Detektoren gestoppt und das aus dem Zerfall
   entstandene Elektron registriert wird. Die registrierten
   individuellen Lebensdauern folgen einer Exponential-Verteilung mit
   einer mittleren Lebensdauern von 2,2 µs, die auf diese Weise
   bestimmt werden kann.

Die Software bietet Echtzeit-Anzeigen der Myon-Rate und
der Detektorsignale sowie von Histogrammen der Pulshöhen
und der Myon-Lebensdauern. Zusätzlich können Mehrfach-Pulse
als Rohdaten der registrierten Pulsformen oder
als Bilder im `.png`-Format gespeichert werden.


## Konfiguration und Programmausführung

Die Datanaufnahme und Analyse wird über die grafische Oberfläche    
(`./CosmoGui.py xxx.daq`) oder über die Kommandozeile     
(`./runCosmo xxxx.daq`) gestartet.

Die benötigten Information zur Konfiguration des USB-Oszilloskops,
der Pufferverwaltung und für die Pulsanalyse werden in 
Konfigurationsdateien im `.yaml`-Format bereit gestellt.
Die für eine spezielle Konfiguration verwendeten Dateien sind in einer Datei im `.yaml`-Format mit der Endung `.daq` enthalten.
Das folgende Beispiel gilt für den Kamiokanne-Detektor:

    # file Kanne.daq ----------------------
    #   configuration files for Kamiokanne

    DeviceFile: config/PMpulse.yaml  # Oscilloscope configuration
    BMfile:     config/BMconfig.yaml # Buffer Manager config.
    PFfile:     config/PFKanne.yaml # Pulse Filter config.

Die Konfigurationsdateien werden in die grafische Oberfläche
geladen und können dort editiert werden.
Über die grafische Oberfläche kann ein Name für die Datennahme
festgelegt werden. Alle für eine Datennahme (einen sogenannten
`Run`) benötigten Konfigurationsdateien und die Programmausgaben
werden in einem eigenen Verzeichnis abgelegt, deren Name aus dem
Namen für die Datennahme und dem Startzeitpunkt abgeleitet wird.


Nach dem Start eines Runs startet die grafische Oberfläche des
Puffer-Managers und die in der Konfiguration festgelegten
Echtzeit-Anzeigen. Über die Kontrollflächen des Puffer-Managers kann
die Datennahme pausiert (`Pause`), wieder aufgenommen (`Resume`) oder
beendet werden kann (`Stop` und `EndRun`). In gestopptem Zustand werden
die Ausgabedateien geschlossen, aber alle Fenster bleiben noch geöffnet,
so dass Grafiken betrachtet  oder gespeichert und statistische Information
ausgewertet werden können. Wird der Run beendet, verschwinden alle Fenster. 

