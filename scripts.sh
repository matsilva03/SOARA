#!/bin/bash

case $1 in
  frontend)
    cd frontend && npm run dev
    ;;
  backend)
    cd backend && python manage.py runserver
    ;;
  servico)
    cd servico-alocacao && python src/main.py
    ;;
  *)
    echo "Comandos disponíveis: frontend | backend | servico"
    ;;
esac

