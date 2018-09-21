docker run -it --rm \
  -e "HOME=/home" \
  -v $HOME/.aws:/home/.aws \
  henritesti:latest


# Kun dockerissa sisällä, niin tämä ja entteriä
npm init

# installoi python requirementsit
npm install --save serverless-python-requirements

# deployaa lambdan
serverless deploy

# serverless remove