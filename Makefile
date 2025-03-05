DOCKER=docker
DCOMPOSE=docker-compose
DCOMPOSE_REMOTE=docker compose
B_CONTEXT=backend
B_DOCKERFILE=deploy/Dockerfile.backend
B_IMAGENAME=mb-trff24-backend
DC_COMPOSE=deploy/docker-compose.yaml

build_backend:
	$(DOCKER) build -t $(B_IMAGENAME) -f $(B_DOCKERFILE) $(B_CONTEXT)

build_backend_amd64:
	$(DOCKER) build --platform linux/amd64 -t $(B_IMAGENAME) -f $(B_DOCKERFILE) $(B_CONTEXT)

volumse_down:
	$(DCOMPOSE) -f $(DC_COMPOSE) down --volumes

compose_up:
	$(DCOMPOSE) -f $(DC_COMPOSE) up -d

compose_up_remote:
	$(DCOMPOSE_REMOTE) -f $(DC_COMPOSE) up -d

clean_ds:
o	find . -name .DS_Store -print0 | xargs -0 git rm --ignore-unmatch
