cd ..
cd helm-charts
helm uninstall app
timeout /t 15
cd ..
cd src

docker login

@REM cd api-crawler
@REM docker build -t eriabark/api-crawler .
@REM docker push eriabark/api-crawler
@REM cd ..

cd controller
docker build -t eriabark/controller .
docker push eriabark/controller
cd ..

@REM cd see
@REM docker build -t eriabark/see .
@REM docker push eriabark/see
@REM cd ..

@REM cd sparkjob
@REM docker build -t eriabark/sparkjob .
@REM docker push eriabark/sparkjob
@REM cd ..

cd ..
cd helm-charts
timeout /t 15
helm upgrade --install app app