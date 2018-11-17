from wsgiref.simple_server import make_server
from pyramid.config import Configurator
from pyramid.response import Response
from pyramid.view import view_config
from qval import validate

@view_config(rendered='json')
def division_view(request):
    with validate(request, a=int, b=int) as p:
        return Response({"answer": p.a // p.b}, content_type = 'application/json; charset=UTF-8')


if __name__ == '__main__':
    with Configurator() as config:
        config.add_route('divide', '/api/divide')
        config.add_view(division_view, route_name='divide')
        app = config.make_wsgi_app()
    server = make_server('0.0.0.0', 6543, app)
    server.serve_forever()
