#!/bin/bash

# Colores para la terminal
VERDE='\033[0;32m'
AZUL='\033[0;34m'
NC='\033[0m' # No Color


# Prueba 1 
echo -e "\n${VERDE}[1/6] Probando: user/api/v1/${NC}"
echo "Ejecutando: curl -H 'x-api-key: test' -H 'x-origin: local' http://localhost:8080/user/api/v1/"
curl -s -H "x-api-key: test" -H "x-origin: local" http://localhost:8080/user/api/v1/
echo -e "\n"

# Prueba 2
echo -e "\n${VERDE}[2/6] Probando: user/api/v2/${NC}"
echo "Ejecutando: curl -H 'x-api-key: test' -H 'x-origin: local' http://localhost:8080/user/api/v2/"
curl -s -H "x-api-key: test" -H "x-origin: local" http://localhost:8080/user/api/v2/
echo -e "\n"

# Prueba 3
echo -e "\n${VERDE}[3/6] Probando: user/api/v1234${NC}"
echo "Ejecutando: curl -H 'x-api-key: test' -H 'x-origin: local' http://localhost:8080/user/api/v1234"
curl -s -H "x-api-key: test" -H "x-origin: local" http://localhost:8080/user/api/v1234
echo -e "\n"

# Prueba 4
echo -e "\n${VERDE}[4/6] Probando: core/api/v1/${NC}"
echo "Ejecutando: curl -H 'x-api-key: test' -H 'x-origin: local' http://localhost:8080/core/api/v1/"
curl -s -H "x-api-key: test" -H "x-origin: local" http://localhost:8080/core/api/v1/
echo -e "\n"

# Prueba 5
echo -e "\n${VERDE}[5/6] Probando: core/api/v2/${NC}"
echo "Ejecutando: curl -H 'x-api-key: test' -H 'x-origin: local' http://localhost:8080/core/api/v2/"
curl -s -H "x-api-key: test" -H "x-origin: local" http://localhost:8080/core/api/v2/
echo -e "\n"

# Prueba 6
echo -e "\n${VERDE}[6/6] Probando: Check General${NC}"
echo "Ejecutando: curl http://localhost:8080/check"
curl -s http://localhost:8080/check
echo -e "\n"




