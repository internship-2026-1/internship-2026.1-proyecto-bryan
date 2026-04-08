#!/bin/bash

# Colores para la terminal
VERDE='\033[0;32m'
AZUL='\033[0;34m'
NC='\033[0m' # No Color



# Prueba 1
echo -e "\n${VERDE}[1/6] Probando: Check General${NC}"
echo "Ejecutando: curl localhost:8080/check"
curl -s localhost:8080/check
echo -e "\n"

# Prueba 2
echo -e "${VERDE}[2/6] Probando: Core API v1${NC}"
echo "Ejecutando: curl localhost:8080/core/api/v1/"
curl -s localhost:8080/core/api/v1/
echo -e "\n"

# Prueba 3
echo -e "${VERDE}[3/6] Probando: Auth API v1${NC}"
echo "Ejecutando: curl localhost:8080/api/v1/auth/"
curl -s localhost:8080/auth/api/v1/
echo -e "\n"

# Prueba 4
echo -e "${VERDE}[4/6] Probando: Ruta inexistente (404)${NC}"
echo "Ejecutando: curl localhost:8080/desconocida"
curl -s localhost:8080/desconocida
echo -e "\n"

# Prueba 5
echo -e "${VERDE}[5/6] Probando: Core con API Key y Origin${NC}"
echo "Ejecutando: curl -H 'x-api-key: abc' -H 'x-origin: prueba' localhost:8080/core/api/v1/"
curl -s -H "x-api-key: abc" -H "x-origin: prueba" localhost:8080/core/api/v1/
echo -e "\n"

# Prueba 6

# Prueba 6
echo -e "${VERDE}[6/6] Probando: Auth con API Key y Origin${NC}"
echo "Ejecutando: curl -H 'x-api-key: abc' -H 'x-origin: prueba' localhost:8080/api/v1/auth/"
curl -s -H "x-api-key: abc" -H "x-origin: prueba" localhost:8080/api/v1/auth/
