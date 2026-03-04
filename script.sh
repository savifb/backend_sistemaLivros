DEPLOYMENT='deployment.yaml'
SERVICE='service.yaml'

if command -v minikube >/dev/null 2>&1; then
    echo "verificando se o minikube está rodando..."
    if ! minikube status | grep -q "host: Running"; then
        echo "minikube não está rodando. Iniciando minikube..."
        minikube start
    else
        echo "minikube já está rodando."
    fi
else
    echo "minikube não encontrado. Por favor, instale o minikube para continuar."

fi

echo "aplicando o deployment..."
kubectl apply -f $DEPLOYMENT

echo "aplicando o service..."
kubectl apply -f $SERVICE

echo "aguarde os pods iniciarem..."
kubectl wait --for=condition=available --timeout=60s deployment/livros-api

echo "iniciando port-forwarding... locall host:8000 -> 80"

kubectl port-forward service/fastapi-service 8000:80 > /dev/null &

sleep 2

#detecta o sistema operacional para abrir o navegador
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    xdg-open http://localhost:8000
elif [[ "$OSTYPE" == "darwin"* ]]; then
    open http://localhost:8000
elif [[ "$OSTYPE" == "cygwin" ]]; then

    cygstart http://localhost:8000
elif [[ "$OSTYPE" == "msys" ]]; then
    start http://localhost:8000
else
    echo "Sistema operacional não suportado para abrir o navegador automaticamente. Por favor, acesse http://localhost:8000 manualmente."
fi

echo "aplicação iniciada com sucesso! Acesse http://localhost:8000 para ver a aplicação em execução."

wait