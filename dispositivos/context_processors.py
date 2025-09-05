from .models import Usuarios

def dados_do_usuario_logado(request):
    usuario_id = request.session.get('usuario_id')
    if usuario_id:
        try:
            usuario = Usuarios.objects.get(id=usuario_id)
            return {
                'nome_usuario_logado': usuario.nome,
                'funcao_usuario_logado': usuario.funcao
            }
        except Usuarios.DoesNotExist:
            request.session.flush()
    return {}