MORSENUMERIPC — CREAZIONE DEL FILE EXE SENZA INSTALLARE PYTHON SUL TUO PC

Questo progetto usa GitHub Actions per compilare l'app su un computer Windows online.
Non devi installare Python sul tuo PC. Serve un account GitHub gratuito e una connessione Internet.

PASSAGGI

1. Apri https://github.com e accedi o crea un account gratuito.
2. Crea un nuovo repository: pulsante + in alto a destra > New repository.
   Nome consigliato: MorseNumeriPC
   Seleziona Public oppure Private, poi Create repository.
3. Nel repository, carica i file di QUESTA cartella mantenendo la struttura:
   - MorseNumeriPC.py
   - requirements.txt
   - README.txt (facoltativo)
   - .github/workflows/build-windows.yml

   Per caricarli dal browser: Add file > Upload files. Attenzione: la cartella nascosta
   .github deve essere inclusa. Se il browser non consente di caricarla facilmente, usa
   la procedura alternativa descritta più sotto.
4. Premi Commit changes. Il workflow parte automaticamente dopo il caricamento sulla
   branch main. In alternativa: scheda Actions > Compila MorseNumeriPC per Windows > Run workflow.
5. Apri la scheda Actions e seleziona l'esecuzione più recente, attendi che sia verde (Success).
6. In fondo alla pagina dell'esecuzione, sotto Artifacts, scarica MorseNumeriPC-Windows.
7. Estrai lo ZIP scaricato. Troverai MorseNumeriPC.exe: avvialo con doppio clic.

IMPORTANTE
- Il file EXE non è ancora compilato né testato: la compilazione deve essere eseguita su GitHub.
- La prima esecuzione potrebbe mostrare un avviso di Windows perché l'app non è firmata digitalmente.
- L'app ascolta l'audio del PC tramite loopback Windows; la compatibilità dipende dai dispositivi audio
  e dal sistema. Va verificata sul PC dell'utente.
- Non caricare in questo repository informazioni personali o altri file privati.

SE NON RIESCI A CARICARE .github DAL BROWSER
Dimmi a quale passaggio sei arrivato e ti guiderò. Non occorre installare strumenti sul PC.
