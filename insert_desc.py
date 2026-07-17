import os

base = '/home/joao/veiculo-dados-br'
files = [
    (
        'postman/collections/Ve\u00edculo Dados BR/health/Health check.request.yaml',
        'description: Verifies that the API is up and reachable. Returns the current service status. Run this before other requests to confirm the server is healthy.'
    ),
    (
        'postman/collections/Ve\u00edculo Dados BR/api/v1/marcas/{marca_id}/Detalhe de uma marca.request.yaml',
        'description: Returns the full details of a specific brand identified by `marca_id`, including its name and any associated metadata.'
    ),
    (
        'postman/collections/Ve\u00edculo Dados BR/api/v1/modelos/{modelo_id}/Detalhe de um modelo.request.yaml',
        'description: Returns the full details of a specific vehicle model identified by `modelo_id`, including its name and the brand it belongs to.'
    ),
    (
        'postman/collections/Ve\u00edculo Dados BR/api/v1/anos/{ano_id}/Detalhe de um ano.request.yaml',
        'description: Returns the details of a specific model year identified by `ano_id`, including the year value and the model it is associated with.'
    ),
]

for rel, desc in files:
    path = os.path.join(base, rel)
    with open(path, 'rb') as f:
        content = f.read()
    le = b'\r\n' if b'\r\n' in content else b'\n'
    lines = content.split(le)
    lines.insert(1, desc.encode('utf-8'))
    with open(path, 'wb') as f:
        f.write(le.join(lines))
    print('Updated:', rel)
