#!/bin/bash

# Variables - AJUSTA ESTOS VALORES
AWS_REGION="us-east-1"
AWS_ACCOUNT_ID="380141753588"
ECR_REPOSITORY="fastapi-lambda"
IMAGE_TAG="latest"

# Nombre completo de la imagen
IMAGE_URI="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPOSITORY}"

echo "🔧 Construyendo imagen Docker..."
docker build -t ${ECR_REPOSITORY}:${IMAGE_TAG} .

echo "🏷️  Etiquetando imagen..."
docker tag ${ECR_REPOSITORY}:${IMAGE_TAG} ${IMAGE_URI}:${IMAGE_TAG}

echo "🔑 Autenticando con ECR..."
aws ecr get-login-password --region ${AWS_REGION} | \
    docker login --username AWS --password-stdin ${IMAGE_URI}

echo "📤 Subiendo imagen a ECR..."
docker push ${IMAGE_URI}:${IMAGE_TAG}

echo "✅ Imagen subida exitosamente: ${IMAGE_URI}:${IMAGE_TAG}"