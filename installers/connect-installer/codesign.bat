@ECHO OFF

REM Remember to login to Google first

FOR /F "tokens=* USEBACKQ" %%F IN (`gcloud auth print-access-token`) DO (
SET TOKEN=%%F
)
java -jar jsign.jar --storetype GOOGLECLOUD --storepass "%TOKEN%" --keystore "projects/ftrack-code-signing/locations/global/keyRings/EVCodeSigningKeyRing" --alias "ftrack" --certfile "codesign-chain.pem" --tsmode RFC3161 --tsaurl http://timestamp.globalsign.com/tsa/r6advanced1 %1
