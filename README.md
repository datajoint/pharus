DJ-GUI-API Backend

Built on top of flask

Requirements:
- Docker
- Docker Compose

To start the server simply run: ```docker-compose up```

NOTE: The docker-compose file creates a docker network call dj-gui-api which is meant to connect to front end to this back end via reverse proxy for developemnt. Final deployment will be using K8 or electron with some production server for flask