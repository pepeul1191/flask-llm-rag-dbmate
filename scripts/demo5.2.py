import os
import re
import logging
from typing import Dict, List

# Configure logging
logging.basicConfig(level=logging.INFO)

def parse_puml_file(puml_path: str) -> Dict:
    """
    Parse a PlantUML file to extract database schema information
    """
    if not os.path.exists(puml_path):
        logging.error(f"PUML file not found at path: {puml_path}")
        return None
    
    try:
        with open(puml_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        logging.info("PUML file loaded successfully.")
        return parse_puml_content(content)
    
    except Exception as e:
        logging.error(f"Error reading PUML file: {e}")
        return None

def parse_puml_content(content: str) -> Dict:
    """
    Parse PlantUML content with the specific format from the example
    """
    schema = {
        'entities': [],
        'relationships': []
    }
    
    # Remove comments
    content = re.sub(r'^\s*//.*$', '', content, flags=re.MULTILINE)
    
    # Extract entity definitions - match the specific format
    entity_pattern = r'entity\s+"([^"]+)"\s+as\s+\w+\s+\{\s*([^}]+)\}'
    entities = re.findall(entity_pattern, content, re.DOTALL | re.IGNORECASE)
    
    print(f"Found {len(entities)} entities")
    
    for entity_name, entity_body in entities:
        entity_name = entity_name.strip()
        print(f"Processing entity: {entity_name}")
        
        entity = {
            'name': entity_name,
            'attributes': [],
            'primary_keys': []
        }
        
        # Process each line in entity body
        lines = entity_body.strip().split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            print(f"Processing line: '{line}'")
            
            # Match attribute pattern: +id : INTEGER
            attr_match = re.match(r'\+\s*(\w+)\s*:\s*(\w+)', line)
            if attr_match:
                attr_name, attr_type = attr_match.groups()
                
                # Check if it's a primary key (usually the first attribute with + and id-like name)
                is_primary_key = (attr_name.lower() == 'id' or 
                                attr_name.lower().endswith('_id') and 
                                'id' in attr_name.lower())
                
                attribute = {
                    'name': attr_name.strip(),
                    'type': map_uml_type_to_sql(attr_type.strip()),
                    'is_primary_key': is_primary_key
                }
                entity['attributes'].append(attribute)
                
                if is_primary_key:
                    entity['primary_keys'].append(attr_name.strip())
                
                print(f"Added attribute: {attribute}")
        
        schema['entities'].append(entity)
    
    # Extract relationships - match the specific format
    relationship_pattern = r'(\w+)\s+--\s+(\w+)\s*:\s*"([^"]*)"'
    relationships = re.findall(relationship_pattern, content)
    
    for entity1, entity2, description in relationships:
        relationship = {
            'entity1': entity1.strip(),
            'entity2': entity2.strip(),
            'type': determine_relationship_type(description),
            'description': description.strip()
        }
        schema['relationships'].append(relationship)
        print(f"Added relationship: {relationship}")
    
    logging.info(f"Parsed {len(schema['entities'])} entities and {len(schema['relationships'])} relationships")
    return schema

def map_uml_type_to_sql(uml_type: str) -> str:
    """
    Map UML data types to SQLite data types
    """
    # Remove parentheses and size information
    base_type = re.sub(r'\([^)]*\)', '', uml_type).upper()
    
    type_mapping = {
        'INTEGER': 'INTEGER',
        'INT': 'INTEGER',
        'BIGINT': 'INTEGER',
        'BOOLEAN': 'INTEGER',
        'BOOL': 'INTEGER',
        'VARCHAR': 'TEXT',
        'CHAR': 'TEXT',
        'STRING': 'TEXT',
        'TEXT': 'TEXT',
        'DATETIME': 'TEXT',
        'TIMESTAMP': 'TEXT',
        'DATE': 'TEXT',
        'TIME': 'TEXT',
        'FLOAT': 'REAL',
        'DOUBLE': 'REAL',
        'DECIMAL': 'REAL',
        'NUMERIC': 'REAL',
        'BLOB': 'BLOB'
    }
    
    return type_mapping.get(base_type, 'TEXT')

def determine_relationship_type(description: str) -> str:
    """
    Determine relationship type based on description
    """
    description_lower = description.lower()
    
    if 'has many' in description_lower:
        return 'one_to_many'
    elif 'belongs to' in description_lower:
        return 'many_to_one'
    elif 'has one' in description_lower:
        return 'one_to_one'
    elif 'many to many' in description_lower:
        return 'many_to_many'
    else:
        # Default based on common patterns
        if 'many' in description_lower:
            return 'one_to_many'
        else:
            return 'many_to_one'

def generate_sqlite_schema(schema: Dict) -> str:
    """
    Generate SQLite schema from parsed UML data
    """
    sql_statements = []
    
    # Generate CREATE TABLE statements
    for entity in schema['entities']:
        table_sql = generate_create_table(entity)
        sql_statements.append(table_sql)
    
    # Generate foreign key constraints based on relationships and naming conventions
    sql_statements.extend(generate_foreign_keys(schema))
    
    # Add indexes for better performance
    sql_statements.extend(generate_indexes(schema))
    
    return '\n\n'.join(sql_statements)

def generate_create_table(entity: Dict) -> str:
    """
    Generate CREATE TABLE statement for an entity
    """
    columns = []
    
    for attr in entity['attributes']:
        column_def = f"    {attr['name']} {attr['type']}"
        
        if attr['is_primary_key']:
            column_def += " PRIMARY KEY"
            if attr['type'] == 'INTEGER':
                column_def += " AUTOINCREMENT"
        
        columns.append(column_def)
    
    # Handle composite primary keys if needed
    if len(entity['primary_keys']) > 1:
        pk_columns = ', '.join(entity['primary_keys'])
        columns.append(f"    PRIMARY KEY ({pk_columns})")
    
    table_sql = f"CREATE TABLE {entity['name']} (\n"
    table_sql += ',\n'.join(columns)
    table_sql += "\n);"
    
    return table_sql

def generate_foreign_keys(schema: Dict) -> List[str]:
    """
    Generate foreign key constraints based on relationships and field names
    """
    fk_statements = []
    
    # First, generate FKs based on explicit relationships
    for relationship in schema['relationships']:
        if relationship['type'] in ['many_to_one', 'belongs_to']:
            fk_sql = generate_relationship_foreign_key(relationship, schema)
            if fk_sql:
                fk_statements.append(fk_sql)
    
    # Then, generate FKs based on naming conventions (_id fields)
    for entity in schema['entities']:
        for attr in entity['attributes']:
            if (attr['name'].endswith('_id') and 
                attr['name'] != 'id' and 
                not attr['is_primary_key'] and
                attr['type'] == 'INTEGER'):
                
                # Try to find the referenced table
                referenced_table = attr['name'][:-3]  # Remove '_id'
                if any(e['name'] == referenced_table for e in schema['entities']):
                    fk_sql = f"ALTER TABLE {entity['name']} ADD COLUMN {attr['name']} INTEGER REFERENCES {referenced_table}(id);"
                    fk_statements.append(fk_sql)
    
    return fk_statements

def generate_relationship_foreign_key(relationship: Dict, schema: Dict) -> str:
    """
    Generate foreign key constraint from relationship
    """
    entity1 = relationship['entity1']
    entity2 = relationship['entity2']
    
    # Determine which entity should get the foreign key
    if relationship['type'] == 'many_to_one' or 'belongs to' in relationship['description'].lower():
        # entity2 belongs to entity1, so entity2 gets the foreign key
        fk_table = entity2
        pk_table = entity1
    else:
        # entity1 belongs to entity2, so entity1 gets the foreign key
        fk_table = entity1
        pk_table = entity2
    
    # Find primary key of referenced table
    pk_table_info = next((e for e in schema['entities'] if e['name'] == pk_table), None)
    if not pk_table_info or not pk_table_info['primary_keys']:
        return None
    
    pk_column = pk_table_info['primary_keys'][0]
    fk_column = f"{pk_table}_id"
    
    return f"ALTER TABLE {fk_table} ADD COLUMN {fk_column} INTEGER REFERENCES {pk_table}({pk_column});"

def generate_indexes(schema: Dict) -> List[str]:
    """
    Generate indexes for foreign keys and frequently searched columns
    """
    indexes = []
    
    for entity in schema['entities']:
        # Index foreign keys
        for attr in entity['attributes']:
            if (attr['name'].endswith('_id') and 
                attr['name'] != 'id' and 
                not attr['is_primary_key']):
                
                index_name = f"idx_{entity['name']}_{attr['name']}"
                indexes.append(f"CREATE INDEX {index_name} ON {entity['name']}({attr['name']});")
        
        # Index common search fields
        for attr in entity['attributes']:
            if attr['name'] in ['email', 'username', 'name', 'created', 'updated']:
                index_name = f"idx_{entity['name']}_{attr['name']}"
                indexes.append(f"CREATE INDEX {index_name} ON {entity['name']}({attr['name']});")
    
    return indexes

def save_sql_file(sql_content: str, output_path: str) -> bool:
    """
    Save SQL content to file
    """
    try:
        with open(output_path, 'w', encoding='utf-8') as file:
            file.write("-- Generated SQL schema from UML file\n")
            file.write("-- SQLite3 compatible\n\n")
            file.write(sql_content)
        
        logging.info(f"SQL file saved successfully: {output_path}")
        return True
    except Exception as e:
        logging.error(f"Error saving SQL file: {e}")
        return False

def main():
    """
    Main function to convert UML file to SQL
    """
    # Get input file from user
    puml_file = input("Enter the path to the UML file (.puml): ").strip()
    
    if not puml_file.endswith('.puml'):
        print("Please provide a .puml file")
        return
    
    # Set output file name
    base_name = os.path.splitext(os.path.basename(puml_file))[0]
    sql_file = f"{base_name}.sql"
    
    # Parse UML file
    schema = parse_puml_file(puml_file)
    if not schema:
        print("Failed to parse UML file")
        return
    
    print(f"\nParsed schema: {schema}")
    
    # Generate SQL schema
    sql_content = generate_sqlite_schema(schema)
    
    # Display generated SQL
    print("\n" + "="*50)
    print("GENERATED SQL SCHEMA:")
    print("="*50)
    print(sql_content)
    print("="*50)
    
    # Save to file
    if save_sql_file(sql_content, sql_file):
        print(f"\nSQL schema saved to: {sql_file}")
    else:
        print("\nFailed to save SQL file")

if __name__ == "__main__":
    main()