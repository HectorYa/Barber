from sqlalchemy import create_engine
from sqlalchemy_schemadisplay import create_schema_graph
from app import db
from flask import Flask

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///instance/barberia.db'
db.init_app(app)

# crea la engine desde la URI
engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'])

with app.app_context():
    graph = create_schema_graph(
        engine=engine,         # ahora sí
        metadata=db.metadata,
        show_datatypes=True,
        show_indexes=True,
        rankdir='LR',
    )
    graph.write_png("modelo.png")

print("✅ Diagrama generado: modelo.png")
