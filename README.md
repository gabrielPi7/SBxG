# SBxG

Dies ist eine Weiterentwicklung vom Verfahren "SeqBox - Sequenced Box container", welches von Marco Pontello entwickelt wurde.

Es wurden zwei Verfahren entwickelt, welches die Aufgabe hat, eine Datei mit beigefügten Informationen auf einem Datenträger vor Verlust durch defekte Bytes zu schützen. Dazu wurde das "SeqBox"-Verfahren mit dem Sicherungsverfahren "Reed-Solomon-Codes" kombiniert.

Damit die Skripts funktioniert, muss die Python-Bibliothek reedsolo installiert werden - https://github.com/tomerfiliba/reedsolomon#installation. 

## SBxGV1

**Encode a file, to save it on a data storage**
```
(venv) C:\Users\Privat\PycharmProjects\Bachelorarbeit>codeSBxG.py test.txt
This codec can correct up to 8 errors and 16 erasures independently
1 = Encode - 2 = Decode.
1
100% abgeschlossen

```
Nachdem diese Operation durchgeführt wurde, wird die Datei mit dem Namen 'filename'+.ec in dem gleichen Verzeichnis wiedergegeben. Diese Datei kann nun entweder auf einem Datenträger abgespeichert werden, oder dekodiert werden, um zu überprüfen, ob die Kodierung erfolgreich war.

**Decode a secured file**
```
(venv) C:\Users\Privat\PycharmProjects\Bachelorarbeit>codeSBxG.py test.txt.ec
This codec can correct up to 8 errors and 16 erasures independently
1 = Encode - 2 = Decode.
2

Die Datei wurde gefunden test.txt
100% abgeschlossen
File has no errors.
```

**Scan an image-file**

Um eine (defekte)-Imagedatei auf geschützte Dateien zu durchsuchen, wird das Skript scanSBxG.py verwendet. Hierbei muss lediglich die Imagedatei mitgegeben werden. Sobald die gesuchte Datei gefunden wurde, kann mit dem wiederherstellen begonnen werden.

```
(venv) C:\Users\Privat\PycharmProjects\Bachelorarbeit>scanSBxG.py testImage.ec
File opened: testImage.ec
Fast Scan = 1 - Slow Scan = 2
1
23 kBytes durchsucht

Die Datei wurde gefunden test.txt erstellt am: 10-05-2022 22:51:07 - Größe: 44 Blöcke
Do you want to recover this file? 1 = Yes - 2 = No and continue searching - 3 = No and stop the search.
1
1: Slow scan. (errors in Bytes will be corrected) - 2: Fast Scan. (errors wont be corrected, may cause switched data-blocks!
1
Searching Blocks...
0.02 MBytes searched. 44/44 Blocks found.. All Blocks have been found.
Start creating Backupfile...

File created!
Please insert the created file "test.txt.ec" into recoverSBxG.py to decode it.
```

Diese erstellte Datei kann dann in das Skript recoverSBxG.py übergeben werden, um die ursprüngliche Datei wiederherzustellen.
```
(venv) C:\Users\Privat\PycharmProjects\Bachelorarbeit>recoverSBxG.py test.txt.ec
Disk Open
0 kBytes durchsucht
Die Datei wurde gefunden test.txt erstellt am: 10-05-2022 22:51:07 - Größe: 44 Blöcke
Do you want to recover this file? 1 = Yes - 2 = No and continue searching - 3 = No and stop the search.
1
lose block y or n?
If this option is no, then defect blocks will be added to the file aswell.
y
start recovering
100.0% wiederhergestellt. Defekte Blöcke: 0 reparierte Bytes: 351.
```
Die wiederhergestellte Datei kann daraufhin mit checkFiles.py überprüft werden, ob diese identisch mit der ursprünglichen Datei ist.
```
(venv) C:\Users\Privat\PycharmProjects\Bachelorarbeit>checkFiles.py recovered_test.txt test.txt
MD5 der ersten übergebenen Datei: ab4db585bb8183b947da9a083fd41084
MD5 der zweiten übergebenen Datei: ab4db585bb8183b947da9a083fd41084
Hash stimmt überein.
```
Diese Version schützt eine Datei vor Blockvertauschungen und vor einer gewissen Anzahl an Bytefehlern pro Block. Diese ist vordefiniert auf 8 Bytes für die erste Hälfte eines Blocks und weiteren 8 Bytes für die zweite Hälfte eines Blocks. Also bis maximal 16 Bytes.

## SBxGV2

Da die erste Version Dateien zwar vor Blockvertauschungen und einer gewissen Anzahl an Bytefehlern schützt, allerdings nicht vor kompletten Blockverlusten, wurde die Kodierung von Blöcken erweitert. Dazu wurde das gleiche Verfahren wie beim vom User entwickelten Verfahren rsbep - https://github.com/ttsiodras/rsbep-backup verwendet.

**Encode a file, to save it on a data storage**
```
(venv) C:\Users\Privat\PycharmProjects\Bachelor2.0>codeSBxG.py test.txt
1 = Encode - 2 = Decode.
1
100.0% done. .
```

**Scan an image-file**
```
(venv) C:\Users\Privat\PycharmProjects\Bachelor2.0>codeSBxG.py testimage.ec
1 = Encode - 2 = Decode.
2
File opened: testimage.ec
Fast Scan = 1 - Slow Scan = 2
1
0 kBytes durchsucht

File found: test.txt - created: 10-05-2022 23:33:31 - size: 392 blocks
Do you want to recover this file? 1 = Yes - 2 = No and continue searching - 3 = No and stop the search.
1
0.21 MBytes searched. 400/400 Blocks found.. All Blocks have been found.
Start recovering file...
391/391 Blocks recovered. File has been successfully recovered - recovered_test.txt
```

Bei dieser Version können Blöcke vertauscht und eine bestimmte Anzahl an Bytes verloren gehen. Allerdings können auch komplette Blöcke verloren gehen. Bei dieser Konfiguration bis zu drei pro 100 Blöcke. Allerdings kann das weiter erhöht werden.

## Create errors in image files

Um Fehler in einer Imagedatei zu simulieren, wurde das Skript errors.py erstellt. Dieses kann Blockvertauschungen und Bytefehler vornehmen.
```
(venv) C:\Users\Privat\PycharmProjects\Bachelor2.0>errors.py testimage.ec
1: Swap Blocks - 2: Change first twelve Bytes - 3: Change eight random Bytes per Block
1
349 Blocks swapped..
```
