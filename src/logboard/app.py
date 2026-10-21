from dash import Dash
from layout import create_layout
from callbacks import register_callbacks

# Inicializar a aplicação Dash
app = Dash(__name__)

# Atribuir o layout construído no outro ficheiro
app.layout = create_layout()

# Registar os callbacks lógicos
register_callbacks(app)

if __name__ == '__main__':
    app.run(debug=True, port=8051)