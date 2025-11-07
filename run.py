from app import create_app
from datetime import date

app = create_app()

if __name__ == '__main__':
    app.run(debug=False)
