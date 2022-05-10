# SBxG

Dies ist eine Weiterentwicklung vom Verfahren "SeqBox - Sequenced Box container", welches von Marco Pontello entwickelt wurde.

Es wurden zwei Verfahren entwickelt, welches die Aufgabe hat, eine Datei mit angefügten Informationen auf einem Datenträger vor Verlust durch defekte Bytes zu schützen. Dazu wurde das "SeqBox"-Verfahren mit dem Sicherungsverfahren "Reed-Solomon-Codes" kombiniert.

Damit die Skripts funktioniern, muss die Python-Bibliothek reedsolo installiert werden - https://github.com/tomerfiliba/reedsolomon#installation. 

SBxGV1

**Encode a file, to save it on a data storage**

```
(venv) C:\Users\Privat\PycharmProjects\Bachelorarbeit>codeSBxG.py test.txt
This codec can correct up to 8 errors and 16 erasures independently
1 = Encode - 2 = Decode.
1
100% abgeschlossen

```
After this operation, the file gets returned as 'filename'+.ec in the same directory. This file is now saved and can be placed on a data storage or be decoded to check, if the operation was successfull.

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
