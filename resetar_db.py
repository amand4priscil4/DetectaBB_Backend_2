import os
from app import create_app, db

print("Recriando banco de dados...")

app = create_app()
with app.app_context():
    # Forçar recriação das tabelas
    db.drop_all()
    db.create_all()
    print("Banco de dados recriado com sucesso!")
    
    # Verificar se as tabelas foram criadas
    from sqlalchemy import inspect
    inspector = inspect(db.engine)
    tables = inspector.get_table_names()
    print(f"Tabelas criadas: {tables}")
    
    # Verificar colunas da tabela analises_boleto
    if 'analises_boleto' in tables:
        columns = inspector.get_columns('analises_boleto')
        column_names = [col['name'] for col in columns]
        print(f"Colunas da tabela analises_boleto: {column_names}")