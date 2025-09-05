from django.shortcuts import render, redirect, get_object_or_404
from .models import Usuarios, Treinamentos, Setores, Servidores,Roteadores,Impressoras,Computadores, PlanoManuPrevent, Dispositivos,LoginUsuarioPc,PastaPublica,Hosts, EmailsNovos, EmailsAntigos, Chamados, MonitoramentoHardware
from datetime import datetime, date, timedelta
from django.contrib import messages 
from .utils import autenticar_usuario, calcular_qualidade_servico,calcular_depreciacao_computador,calcular_depreciacao_impressora,calcular_depreciacao_roteador,calcular_depreciacao_servidor,render_to_pdf,link_callback
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.hashers import make_password
from django.contrib.auth.hashers import check_password
from .forms import CadastroUsuarioForm, CadastroChamadoForm, CadastroPastaPublicaForm,CadastroLoginPcForm,CadastroHostForm,CadastroEmailNovoForm,CadastroEmailAntigoForm,ComputadorForm, ServidorForm, RoteadorForm, ImpressoraForm,PlanoManutencaoForm,TreinamentoForm,UsuarioForm
from django.utils import timezone
from django.http import JsonResponse
import json
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from django.db.models import Avg, F, Count
from django.template.loader import render_to_string
from io import BytesIO
from xhtml2pdf import pisa



def listar_usuarios_view(request):
    """ Busca e exibe todos os Usuários do sistema. """
    usuarios = Usuarios.objects.all().order_by('nome')
    contexto = {'lista_de_usuarios': usuarios}
    return render(request, 'dispositivos/listar_usuarios.html', contexto)

def criar_treinamento_com_id(titulo: str, descricao: str, setor_id: int,
                           data_ts_treinamento: datetime, data_finalizacao: datetime,
                           data_trei: date = None):
    if not Setores.objects.filter(id=setor_id).exists():
        print(f"ERRO: Não foi possível criar o treinamento. O setor com ID '{setor_id}' não existe.")
        return None
    treinamento_obj, created = Treinamentos.objects.get_or_create(
        titulo=titulo,
        data_ts_treinamento=data_ts_treinamento,
        defaults={
            'setor_id': setor_id,  
            'descricao': descricao,
            'data_finalizacao': data_finalizacao,
            'data_trei': data_trei
        }
    )

    if created:
        setor_nome = Setores.objects.get(id=setor_id).nome
        print(f"SUCESSO: Treinamento '{treinamento_obj.titulo}' para o setor '{setor_nome}' foi criado.")
    else:
        print(f"AVISO: Treinamento '{treinamento_obj.titulo}' com esta data de início já existe.")
    return treinamento_obj

def listar_treinamentos(request):
    """
    Busca os últimos treinamentos cadastrados e os exibe em uma tabela.
    Usa select_related para otimizar a performance.
    """
    # Esta única linha busca todos os treinamentos E os dados dos setores
    # relacionados em uma única consulta ao banco de dados.
    ultimos_treinamentos = Treinamentos.objects.select_related('setores').order_by('-data_ts_treinamento')

    # Não precisamos mais do laço 'for' para buscar o nome do setor.
    # O objeto 'setor' completo já vem junto com cada 'treinamento'.
    contexto = {
        'lista_de_treinamentos': ultimos_treinamentos
    }
    
    return render(request, 'dispositivos/listar_treinamentos.html', contexto)

def criar_treinamento_view(request):
    lista_de_setores = Setores.objects.all().order_by('nome')
    if request.method == 'POST':
        pass
    contexto = {
        'todos_os_setores': lista_de_setores
    }
    return render(request, 'dispositivos/criar_treinamento.html', contexto)

def inventario_view(request):
    """
    Exibe uma lista de dispositivos e fornece os dados para o modal de cadastro.
    """
    tipo_filtro = request.GET.get('tipo', 'computador')
    lista_de_dispositivos = None
    
    if tipo_filtro == 'computador':
        lista_de_dispositivos = Computadores.objects.select_related('setor').all()
    elif tipo_filtro == 'servidor':
        lista_de_dispositivos = Servidores.objects.select_related('setor').all()
    elif tipo_filtro == 'roteador':
        lista_de_dispositivos = Roteadores.objects.select_related('setor').all()
    elif tipo_filtro == 'impressora':
        lista_de_dispositivos = Impressoras.objects.select_related('setor').all()
    
    todos_os_setores = Setores.objects.all().order_by('nome')
    contexto = {
        'dispositivos': lista_de_dispositivos,
        'tipo_filtro_ativo': tipo_filtro,
        
        'todos_os_setores': todos_os_setores,
    }
    
    return render(request, 'dispositivos/inventario.html', contexto)

def cadastrar_plano_view(request):
    if request.method == 'POST':
        pass
    todos_os_dispositivos = Dispositivos.objects.select_related(
        'computadores', 'servidores', 'roteadores', 'impressoras'
    ).all()

    contexto = {
        'lista_dispositivos': todos_os_dispositivos
    }
    
    return render(request, 'dispositivos/cadastrar_plano.html', contexto)

def api_planos_manutencao(request):
    """
    Returns maintenance plans in JSON format for FullCalendar.
    Filters events based on 'start' and 'end' parameters if they are provided.
    """
    start_date_str = request.GET.get('start')
    end_date_str = request.GET.get('end')
    
    # Start with all plans
    planos = PlanoManuPrevent.objects.all()

    # --- CORRECTION IS HERE ---
    # Only apply the date filter if the parameters were actually sent
    if start_date_str and end_date_str:
        start_date = start_date_str.split('T')[0]
        end_date = end_date_str.split('T')[0]
        planos = planos.filter(data_manu__range=[start_date, end_date])
    
    # --- The rest of the function remains the same ---
    planos = planos.select_related(
        'dispositivos__computadores', 
        'dispositivos__servidores',
        'dispositivos__roteadores',
        'dispositivos__impressoras'
    )
    
    eventos = []
    for plano in planos:
        cor_evento = '#0d6efd' # Default blue
        if hasattr(plano, 'SituacaoChoices'): # Check if choices are defined
            if plano.situacao == PlanoManuPrevent.SituacaoChoices.ATRASADO:
                cor_evento = '#dc3545' # Red
            elif plano.situacao == PlanoManuPrevent.SituacaoChoices.FEITO:
                cor_evento = '#198754' # Green

        eventos.append({
            'id': plano.id,
            'title': plano.dispositivos.nome_descritivo,
            'start': plano.data_manu.strftime('%Y-%m-%d'),
            'allDay': True,
            'color': cor_evento,
        })
        
    return JsonResponse(eventos, safe=False)

def visualizacao_geral(request):
    """Exibe diferentes listas de informações com base na aba selecionada."""
    aba_ativa = request.GET.get('aba', 'logins_pc') # A aba padrão será 'logins_pc'
    
    dados = None
    if aba_ativa == 'logins_pc':
        # .select_related() otimiza a consulta buscando dados relacionados de uma vez
        dados = LoginUsuarioPc.objects.select_related('computadores__setor').all()
    elif aba_ativa == 'pastas_publicas':
        dados = PastaPublica.objects.select_related('setores').all()
    elif aba_ativa == 'hosts':
        dados = Hosts.objects.all().order_by('nome_host')
    elif aba_ativa == 'emails_novos':
        dados = EmailsNovos.objects.select_related('setores').all()
    elif aba_ativa == 'emails_antigos':
        dados = EmailsAntigos.objects.select_related('setores').all()

    contexto = {
        'dados_para_tabela': dados,
        'aba_ativa': aba_ativa
    }
    
    return render(request, 'dispositivos/visualizacao_geral.html', contexto)

def listar_chamados(request):

    ultimos_chamados = Chamados.objects.select_related(
        'setores', 
        'usuario', 
        'dispositivos__computadores', 
        'dispositivos__servidores',
        'dispositivos__roteadores',
        'dispositivos__impressoras',
        'categoria' 
    ).order_by('-data_chamado') 

    contexto = {
        'lista_de_chamados': ultimos_chamados
    }
    
    return render(request, 'dispositivos/listar_chamados.html', contexto)

def login_view(request):
    if request.method == 'POST':
        nome_usuario = request.POST.get('username')
        senha_plana = request.POST.get('password')
        usuario_autenticado = autenticar_usuario(nome_usuario, senha_plana)
        
        if usuario_autenticado:
            request.session['usuario_id'] = usuario_autenticado.id
            request.session['usuario_nome'] = usuario_autenticado.nome
            return redirect('dispositivos:dashboard')
        else:
            messages.error(request, 'Usuário ou senha inválidos.')
            return redirect('dispositivos:login')
    return render(request, 'dispositivos/login.html')

def cadastrar_usuario_view(request):
    if request.method == 'POST':
        # Se o formulário foi enviado, criamos uma instância com os dados recebidos
        form = CadastroUsuarioForm(request.POST)
        if form.is_valid():
            # Se a validação do form (incluindo a confirmação de senha) passar...
            novo_usuario = form.save(commit=False) # Pega o objeto do modelo, mas não salva ainda

            # Pega a senha do formulário e cria o hash seguro
            senha_plana = form.cleaned_data['senha']
            novo_usuario.senha_hash = make_password(senha_plana) # make_password precisa ser importado
            
            # Agora sim, salva o objeto completo no banco
            novo_usuario.save()

            messages.success(request, f"Usuário '{novo_usuario.nome}' cadastrado com sucesso!")
            return redirect('dispositivos:lista_usuarios') # Redireciona para a lista de usuários
    else:
        # Se for a primeira vez na página (GET), cria um formulário vazio
        form = CadastroUsuarioForm()

    contexto = {'form': form}
    return render(request, 'dispositivos/cadastrar_usuario.html', contexto)

def dashboard_view(request):
    """ Coleta todos os dados necessários para o dashboard principal. """

    contexto = {} # Começamos com um dicionário vazio
    try:
        # --- DADOS DO USUÁRIO LOGADO ---
        usuario_id = request.session.get('usuario_id')
        if usuario_id:
            usuario = Usuarios.objects.get(id=usuario_id)
            contexto['nome_usuario_logado'] = usuario.nome
            contexto['funcao_usuario_logado'] = usuario.funcao
        else:
            contexto['nome_usuario_logado'] = "Visitante"
            contexto['funcao_usuario_logado'] = "N/A"

        # --- DADOS PARA OS GRÁFICOS ---
        contexto['total_computadores'] = Computadores.objects.count()
        contexto['computadores_ativos'] = Computadores.objects.filter(ativo=True).count()
        contexto['dispositivos_em_manutencao'] = PlanoManuPrevent.objects.filter(situacao='NAO FEITO').count()

        # --- DADOS PARA A LISTA DE PRÓXIMAS MANUTENÇÕES ---
        contexto['proximas_manutencoes'] = PlanoManuPrevent.objects.filter(
            data_manu__gte=date.today()
        ).select_related('dispositivos').order_by('data_manu')[:4]

        # --- DADOS PARA O PAINEL DIREITO ---
        contexto['lista_computadores_painel'] = Computadores.objects.select_related('setor').all()

    except Exception as e:
        # Se qualquer consulta falhar, nós saberemos o motivo
        print(f"!!!!!!!!!! OCORREU UM ERRO NA VIEW DO DASHBOARD !!!!!!!!!!")
        print(e)

    # ==================== LINHA DE DEPURAÇÃO ====================
    print("--- CONTEXTO ENVIADO PARA O TEMPLATE DO DASHBOARD ---")
    print(contexto)
    print("-----------------------------------------------------")
    # ============================================================

    return render(request, 'dispositivos/dashboard.html', contexto)

def plano_manutencao_view(request):
    return render(request, 'dispositivos/plano_manutencao.html')

def cadastrar_chamado_view(request):
    if request.method == 'POST':
        form = CadastroChamadoForm(request.POST)
        if form.is_valid():
            chamado = form.save(commit=False) # Pega o objeto, mas não salva ainda
            
            # Podemos preencher campos que não vêm do formulário, se necessário
            chamado.data_chamado = timezone.now() # Define a data de abertura como agora
            chamado.data_dia = timezone.now().date()
            chamado.save() # Salva no banco de dados
            
            messages.success(request, f"Chamado '{chamado.titulo}' aberto com sucesso!")
            return redirect('dispositivos:lista_chamados')
    else:
        form = CadastroChamadoForm()

    contexto = {'form': form}
    return render(request, 'dispositivos/cadastrar_chamado.html', contexto)

def listar_pastas_publicas_view(request):
    """ Busca e exibe todas as Pastas Públicas cadastradas. """
    pastas = PastaPublica.objects.select_related('setores').order_by('nome_user')
    
    contexto = {
        'lista_de_pastas': pastas
    }
    return render(request, 'dispositivos/listar_pastas_publicas.html', contexto)

def cadastrar_pasta_publica_view(request):
    """ Controla o formulário de cadastro de uma nova Pasta Pública. """
    if request.method == 'POST':
        form = CadastroPastaPublicaForm(request.POST)
        if form.is_valid():
            nova_pasta = form.save(commit=False)
            nova_pasta.senha = form.cleaned_data['senha']
            nova_pasta.save()
            
            messages.success(request, f"Pasta Pública '{nova_pasta.nome_user}' cadastrada com sucesso!")
            return redirect('dispositivos:lista_pastas_publicas')
    else:
        form = CadastroPastaPublicaForm()

    contexto = {'form': form}
    return render(request, 'dispositivos/cadastrar_pasta_publica.html', contexto)

def listar_logins_pc_view(request):
    logins = LoginUsuarioPc.objects.select_related('computadores__setor').order_by('nome_user')
    
    contexto = {
        'lista_de_logins': logins
    }
    return render(request, 'dispositivos/listar_logins_pc.html', contexto)

def cadastrar_login_pc_view(request):
    if request.method == 'POST':
        form = CadastroLoginPcForm(request.POST)
        if form.is_valid():
            novo_login = form.save(commit=False)
            novo_login.senha = form.cleaned_data['senha'] 
            novo_login.save()
            
            messages.success(request, f"Login '{novo_login.nome_user}' cadastrado com sucesso!")
            return redirect('dispositivos:lista_logins_pc')
    else:
        form = CadastroLoginPcForm()

    contexto = {'form': form}
    return render(request, 'dispositivos/cadastrar_login_pc.html', contexto)

def listar_hosts_view(request):
    """ Busca e exibe todos os Hosts cadastrados. """
    hosts = Hosts.objects.all().order_by('nome_host')
    contexto = {'lista_de_hosts': hosts}
    return render(request, 'dispositivos/listar_hosts.html', contexto)

def cadastrar_host_view(request):
    """ Controla o formulário de cadastro de um novo Host. """
    if request.method == 'POST':
        form = CadastroHostForm(request.POST)
        if form.is_valid():
            form.save() 
            messages.success(request, f"Host '{form.cleaned_data['nome_host']}' cadastrado com sucesso!")
            return redirect('dispositivos:lista_hosts')
    else:
        form = CadastroHostForm()

    contexto = {'form': form}
    return render(request, 'dispositivos/cadastrar_host.html', contexto)

def listar_emails_antigos_view(request):
    """ Busca e exibe todos os Emails Antigos cadastrados. """
    emails = EmailsAntigos.objects.select_related('setores').order_by('nome_email')
    contexto = {'lista_de_emails': emails}
    return render(request, 'dispositivos/listar_emails_antigos.html', contexto)

def cadastrar_email_antigo_view(request):
    if request.method == 'POST':
        form = CadastroEmailAntigoForm(request.POST)
        if form.is_valid():
            novo_email = form.save(commit=False)
            novo_email.senha = form.cleaned_data['senha']
            novo_email.save()
            messages.success(request, f"Email '{novo_email.nome_email}' cadastrado com sucesso!")
            return redirect('dispositivos:lista_emails_antigos')
    else:
        form = CadastroEmailAntigoForm()
    contexto = {'form': form}
    return render(request, 'dispositivos/cadastrar_email_antigo.html', contexto)

def listar_emails_novos_view(request):
    """ Busca e exibe todos os Emails Novos cadastrados. """
    emails = EmailsNovos.objects.select_related('setores').order_by('nome_email')
    contexto = {'lista_de_emails': emails}
    return render(request, 'dispositivos/listar_emails_novos.html', contexto)

def cadastrar_email_novo_view(request):
    if request.method == 'POST':
        form = CadastroEmailNovoForm(request.POST)
        if form.is_valid():
            novo_email = form.save(commit=False)
            novo_email.senha = form.cleaned_data['senha']
            novo_email.save()
            messages.success(request, f"Email '{novo_email.nome_email}' cadastrado com sucesso!")
            return redirect('dispositivos:lista_emails_novos')
    else:
        form = CadastroEmailNovoForm()

    contexto = {'form': form}
    return render(request, 'dispositivos/cadastrar_email_novo.html', contexto)

def api_get_device_details(request, tipo, identificador):
    tipo = request.GET.get('tipo')
    identificador = request.GET.get('identificador')
    
    modelo = None
    if tipo == 'computador':
        modelo = Computadores
        filtro = {'endereco_mac': identificador}
    elif tipo == 'servidor':
        modelo = Servidores
        filtro = {'service_tag': identificador} 
    elif tipo == 'roteador':
        modelo = Roteadores
        filtro = {'endereco_mac': identificador}
    elif tipo == 'impressora':
        modelo = Impressoras
        filtro = {'serial': identificador}

    if modelo:
        dispositivo = modelo.objects.filter(**filtro).values().first()
        if dispositivo:
            if 'data_instalacao' in dispositivo and dispositivo['data_instalacao']:
                dispositivo['data_instalacao'] = dispositivo['data_instalacao'].strftime('%Y-%m-%d')
            return JsonResponse(dispositivo)

    return JsonResponse({'error': 'Dispositivo não encontrado'}, status=404)

def api_save_device(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        tipo = data.pop('tipo', None)
        
        modelo = None
        identificador_chave = None
        identificador_valor = None

        if tipo == 'computador':
            modelo = Computadores
            identificador_chave = 'endereco_mac'
        elif tipo == 'servidor':
            modelo = Servidores
            identificador_chave = 'service_tag'
        elif tipo == 'roteador':
            modelo = Roteadores
            identificador_chave = 'endereco_mac'
        elif tipo == 'impressora':
            modelo = Impressoras
            identificador_chave = 'serial'

        if not modelo or not identificador_chave:
            return JsonResponse({'status': 'error', 'message': 'Tipo de dispositivo inválido.'}, status=400)

        identificador_valor = data.get(identificador_chave)
        if not identificador_valor:
            return JsonResponse({'status': 'error', 'message': f'Campo identificador ({identificador_chave}) é obrigatório.'}, status=400)
        obj, created = modelo.objects.update_or_create(
            **{identificador_chave: identificador_valor},
            defaults=data
        )
        
        status_text = "criado" if created else "atualizado"
        return JsonResponse({'status': 'success', 'message': f'{tipo.capitalize()} {status_text} com sucesso!'})

    return JsonResponse({'status': 'error', 'message': 'Método inválido.'}, status=405)

def selecionar_tipo_dispositivo_view(request):
    return render(request, 'dispositivos/selecionar_tipo_dispositivo.html')

# VIEW DE FORMULÁRIO FINAL E CORRIGIDA
def dispositivo_form_view(request, tipo, identificador=None):
    ModelMap = {
        'computador': (Computadores, ComputadorForm, 'endereco_mac'),
        'servidor': (Servidores, ServidorForm, 'service_tag'),
        'roteador': (Roteadores, RoteadorForm, 'endereco_mac'),
        'impressora': (Impressoras, ImpressoraForm, 'serial'),
    }
    
    Model, FormClass, id_field = ModelMap.get(tipo)
    instance = None

    if identificador:
        instance = get_object_or_404(Model, **{id_field: identificador})

    if request.method == 'POST':
        form = FormClass(request.POST, instance=instance)
        if form.is_valid():
            form.save()
            messages.success(request, f'{tipo.capitalize()} salvo com sucesso!')
            return redirect('dispositivos:inventario_geral')
    else:
        form = FormClass(instance=instance)

    contexto = {
        'form': form,
        'tipo_dispositivo': tipo,
    }
    return render(request, 'dispositivos/dispositivo_form.html', contexto)

def plano_manutencao_form_view(request, pk=None):
    """
    Controla o formulário para criar (se pk=None) ou editar (se pk for fornecido)
    um Plano de Manutenção.
    """
    instance = None
    if pk: # Se um 'pk' (Primary Key) foi passado pela URL, estamos a editar.
        instance = get_object_or_404(PlanoManuPrevent, pk=pk)

    if request.method == 'POST':
        form = PlanoManutencaoForm(request.POST, instance=instance)
        if form.is_valid():
            form.save()
            messages.success(request, "Plano de Manutenção salvo com sucesso!")
            # Redireciona para a página do calendário após salvar
            return redirect('dispositivos:calendario_planos') 
    else:
        form = PlanoManutencaoForm(instance=instance)

    contexto = {
        'form': form,
    }
    return render(request, 'dispositivos/plano_manutencao_form.html', contexto)

def listar_planos_view(request):
    """ Busca e exibe todos os Planos de Manutenção em uma tabela. """
    planos = PlanoManuPrevent.objects.select_related(
        'dispositivos__computadores', # Otimização para buscar todos os dados
        'dispositivos__servidores',
        'dispositivos__roteadores',
        'dispositivos__impressoras'
    ).order_by('-data_manu') # Dos mais recentes para os mais antigos
    
    contexto = {'lista_de_planos': planos}
    return render(request, 'dispositivos/listar_planos.html', contexto)

from django.utils import timezone
from django.shortcuts import render, redirect, get_object_or_404
from .forms import TreinamentoForm
from .models import Treinamentos
from django.contrib import messages

def treinamento_form_view(request, pk=None):
    instance = None
    if pk:
        instance = get_object_or_404(Treinamentos, pk=pk)

    if request.method == 'POST':
        form = TreinamentoForm(request.POST, instance=instance)
        if form.is_valid():
            treinamento = form.save(commit=False)
            
            # --- A CORREÇÃO ESTÁ AQUI ---
            # Pegamos as datas/horas que vieram do formulário
            dt_inicio = form.cleaned_data.get('data_ts_treinamento')
            dt_finalizacao = form.cleaned_data.get('data_finalizacao')
            
            # Verificamos se a data/hora já é 'consciente'.
            # Só chamamos make_aware se ela for 'ingénua'.
            if dt_inicio and timezone.is_naive(dt_inicio):
                treinamento.data_ts_treinamento = timezone.make_aware(dt_inicio)
            
            if dt_finalizacao and timezone.is_naive(dt_finalizacao):
                treinamento.data_finalizacao = timezone.make_aware(dt_finalizacao)
            # --------------------------------

            treinamento.save()
            
            messages.success(request, "Treinamento salvo com sucesso!")
            return redirect('dispositivos:lista_treinamentos')
        else:
            print(form.errors.as_json())
    else:
        form = TreinamentoForm(instance=instance)

    contexto = {'form': form}
    return render(request, 'dispositivos/treinamento_form.html', contexto)

def chamado_form_view(request, pk=None):
    """ Controla o formulário para criar ou editar um Chamado. """
    instance = None
    if pk:
        instance = get_object_or_404(Chamados, pk=pk)

    if request.method == 'POST':
        form = CadastroChamadoForm(request.POST, instance=instance)
        if form.is_valid():
            chamado = form.save(commit=False)
            
            # Pegamos a data de início para preencher a 'data_dia'
            dt_inicio = form.cleaned_data.get('data_chamado')
            if dt_inicio:
                chamado.data_dia = dt_inicio.date()

            # Lida com a conversão de fuso horário para os campos datetime
            dt_finalizacao = form.cleaned_data.get('data_finalizacao')

            if dt_inicio and timezone.is_naive(dt_inicio):
                chamado.data_chamado = timezone.make_aware(dt_inicio)
            
            if dt_finalizacao and timezone.is_naive(dt_finalizacao):
                chamado.data_finalizacao = timezone.make_aware(dt_finalizacao)

            chamado.save()
            messages.success(request, "Chamado salvo com sucesso!")
            return redirect('dispositivos:lista_chamados')
    else:
        form = CadastroChamadoForm(instance=instance)

    contexto = {'form': form}
    return render(request, 'dispositivos/chamado_form.html', contexto)

def login_pc_form_view(request, pk=None):
    """ Controla o formulário para criar ou editar um Login de PC. """
    instance = None
    if pk:
        instance = get_object_or_404(LoginUsuarioPc, pk=pk)

    if request.method == 'POST':
        form = CadastroLoginPcForm(request.POST, instance=instance)
        if form.is_valid():
            form.save() # Salva diretamente, pois a senha é em texto puro
            messages.success(request, f"Login de PC '{form.cleaned_data['nome_user']}' salvo com sucesso!")
            return redirect('dispositivos:lista_logins_pc')
    else:
        form = CadastroLoginPcForm(instance=instance)

    contexto = {'form': form}
    return render(request, 'dispositivos/login_pc_form.html', contexto)

def pasta_publica_form_view(request, pk=None):
    """ Controla o formulário para criar ou editar um registro de Pasta Pública. """
    instance = None
    if pk:
        instance = get_object_or_404(PastaPublica, pk=pk)

    if request.method == 'POST':
        form = CadastroPastaPublicaForm(request.POST, instance=instance)
        if form.is_valid():
            form.save()
            messages.success(request, f"Pasta Pública '{form.cleaned_data['nome_user']}' salva com sucesso!")
            return redirect('dispositivos:lista_pastas_publicas')
    else:
        form = CadastroPastaPublicaForm(instance=instance)

    contexto = {'form': form}
    return render(request, 'dispositivos/cadastrar_pasta_publica.html', contexto)

def host_form_view(request, pk=None):
    """ Controla o formulário para criar ou editar um Host. """
    instance = None
    if pk:
        instance = get_object_or_404(Hosts, pk=pk)

    if request.method == 'POST':
        form = CadastroHostForm(request.POST, instance=instance)
        if form.is_valid():
            form.save()
            nome = form.cleaned_data['nome_host']
            messages.success(request, f"Host '{nome}' salvo com sucesso!")
            return redirect('dispositivos:lista_hosts')
    else:
        form = CadastroHostForm(instance=instance)

    contexto = {'form': form}
    return render(request, 'dispositivos/host_form.html', contexto)

def email_novo_form_view(request, pk=None):
    """ Controla o formulário para criar ou editar um Email Novo. """
    instance = None
    if pk:
        instance = get_object_or_404(EmailsNovos, pk=pk)

    if request.method == 'POST':
        form = CadastroEmailNovoForm(request.POST, instance=instance)
        if form.is_valid():
            form.save()
            nome = form.cleaned_data['nome_email']
            messages.success(request, f"Email '{nome}' salvo com sucesso!")
            return redirect('dispositivos:lista_emails_novos')
    else:
        form = CadastroEmailNovoForm(instance=instance)

    contexto = {'form': form}
    return render(request, 'dispositivos/cadastrar_email_novo.html', contexto)

def email_antigo_form_view(request, pk=None):
    """ Controla o formulário para criar ou editar um Email Antigo. """
    instance = None
    if pk:
        instance = get_object_or_404(EmailsAntigos, pk=pk)

    if request.method == 'POST':
        form = CadastroEmailAntigoForm(request.POST, instance=instance)
        if form.is_valid():
            form.save()
            nome = form.cleaned_data['nome_email']
            messages.success(request, f"Email antigo '{nome}' salvo com sucesso!")
            return redirect('dispositivos:lista_emails_antigos')
    else:
        form = CadastroEmailAntigoForm(instance=instance)

    contexto = {'form': form}
    return render(request, 'dispositivos/cadastrar_email_antigo.html', contexto)

def usuario_form_view(request, pk=None):
    """ Controla o formulário para criar ou editar um Usuário. """
    instance = None
    if pk:
        instance = get_object_or_404(Usuarios, pk=pk)

    if request.method == 'POST':
        form = UsuarioForm(request.POST, instance=instance)
        if form.is_valid():
            usuario = form.save(commit=False)
            
            # LÓGICA DE SENHA SEGURA
            nova_senha = form.cleaned_data.get('nova_senha')
            if nova_senha: # Se o campo 'nova_senha' foi preenchido...
                usuario.senha_hash = make_password(nova_senha) # ...gera o hash seguro
            
            usuario.save()
            messages.success(request, f"Usuário '{usuario.nome}' salvo com sucesso!")
            return redirect('dispositivos:lista_usuarios')
    else:
        form = UsuarioForm(instance=instance)

    contexto = {'form': form}
    return render(request, 'dispositivos/usuario_form.html', contexto)

def api_relatorio_view(request):
    """
    Gera o HTML para um relatório específico (gráfico ou tabela)
    e o retorna como JSON.
    """
    report_name = request.GET.get('name')
    report_html = "<div class='alert alert-danger'>Relatório não encontrado.</div>"

    # ====================================================================
    #           ÁRVORE DE DECISÃO PARA GERAR O RELATÓRIO CORRETO
    # ====================================================================

    if report_name == 'dispositivos_por_setor':
        queryset = Computadores.objects.values('setor__nome')
        if queryset.exists():
            df = pd.DataFrame(list(queryset))
            df_contagem = df['setor__nome'].value_counts().reset_index()
            df_contagem.columns = ['setor', 'quantidade']
            fig = px.bar(df_contagem, x='setor', y='quantidade', title='Nº de Computadores por Setor')
            report_html = fig.to_html(full_html=False, include_plotlyjs='cdn')

    elif report_name == 'chamados_por_setor':
        # Esta consulta agrupa por nome do setor e conta os chamados em cada grupo
        queryset = Chamados.objects.values('setores__nome').annotate(
            total= Count('id')
        ).order_by('-total') # Ordena do maior para o menor

        if queryset.exists():
            # Renomeamos as colunas para nomes mais amigáveis
            df = pd.DataFrame(list(queryset)).rename(columns={
                'setores__nome': 'Setor',
                'total': 'Nº de Chamados'
            })

            # Geramos o gráfico de barras com Plotly
            fig = px.bar(
                df, 
                x='Setor', 
                y='Nº de Chamados', 
                title='Demandas de Chamados por Setor',
                text_auto=True # Mostra o número em cima de cada barra
            )
            fig.update_layout(title_x=0.5) # Centraliza o título
            report_html = fig.to_html(full_html=False, include_plotlyjs='cdn')
        else:
            report_html = "<div class='alert alert-warning'>Não há dados de chamados para exibir o relatório.</div>"
    # Adicione outros 'elif report_name == ...' para cada novo relatório que você criar

    return JsonResponse({'html': report_html})

def relatorios_view(request):
    """
    Prepara os dados e gera os gráficos para a VISÃO GERAL da página de relatórios.
    """
    contexto = {}

    # --- GRÁFICO GERAL 1: DISPOSITIVOS POR TIPO ---
    contagens = {
        'Computadores': Computadores.objects.count(),
        'Servidores': Servidores.objects.count(),
        'Roteadores': Roteadores.objects.count(),
        'Impressoras': Impressoras.objects.count(),
    }
    df_tipos = pd.DataFrame(list(contagens.items()), columns=['Tipo', 'Quantidade'])
    
    fig_tipos = px.pie(df_tipos, names='Tipo', values='Quantidade', 
                       title='Distribuição de Dispositivos por Tipo', hole=.4)
    fig_tipos.update_layout(title_x=0.5)
    contexto['graph_geral_dispositivos'] = fig_tipos.to_html(full_html=False, include_plotlyjs='cdn')

    # --- GRÁFICO GERAL 2: CHAMADOS POR STATUS ---
    qs_status = Chamados.objects.values('situacao').annotate(total=Count('id'))
    if qs_status.exists():
        df_status = pd.DataFrame(list(qs_status)).rename(columns={'situacao': 'Status', 'total': 'Quantidade'})
        fig_status = px.bar(df_status, x='Status', y='Quantidade', 
                            title='Contagem de Chamados por Status', text_auto=True)
        fig_status.update_layout(title_x=0.5)
        contexto['graph_geral_chamados'] = fig_status.to_html(full_html=False, include_plotlyjs=False)
        
    return render(request, 'dispositivos/relatorios.html', contexto)

def relatorios_chamados_view(request):
    """
    Prepara todos os dados e gráficos para o dashboard de Chamados.
    """
    contexto = {}
    
    # --- GRÁFICO 1: CHAMADOS POR SETOR (sem alterações) ---
    qs_setor = Chamados.objects.values('setores__nome').annotate(total=Count('id')).order_by('-total')
    if qs_setor.exists():
        df_setor = pd.DataFrame(list(qs_setor)).rename(columns={'setores__nome': 'Setor', 'total': 'Nº de Chamados'})
        fig_setor = px.bar(df_setor, x='Setor', y='Nº de Chamados', title='Demandas de Chamados por Setor', text_auto=True)
        fig_setor.update_layout(title_x=0.5)
        contexto['graph_chamados_por_setor'] = fig_setor.to_html(full_html=False, include_plotlyjs='cdn')

    # --- GRÁFICO 2: CHAMADOS POR STATUS (sem alterações) ---
    qs_status = Chamados.objects.values('situacao').annotate(total=Count('id')).order_by('-total')
    if qs_status.exists():
        df_status = pd.DataFrame(list(qs_status)).rename(columns={'situacao': 'Status', 'total': 'Quantidade'})
        fig_status = px.pie(df_status, names='Status', values='Quantidade', title='Chamados por Status', hole=.4)
        fig_status.update_layout(title_x=0.5)
        contexto['graph_chamados_por_status'] = fig_status.to_html(full_html=False, include_plotlyjs=False)

    # --- NOVO GRÁFICO 3: TOP 10 DISPOSITIVOS COM CHAMADOS ---
    top_dispositivos_qs = Chamados.objects.values('dispositivos_id').annotate(
        total_chamados=Count('dispositivos_id')
    ).order_by('-total_chamados')[:10]

    if top_dispositivos_qs.exists():
        dados_para_grafico = []
        for item in top_dispositivos_qs:
            # Precisamos buscar o objeto para pegar o nome descritivo
            dispositivo = Dispositivos.objects.get(id=item['dispositivos_id'])
            dados_para_grafico.append({
                'Dispositivo': dispositivo.nome_descritivo,
                'Nº de Chamados': item['total_chamados']
            })
        
        df_top = pd.DataFrame(dados_para_grafico)
        fig_top = px.bar(
            df_top, 
            x='Nº de Chamados', # Invertemos x e y para um gráfico horizontal
            y='Dispositivo',
            orientation='h', # Define o gráfico como horizontal
            title='Top 10 Dispositivos com Mais Chamados',
            text_auto=True
        )
        # Ordenamos o eixo Y para que o dispositivo com mais chamados apareça no topo
        fig_top.update_yaxes(categoryorder="total ascending")
        fig_top.update_layout(title_x=0.5)
        contexto['graph_top_dispositivos'] = fig_top.to_html(full_html=False, include_plotlyjs=False)
    
    hoje = timezone.now().date()
    # Filtramos os chamados que foram finalizados no ano e mês atuais
    tempo_medio_timedelta = Chamados.objects.filter(
        data_finalizacao__year=hoje.year,
        data_finalizacao__month=hoje.month
    ).aggregate(
        # Calculamos a média da diferença entre a data final e a inicial
        tempo_medio=Avg(F('data_finalizacao') - F('data_chamado'))
    )['tempo_medio']

    # Formatamos o resultado (que é um objeto timedelta) para um texto legível
    tempo_medio_formatado = "N/A"
    if tempo_medio_timedelta:
        total_seconds = int(tempo_medio_timedelta.total_seconds())
        dias = total_seconds // 86400
        horas = (total_seconds % 86400) // 3600
        minutos = (total_seconds % 3600) // 60
        if dias > 0:
            tempo_medio_formatado = f"{dias}d {horas}h"
        else:
            tempo_medio_formatado = f"{horas}h {minutos}m"
    
    contexto['tempo_medio_chamados'] = tempo_medio_formatado


    contexto['contagem_manutencoes_mes'] = Chamados.objects.filter(
        data_chamado__year=hoje.year,
        data_chamado__month=hoje.month,
        categoria__nome__iexact='Manutenção'
    ).count()

    # Contagem de chamados da categoria 'Ajuste'
    contexto['contagem_ajustes_mes'] = Chamados.objects.filter(
        data_chamado__year=hoje.year,
        data_chamado__month=hoje.month,
        categoria__nome__iexact='Ajuste'
    ).count()

    score_qualidade = calcular_qualidade_servico()
    
    fig_qualidade = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = score_qualidade,
        title = {'text': "Qualidade de Serviço (QoS)"},
        gauge = {
            'axis': {'range': [None, 100]},
            'steps': [
                {'range': [0, 50], 'color': "#ea4335"}, # Vermelho
                {'range': [50, 80], 'color': "#fbbc05"}, # Amarelo
                {'range': [80, 100], 'color': "#34a853"}], # Verde
            'threshold': {'line': {'color': "black", 'width': 4}, 'thickness': 0.75, 'value': score_qualidade}
        }))
    fig_qualidade.update_layout(height=300, title_x=0.5)
    contexto['graph_qualidade_servico'] = fig_qualidade.to_html(full_html=False, include_plotlyjs=False)
    
    return render(request, 'dispositivos/relatorio_chamados.html', contexto)

def relatorios_computadores_view(request):
    """
    Prepara TODOS os dados para o dashboard de Computadores:
    - Contagem total para o card.
    - Gráfico de pizza de ativos/inativos.
    - Gráfico de barras por setor.
    - Tabela de análise de depreciação.
    """
    contexto = {}
    
    # --- DADOS PARA A TABELA DE DEPRECIAÇÃO E CARD DE TOTAL ---
    # Usamos prefetch_related para otimizar a busca de chamados
    todos_computadores = Computadores.objects.select_related('setor').prefetch_related(
        'dispositivos__chamados_set__categoria'
    )
    
    dados_depreciacao = []
    for comp in todos_computadores:
        score = calcular_depreciacao_computador(comp)
        dados_depreciacao.append({
            'computador': comp,
            'score': score
        })
    dados_depreciacao.sort(key=lambda x: x['score'])
    
    contexto['dados_depreciacao'] = dados_depreciacao
    contexto['total_computadores'] = todos_computadores.count()



    total_computadores = Computadores.objects.count()


    # --- LÓGICA PARA O GRÁFICO DE PIZZA (ATIVOS VS INATIVOS) ---
    todos_computadores = Computadores.objects.all()
    total_computadores = todos_computadores.count()
    contexto['total_computadores'] = total_computadores

    if total_computadores > 0:
        ativos = todos_computadores.filter(ativo=True).count()
        inativos = total_computadores - ativos
        
        df_status = pd.DataFrame({
            'Status': ['Ativos', 'Inativos'], 
            'Quantidade': [ativos, inativos]
        })
        fig_status = px.pie(
            df_status, 
            names='Status', 
            values='Quantidade', 
            title='Status dos Computadores',
            color_discrete_map={'Ativos':'#36A2EB', 'Inativos':'#FF6384'}
        )
        fig_status.update_traces(
            textposition='inside', 
            textinfo='label+percent', 
            insidetextorientation='radial',
            textfont_size=16
        )
        fig_status.update_layout(
            title_x=0.5,
            showlegend=True 
        )
        
        contexto['plotly_graph_ativos'] = fig_status.to_html(full_html=False, include_plotlyjs='cdn')


    # --- LÓGICA PARA O GRÁFICO DE BARRAS (COMPUTADORES POR SETOR) ---
    qs_setor = todos_computadores.values('setor__nome').annotate(
        quantidade=Count('id')
    ).order_by('-quantidade')

    if qs_setor.exists():
        df_setor = pd.DataFrame(list(qs_setor)).rename(columns={'setor__nome': 'Setor'})
        fig_setor = px.bar(df_setor, x='Setor', y='quantidade', title='Nº de Computadores por Setor', text_auto=True)
        fig_setor.update_layout(title_x=0.5)
        contexto['plotly_graph_por_setor'] = fig_setor.to_html(full_html=False, include_plotlyjs=False) # JS já incluído pelo primeiro gráfico

    return render(request, 'dispositivos/relatorio_computadores.html', contexto)

def relatorios_impressoras_view(request):
    """
    Prepara os dados e gráficos para o dashboard de Impressoras.
    """
    contexto = {}
    
    # --- DADO PARA O CARD: Quantidade total ---
    total_impressoras = Impressoras.objects.count()

    impressoras = Impressoras.objects.select_related('setor').prefetch_related(
        'dispositivos__chamados_set__categoria'
    )
    
    dados_depreciacao = []
    for imp in impressoras:
        score = calcular_depreciacao_impressora(imp)
        dados_depreciacao.append({
            'impressora': imp,
            'score': score
        })
    
    # Ordena a lista da pior para a melhor
    dados_depreciacao.sort(key=lambda x: x['score'])

    contexto = {
        'dados_depreciacao': dados_depreciacao,
    }

    contexto['total_impressoras'] = total_impressoras

    # --- GRÁFICO 1: IMPRESSORAS POR TIPO DE CONEXÃO ---
    if total_impressoras > 0:
        qs_conexao = Impressoras.objects.values('tipo_conexao').annotate(
            quantidade=Count('id')
        ).order_by('-quantidade')
        
        df_conexao = pd.DataFrame(list(qs_conexao)).rename(columns={'tipo_conexao': 'Tipo de Conexão'})
        
        fig_conexao = px.pie(
            df_conexao, 
            names='Tipo de Conexão', 
            values='quantidade', 
            title='Distribuição por Tipo de Conexão',
            hole=.4
        )
        fig_conexao.update_layout(title_x=0.5)
        contexto['plotly_graph_conexao'] = fig_conexao.to_html(full_html=False, include_plotlyjs='cdn')

    # --- GRÁFICO 2: IMPRESSORAS POR SETOR ---
    qs_setor = Impressoras.objects.values('setor__nome').annotate(
        quantidade=Count('id')
    ).order_by('-quantidade')

    if qs_setor.exists():
        df_setor = pd.DataFrame(list(qs_setor)).rename(columns={'setor__nome': 'Setor'})
        
        fig_setor = px.bar(
            df_setor,
            x='Setor',
            y='quantidade',
            title='Quantidade de Impressoras por Setor',
            labels={'quantidade': 'Nº de Impressoras'},
            text_auto=True
        )
        fig_setor.update_layout(title_x=0.5)
        contexto['plotly_graph_por_setor'] = fig_setor.to_html(full_html=False, include_plotlyjs=False)

    return render(request, 'dispositivos/relatorio_impressoras.html', contexto)

def relatorios_manutencoes_view(request):
    """
    Prepara os dados e gráficos para o dashboard de Planos de Manutenção.
    """
    contexto = {}
    
    # --- GRÁFICO 1: MANUTENÇÕES POR STATUS (FEITO, NAO FEITO, ATRASADO) ---
    qs_status = PlanoManuPrevent.objects.values('situacao').annotate(
        quantidade=Count('id')
    ).order_by('-quantidade')

    if qs_status.exists():
        df_status = pd.DataFrame(list(qs_status)).rename(columns={'situacao': 'Status'})
        
        fig_status = px.pie(
            df_status, 
            names='Status', 
            values='quantidade', 
            title='Status dos Planos de Manutenção',
            hole=.4,
            color_discrete_map={'FEITO':'#198754', 'NAO FEITO':'#0d6efd', 'ATRASADO':'#dc3545'}
        )
        fig_status.update_layout(title_x=0.5)
        contexto['plotly_graph_status'] = fig_status.to_html(full_html=False, include_plotlyjs='cdn')

    # --- GRÁFICO 2: MANUTENÇÕES POR TIPO DE DISPOSITIVO ---
    # Esta é uma consulta mais complexa que verifica o tipo de cada dispositivo relacionado
    dispositivos_com_plano = PlanoManuPrevent.objects.select_related('dispositivos').all()
    
    contagem_tipos = {'Computadores': 0, 'Servidores': 0, 'Roteadores': 0, 'Impressoras': 0, 'Outros': 0}
    for plano in dispositivos_com_plano:
        if hasattr(plano.dispositivos, 'computadores') and plano.dispositivos.computadores:
            contagem_tipos['Computadores'] += 1
        elif hasattr(plano.dispositivos, 'servidores') and plano.dispositivos.servidores:
            contagem_tipos['Servidores'] += 1
        elif hasattr(plano.dispositivos, 'roteadores') and plano.dispositivos.roteadores:
            contagem_tipos['Roteadores'] += 1
        elif hasattr(plano.dispositivos, 'impressoras') and plano.dispositivos.impressoras:
            contagem_tipos['Impressoras'] += 1
        else:
            contagem_tipos['Outros'] += 1
    
    if sum(contagem_tipos.values()) > 0:
        df_tipos = pd.DataFrame(list(contagem_tipos.items()), columns=['Tipo de Dispositivo', 'Quantidade'])
        fig_tipos = px.bar(
            df_tipos,
            x='Tipo de Dispositivo',
            y='Quantidade',
            title='Nº de Manutenções por Tipo de Dispositivo',
            text_auto=True
        )
        fig_tipos.update_layout(title_x=0.5)
        contexto['plotly_graph_tipos'] = fig_tipos.to_html(full_html=False, include_plotlyjs=False)
    
    return render(request, 'dispositivos/relatorio_manutencoes.html', contexto)

def relatorios_roteadores_view(request):
    """
    Prepara os dados e gráficos para o dashboard de Roteadores.
    """
    contexto = {}
    
    # --- GRÁFICO: ROTEADORES POR SETOR ---
    qs_setor = Roteadores.objects.values('setor__nome').annotate(
        quantidade=Count('id')
    ).order_by('-quantidade')
    
    if qs_setor.exists():
        df_setor = pd.DataFrame(list(qs_setor)).rename(columns={'setor__nome': 'Setor'})
        fig_setor = px.bar(
            df_setor, x='Setor', y='quantidade', 
            title='Quantidade de Roteadores por Setor', text_auto=True
        )
        fig_setor.update_layout(title_x=0.5)
        contexto['plotly_graph_por_setor'] = fig_setor.to_html(full_html=False, include_plotlyjs='cdn')

    # --- TABELA DE ANÁLISE DE DEPRECIAÇÃO ---
    roteadores = Roteadores.objects.select_related('setor').prefetch_related(
        'dispositivos__chamados_set__categoria'
    )
    
    dados_depreciacao = []
    for rot in roteadores:
        score = calcular_depreciacao_roteador(rot)
        dados_depreciacao.append({
            'roteador': rot,
            'score': score
        })
    dados_depreciacao.sort(key=lambda x: x['score'])
    
    contexto['dados_depreciacao'] = dados_depreciacao
    
    return render(request, 'dispositivos/relatorio_roteadores.html', contexto)

def relatorios_servidores_view(request):
    """
    Prepara os dados e gráficos para o dashboard de Servidores.
    """
    contexto = {}
    
    # --- GRÁFICO: SERVIDORES POR MARCA ---
    qs_marca = Servidores.objects.values('marca').annotate(
        quantidade=Count('id')
    ).order_by('-quantidade')
    
    if qs_marca.exists():
        df_marca = pd.DataFrame(list(qs_marca))
        fig_marca = px.bar(
            df_marca, x='marca', y='quantidade', 
            title='Quantidade de Servidores por Marca', text_auto=True
        )
        fig_marca.update_layout(title_x=0.5)
        contexto['plotly_graph_por_marca'] = fig_marca.to_html(full_html=False, include_plotlyjs='cdn')

    # --- TABELA DE ANÁLISE DE DEPRECIAÇÃO ---
    servidores = Servidores.objects.select_related('setor').prefetch_related(
        'dispositivos__chamados_set__categoria'
    )
    
    dados_depreciacao = []
    for srv in servidores:
        score = calcular_depreciacao_servidor(srv)
        dados_depreciacao.append({
            'servidor': srv,
            'score': score
        })
    dados_depreciacao.sort(key=lambda x: x['score'])
    
    contexto['dados_depreciacao'] = dados_depreciacao
    
    return render(request, 'dispositivos/relatorio_servidores.html', contexto)

def relatorios_treinamentos_view(request):
    """
    Prepara os dados e gráficos para o dashboard de Treinamentos.
    """
    contexto = {}
    
    # --- GRÁFICO: QUANTIDADE DE TREINAMENTOS POR SETOR ---
    qs_setor = Treinamentos.objects.values('setores__nome').annotate(
        quantidade=Count('id')
    ).order_by('-quantidade')
    
    if qs_setor.exists():
        df_setor = pd.DataFrame(list(qs_setor)).rename(columns={'setores__nome': 'Setor'})
        fig_setor = px.bar(
            df_setor, 
            x='Setor', 
            y='quantidade', 
            title='Nº de Treinamentos por Setor', 
            text_auto=True,
            labels={'quantidade': 'Nº de Treinamentos'}
        )
        fig_setor.update_layout(title_x=0.5)
        contexto['plotly_graph_por_setor'] = fig_setor.to_html(full_html=False, include_plotlyjs='cdn')

    # --- CARD: TEMPO MÉDIO DE DURAÇÃO DOS TREINAMENTOS ---
    # Usamos F() para calcular a diferença entre as datas diretamente no banco
    media_timedelta = Treinamentos.objects.aggregate(
        media_duracao=Avg(F('data_finalizacao') - F('data_ts_treinamento'))
    )['media_duracao']

    media_duracao_formatada = "N/A"
    if media_timedelta:
        total_seconds = int(media_timedelta.total_seconds())
        horas = total_seconds // 3600
        minutos = (total_seconds % 3600) // 60
        media_duracao_formatada = f"{horas}h {minutos}m"
        
    contexto['media_duracao_treinamentos'] = media_duracao_formatada
    
    return render(request, 'dispositivos/relatorio_treinamentos.html', contexto)

def dashboard_view(request):
    """
    Coleta dados e gera gráficos Plotly compactos para o dashboard.
    """
    contexto = {}
    
    # A lógica para buscar nome e função do usuário continua a mesma
    contexto['nome_usuario_logado'] = request.session.get('usuario_nome', 'Usuário')
    # ... (você pode adicionar a busca completa do usuário aqui se precisar)

    # --- LÓGICA CORRIGIDA: Contagem de TODOS os Dispositivos Ativos ---
    
    # 1. Contamos o total de cada tipo de dispositivo
    total_computadores = Computadores.objects.count()
    total_servidores = Servidores.objects.count()
    total_roteadores = Roteadores.objects.count()
    total_impressoras = Impressoras.objects.count()
    
    # 2. Somamos para ter o total geral
    total_dispositivos = total_computadores + total_servidores + total_roteadores + total_impressoras
    
    # 3. Contamos apenas os dispositivos ATIVOS de cada categoria
    ativos_computadores = Computadores.objects.filter(ativo=True).count()
    ativos_servidores = Servidores.objects.filter(ativo=True).count()
    # Assumimos que roteadores e impressoras estão sempre "ativos" se cadastrados
    ativos_roteadores = total_roteadores
    ativos_impressoras = total_impressoras
    
    total_ativos = ativos_computadores + ativos_servidores + ativos_roteadores + ativos_impressoras
    
    # 4. Calculamos os inativos pela diferença
    total_inativos = total_dispositivos - total_ativos
    
    if total_dispositivos > 0:
        df_status = pd.DataFrame({'Status': ['Ativos', 'Inativos'], 'Quantidade': [total_ativos, total_inativos]})
        fig_ativos = px.pie(df_status, names='Status', values='Quantidade', hole=0.6,
                            color_discrete_map={'Ativos':"#33D6FF", 'Inativos':'#dc3545'})
        
        fig_ativos.update_layout(
            title_text='Dispositivos Ativos',
            title_x=0.3,
            height=170,
            width = 350,
            margin=dict(l=10, r=40, t=40, b=20),
            font=dict(size=12),
            annotations=[dict(text=str(total_ativos), x=0.5, y=0.5, font_size=40, showarrow=False, font_color='#198754')],
            legend=dict(
                orientation="v", # Vertical
                yanchor="middle",  # Âncora no meio da legenda
                y=0.5,             # Posição vertical no centro do gráfico
                xanchor="right",    # Âncora na esquerda da legenda
                x=-0.1             # Posição X à esquerda do gráfico
            )
        )
        contexto['plotly_graph_ativos'] = fig_ativos.to_html(full_html=False, include_plotlyjs='cdn')


    dispositivos_em_manutencao = PlanoManuPrevent.objects.filter(situacao='NAO FEITO').count()
    dispositivos_ok = total_ativos - dispositivos_em_manutencao
    
    if total_ativos > 0:
        df_manutencao = pd.DataFrame({'Status': ['Em Manutenção', 'Operando OK'], 'Quantidade': [dispositivos_em_manutencao, dispositivos_ok]})
        fig_manutencao = px.pie(df_manutencao, names='Status', values='Quantidade', hole=0.6,
                                color_discrete_map={'Em Manutenção':'#ffc107', 'Operando OK':'#0dcaf0'})
        fig_manutencao.update_layout(
            title_text='Dispositivos em Manutenção', title_x=0.5, height=170,
            width = 350,
            margin=dict(l=10, r=60, t=40, b=20), font=dict(size=12),
            annotations=[dict(text=str(dispositivos_em_manutencao), x=0.5, y=0.5, font_size=40, showarrow=False, font_color='#ffc107')],
            legend=dict(
                orientation="v", # Vertical
                yanchor="middle",  # Âncora no meio da legenda
                y=0.5,             # Posição vertical no centro do gráfico
                xanchor="right",    # Âncora na esquerda da legenda
                x=-0.1             # Posição X à esquerda do gráfico
            )
        
        )
        contexto['plotly_graph_manutencao'] = fig_manutencao.to_html(full_html=False, include_plotlyjs=False)

    contexto['proximas_manutencoes'] = PlanoManuPrevent.objects.select_related(
        'dispositivos'
    ).filter(data_manu__gte=date.today()).order_by('data_manu')[:4]
    
    # --- DADOS PARA O PAINEL DIREITO (MONITORAMENTO) ---
    lista_computadores = Computadores.objects.select_related('setor').all()
    lista_computadores_com_status = []
    for comp in lista_computadores:
        ultimo_status = MonitoramentoHardware.objects.filter(computadores=comp).order_by('-timestamp').first()
        lista_computadores_com_status.append({'computador': comp, 'status': ultimo_status})
    contexto['lista_computadores_painel'] = lista_computadores_com_status
    
    return render(request, 'dispositivos/dashboard.html', contexto)
    
@csrf_exempt 
def api_receive_monitoring(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            mac_address = data.get('mac_address')
            
            if not mac_address:
                return JsonResponse({'error': 'MAC address em falta.'}, status=400)

            # Encontra o computador no inventário com base no MAC address
            computador = Computadores.objects.get(endereco_mac=mac_address)
            
            # Cria um novo registro de monitoramento
            MonitoramentoHardware.objects.create(
                computadores=computador,
                cpu_percent=data.get('cpu_percent'),
                memory_percent=data.get('memory_percent'),
                disk_percent=data.get('disk_percent'),
            )
            return JsonResponse({'status': 'success'}, status=201)

        except Computadores.DoesNotExist:
            return JsonResponse({'error': 'Computador com este MAC não está cadastrado no inventário.'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    
    return JsonResponse({'error': 'Apenas o método POST é permitido.'}, status=405)

def api_listar_computadores_view(request):
    """
    Retorna uma lista de todos os computadores (ID e Nome) em formato JSON.
    """
    computadores = Computadores.objects.all().order_by('nome')
    # Usamos .values() para transformar os objetos em dicionários
    dados = list(computadores.values('id', 'nome', 'endereco_mac'))
    return JsonResponse(dados, safe=False)

def api_monitoring_history_view(request, computador_id):
    """ Fornece o histórico recente de monitoramento para um computador. """
    historico = MonitoramentoHardware.objects.filter(
        computadores_id=computador_id
    ).order_by('-timestamp')[:30] # Pega os últimos 30 registros
    
    historico = reversed(list(historico)) # Inverte para o gráfico ficar na ordem correta

    dados = {
        'timestamps': [h.timestamp.strftime('%H:%M:%S') for h in historico],
        'cpu_data': [h.cpu_percent for h in historico],
        'memory_data': [h.memory_percent for h in historico],
        'disk_data': [h.disk_percent for h in historico],
    }
    return JsonResponse(dados)

def exportacao_relatorios_view(request):
    """ Apenas renderiza a página de exportação com os filtros. """
    contexto = {
        'setores': Setores.objects.all(),
        'versoes_so': Computadores.objects.values_list('versao_so', flat=True).distinct(),
    }
    return render(request, 'dispositivos/exportacao_relatorios.html', contexto)

def api_gerar_preview_relatorio(request):
    """
    Recebe os filtros, busca os dados e renderiza um template HTML
    apenas com o conteúdo do relatório para a pré-visualização.
    """
    categoria = request.GET.get('categoria_principal')
    contexto = {} # Começamos com um contexto vazio
    template_name = 'dispositivos/partials/relatorios/_preview_vazio.html'

    if categoria == 'computadores':
        # --- Lógica de Filtro para Computadores ---
        queryset = Computadores.objects.select_related('setor').all()
        
        # Filtros de data
        data_inicio = request.GET.get('data_instalacao_inicio')
        data_fim = request.GET.get('data_instalacao_fim')
        if data_inicio:
            queryset = queryset.filter(data_instalacao__gte=data_inicio)
        if data_fim:
            queryset = queryset.filter(data_instalacao__lte=data_fim)
        
        # --- Lógica de Depreciação ou Listagem Simples ---
        tipo_listagem = request.GET.get('tipo_listagem')
        if tipo_listagem == 'depreciacao':
            dados_depreciacao = []
            computadores_para_depreciacao = queryset.prefetch_related('dispositivos__chamados_set__categoria')
            for comp in computadores_para_depreciacao:
                score = calcular_depreciacao_computador(comp)
                dados_depreciacao.append({'computador': comp, 'score': score})
            dados_depreciacao.sort(key=lambda x: x['score'])
            contexto['dados_depreciacao'] = dados_depreciacao
        else: # Listagem Simples
            contexto['computadores'] = queryset

        # --- Lógica para Gráficos ---
        com_graficos = request.GET.get('com_graficos') == 'true'
        if com_graficos and queryset.exists():
            # Gráfico de Ativos
            ativos = queryset.filter(ativo=True).count()
            inativos = queryset.count() - ativos
            df = pd.DataFrame({'Status': ['Ativos', 'Inativos'], 'Quantidade': [ativos, inativos]})
            fig = px.pie(df, names='Status', values='Quantidade', title='Status dos Computadores Filtrados')
            contexto['graph_ativos'] = fig.to_html(full_html=False, include_plotlyjs='cdn')
            # Você poderia adicionar o gráfico por setor aqui também
        
        template_name = 'dispositivos/partials/relatorios/_preview_computadores.html'

    # ... adicione elif para cada outra categoria (servidores, chamados, etc.) ...
    
    # A CORREÇÃO: Passamos o 'contexto' diretamente, sem o aninhar dentro de 'dados'
    html_content = render_to_string(template_name, contexto)

    return JsonResponse({'html': html_content})

@csrf_exempt # Para simplificar a chamada via POST do JS
def exportar_html_para_pdf(request):
    """
    Recebe um bloco de HTML via POST e o converte para um PDF para download.
    """
    if request.method == 'POST':
        # Pegamos o HTML que o JavaScript nos enviou
        html_para_converter = request.POST.get('html_content', '')
        
        # Criamos um contexto simples para o template do PDF
        contexto = {'conteudo_do_preview': html_para_converter}
        
        # Usamos um template "invólucro" que contém o cabeçalho e os estilos do PDF
        template_path = 'dispositivos/partials/relatorios/pdf_wrapper.html'
        
        pdf = render_to_pdf(template_path, contexto)
        
        if pdf:
            response = HttpResponse(pdf, content_type='application/pdf')
            filename = f"relatorio_customizado_{timezone.now().strftime('%Y%m%d')}.pdf"
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response
        
    return HttpResponse("Erro: Requisição inválida ou falha na geração do PDF.", status=400)







