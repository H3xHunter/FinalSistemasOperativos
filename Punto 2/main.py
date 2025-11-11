from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, field_validator
import boto3
from botocore.exceptions import ClientError
import csv
import io
from typing import List

app = FastAPI(title="Person Data API", version="1.0.0")

# Configuración de S3
S3_BUCKET = "sistoperat-fastapi-h3x"
S3_KEY = "personas.csv"
s3_client = boto3.client('s3')


class Persona(BaseModel):
    """Modelo Pydantic para validar datos de entrada"""
    nombre: str = Field(..., min_length=1, max_length=100)
    edad: int = Field(..., ge=0, le=150)
    altura: float = Field(..., gt=0, le=3.0)
    
    @field_validator('nombre')
    @classmethod
    def validar_nombre(cls, v):
        if not v.strip():
            raise ValueError('El nombre no puede estar vacío')
        return v.strip()


def leer_csv_desde_s3() -> List[List[str]]:
    """Lee el CSV desde S3 y retorna las filas"""
    try:
        response = s3_client.get_object(Bucket=S3_BUCKET, Key=S3_KEY)
        contenido = response['Body'].read().decode('utf-8')
        reader = csv.reader(io.StringIO(contenido))
        return list(reader)
    except ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchKey':
            # El archivo no existe, retornar solo headers
            return [['nombre', 'edad', 'altura']]
        raise


def escribir_csv_a_s3(filas: List[List[str]]):
    """Escribe las filas al CSV en S3"""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerows(filas)
    
    s3_client.put_object(
        Bucket=S3_BUCKET,
        Key=S3_KEY,
        Body=output.getvalue().encode('utf-8'),
        ContentType='text/csv'
    )


@app.post("/persona", status_code=201)
async def agregar_persona(persona: Persona):
    """
    Agrega una nueva persona al CSV en S3.
    Sobrescribe el archivo existente con los datos actualizados.
    """
    try:
        # Leer datos existentes
        filas = leer_csv_desde_s3()
        
        # Agregar nueva fila
        filas.append([persona.nombre, str(persona.edad), str(persona.altura)])
        
        # Sobrescribir archivo en S3
        escribir_csv_a_s3(filas)
        
        return {
            "mensaje": "Persona agregada exitosamente",
            "datos": persona.dict()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al guardar en S3: {str(e)}")


@app.get("/personas/count")
async def contar_personas():
    """
    Retorna el número de filas de datos en el CSV (excluyendo el header).
    """
    try:
        filas = leer_csv_desde_s3()
        # Restar 1 para excluir el header
        num_personas = len(filas) - 1 if len(filas) > 0 else 0
        
        return {
            "total_filas": num_personas,
            "archivo": S3_KEY
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al leer desde S3: {str(e)}")


@app.get("/")
async def root():
    """Endpoint de verificación"""
    return {"mensaje": "API funcionando correctamente"}
