cd databases
del Chart.lock
del charts
@REM helm dependency update
cd ..
helm upgrade --install databases databases

cd storage
cd ..
helm upgrade --install storage storage

helm upgrade --install app app