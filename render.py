from sqlalchemy import create_engine, MetaData
from sqlalchemy_schemadisplay import create_schema_graph

engine = create_engine("sqlite:///instance/barberia.db")
metadata = MetaData()
metadata.reflect(bind=engine)

graph = create_schema_graph(
    metadata=metadata,
    show_datatypes=True,
    show_indexes=True,
    rankdir="LR"
)

graph.write_png("modelo.png")

print("✅ Diagrama generado: modelo.png")
