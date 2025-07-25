from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.responses import FileResponse
from docx import Document
import uuid
import os

app = FastAPI()

class Medidas(BaseModel):
    comprimento: float
    largura: float
    espessura: float

class Nodulo(BaseModel):
    local: str
    dimensoes_mm: str
    composicao: str
    ecogenicidade: str
    margens: str
    calcificacoes: str
    formato: str

class EntradaTireoide(BaseModel):
    idade: int
    sexo: str
    medidas_lobo_direito: Medidas
    medidas_lobo_esquerdo: Medidas
    espessura_istmo: float
    nodulos: list[Nodulo]

def calcular_volume(m: Medidas) -> float:
    return round(m.comprimento * m.largura * m.espessura * 0.523, 2)

def gerar_laudo_texto(dados: EntradaTireoide) -> str:
    vdir = calcular_volume(dados.medidas_lobo_direito)
    vesq = calcular_volume(dados.medidas_lobo_esquerdo)
    vtotal = round(vdir + vesq, 2)

    nod = dados.nodulos[0] if dados.nodulos else None
    tirads = "TI-RADS 4" if nod else "Sem nódulos identificados"

    texto = f"""ULTRASSONOGRAFIA DA TIREOIDE

REFERÊNCIA CLÍNICA:
Exame solicitado para avaliação da glândula tireoide.

TÉCNICA:
Exame realizado com transdutor linear de alta frequência.

RELATÓRIO:
Lobo direito: {vdir} cm³
Lobo esquerdo: {vesq} cm³
Volume total estimado: {vtotal} cm³
Istmo: {dados.espessura_istmo:.2f} cm

{"Nódulo identificado no lobo " + nod.local + ", medindo " + nod.dimensoes_mm + " mm, de composição " + nod.composicao + ", ecogenicidade " + nod.ecogenicidade + ", margens " + nod.margens + ", calcificações " + nod.calcificacoes + ", formato " + nod.formato + "." if nod else "Ausência de nódulos visíveis."}

OPINIÃO:
• {tirads}
• Volume glandular compatível com sexo {dados.sexo} e idade {dados.idade} anos.
"""
    return texto

def gerar_docx(texto: str, path: str):
    doc = Document()
    for linha in texto.strip().split("\n"):
        doc.add_paragraph(linha)
    doc.save(path)

@app.post("/gerar-laudo-tireoide")
def gerar_laudo(dados: EntradaTireoide):
    laudo = gerar_laudo_texto(dados)
    nome_arquivo = f"{uuid.uuid4()}.docx"
    caminho = f"app/output/{nome_arquivo}"
    gerar_docx(laudo, caminho)
    return {
        "laudo_txt": laudo,
        "download_docx": f"/baixar-laudo/{nome_arquivo}"
    }

@app.get("/baixar-laudo/{arquivo}")
def baixar_laudo(arquivo: str):
    caminho = os.path.join("app/output", arquivo)
    return FileResponse(caminho, media_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document', filename=arquivo)