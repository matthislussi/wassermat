## Resources

- https://medium.com/google-cloud/build-a-weather-station-using-google-cloud-iot-core-and-mongooseos-7a78b69822c5
- https://github.com/GoogleCloudPlatform/python-docs-samples.git


## google cloud sdk

- download from google
- cd ~/stash/projects.ext/google-cloud-sdk/
- ./install.sh


## pyenv

- brew install pyenv
- brew install pyenv-virtualenv
- pyenv virtualenv 3.6.7 wassermat
- pyenv local wassermat
- pip install --proxy http://proxy.adnovum.ch:3128 -r requirements.txt


## Firebase installation & configuration

- project=wassermat
- npm install -g firebase-tools
- firebase login
- firebase init
- firebase functions:config:set bigquery.datasetname="wassermat_iot" bigquery.tablename="raw_data"
- firebase deploy --only functions
- firebase functions:config:get


## Big Query configuration

- project=wassermat
- dataset=wassermat_iot
- table=raw_data


