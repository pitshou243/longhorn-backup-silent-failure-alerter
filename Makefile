lint:
    yamllint .
    python -m py_compile src/exporter.py

docker-build:
    docker build -t longhorn-backup-silent-failure-alerter .

install:
    kubectl apply -f deploy/all-in-one.yaml

dashboard:
    kubectl apply -f monitoring/
