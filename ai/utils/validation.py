# application/ai/utils/validation.py
import re

class Validation:
  """Utilidades para validación de respuestas AI"""
  
  @staticmethod
  def is_model_refusal(response):
    """Verifica si el modelo rechazó generar la respuesta"""
    refusal_indicators = [
      "No puedo cumplir",
      "I cannot fulfill", 
      "I cannot comply",
      "I'm sorry",
      "I am sorry",
      "I cannot create",
      "I cannot generate",
      "as an AI",
      "as a language model"
    ]
    
    response_lower = response.lower()
    return any(indicator.lower() in response_lower for indicator in refusal_indicators)
  
  @staticmethod
  def is_valid_sql(sql_statement):
    """Valida si una sentencia SQL tiene formato básico correcto"""
    sql_upper = sql_statement.upper().strip()
    
    valid_starts = ['CREATE TABLE', 'DROP TABLE', 'ALTER TABLE', 'INSERT INTO', 'SELECT']
    starts_with_valid = any(sql_upper.startswith(start) for start in valid_starts)
    
    ends_with_semicolon = sql_upper.strip().endswith(';')
    
    return starts_with_valid and ends_with_semicolon
  
  @staticmethod
  def count_sql_statements(text):
    """Cuenta el número de sentencias SQL en un texto"""
    pattern = r'(CREATE TABLE[^;]+;|DROP TABLE[^;]+;)'
    matches = re.findall(pattern, text, re.IGNORECASE | re.DOTALL)
    return len(matches)