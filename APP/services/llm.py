"""
Módulo de integração com LLMs (Gemini) para responder consultas baseadas em RAG.

Este módulo implementa a conexão com a API do Gemini e fornece funções
para gerar respostas baseadas em contexto recuperado do Qdrant.
"""

import os
import traceback
import google.generativeai as genai
from typing import List, Dict, Any

from APP.core import config

# Inicialização lazy do cliente Gemini
_gemini_initialized = False

def initialize_gemini():
    """
    Inicializa a API do Gemini com a chave obtida das variáveis de ambiente.
    
    Returns:
        bool: True se a inicialização foi bem-sucedida, False caso contrário.
    """
    global _gemini_initialized
    
    if _gemini_initialized:
        return True
    
    try:
        # Configura a API do Gemini
        genai.configure(api_key=config.GEMINI_API_KEY)
        _gemini_initialized = True
        return True
    except Exception as e:
        print(f"ERRO ao inicializar Gemini API: {str(e)}")
        print(f"Detalhes do erro: {traceback.format_exc()}")
        return False

def generate_response(query: str, retrieved_context: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Gera uma resposta usando o modelo Gemini com base na consulta e no contexto recuperado.
    
    Args:
        query: A pergunta do usuário
        retrieved_context: Resultados recuperados do Qdrant com metadados
        
    Returns:
        Dict[str, Any]: Dicionário com a resposta gerada e informações adicionais
    """
    if not initialize_gemini():
        return {
            "status": "error",
            "message": "Falha ao inicializar a API do Gemini",
            "answer": None
        }
    
    try:
        # Prepara o contexto formatado para o prompt
        formatted_context = ""
        for i, item in enumerate(retrieved_context, 1):
            formatted_context += f"--- Documento {i} ---\n"
            payload = item.get("payload", {})
            for key, value in payload.items():
                formatted_context += f"{key}: {value}\n"
            formatted_context += f"Relevância: {item.get('score', 0):.4f}\n\n"
        
        # Template do prompt
        prompt = f"""
        Você é um assistente especializado em dados da TOTVS Atlas, uma empresa de software de gestão empresarial.
        
        CONTEXTO:
        {formatted_context}
        
        INSTRUÇÕES:
        1. Use APENAS as informações do contexto fornecido para responder à pergunta.
        2. Se o contexto não contiver a informação necessária, diga que você não tem dados suficientes.
        3. Seja objetivo, conciso e profissional em suas respostas.
        4. NÃO invente informações que não estejam nos dados fornecidos.
        5. Formate a resposta de forma clara e estruturada.
        
        PERGUNTA DO USUÁRIO:
        {query}
        
        RESPOSTA:
        """
        
        # Configura o modelo Gemini
        model = genai.GenerativeModel(config.LLM_MODEL)
        
        # Gera a resposta
        response = model.generate_content(prompt)
        
        # Retorna a resposta formatada
        return {
            "status": "success",
            "answer": response.text,
            "model": config.LLM_MODEL,
            "context_docs_count": len(retrieved_context)
        }
        
    except Exception as e:
        print(f"ERRO ao gerar resposta com Gemini: {str(e)}")
        print(f"Detalhes do erro: {traceback.format_exc()}")
        
        return {
            "status": "error",
            "message": f"Erro ao gerar resposta: {str(e)}",
            "answer": "Desculpe, houve um problema ao processar sua consulta. Por favor, tente novamente."
        }