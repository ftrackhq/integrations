@ECHO OFF

REM Evaluate the full path to script
SET CODESIGN_SCRIPT_PATH=%~dp0

REM Remember to login to Google first

FOR /F "tokens=* USEBACKQ" %%F IN (`gcloud auth print-access-token`) DO (
SET TOKEN=%%F
)
java -jar %CODESIGN_SCRIPT_PATH%\jsign.jar --storetype GOOGLECLOUD --storepass "%TOKEN%" --keystore "projects/ftrack-code-signing/locations/global/keyRings/EVCodeSigningKeyRing" --alias "ftrack" --certfile "%CODESIGN_SCRIPT_PATH%\codesign-chain.pem" --tsmode RFC3161 --tsaurl http://timestamp.globalsign.com/tsa/r6advanced1 %1
