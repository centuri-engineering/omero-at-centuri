update:
	docker build --no-cache -t centuri/centuri-omero-server docker/
	docker push centuri/centuri-omero-server

test:
	cd test_omero && docker-compose pull \
			      && docker-compose up -d \
				  && docker-compose exec omeroserver /data/run_impomero.sh
