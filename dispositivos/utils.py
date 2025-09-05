from datetime import date
from .models import Usuarios, Treinamentos, Setores, Servidores,Roteadores,Impressoras,Computadores, PlanoManuPrevent, Dispositivos,LoginUsuarioPc,PastaPublica,Hosts, EmailsNovos, EmailsAntigos, Chamados
from django.contrib.auth.hashers import make_password
from django.contrib.auth.hashers import check_password
from django.utils import timezone
from datetime import datetime
from datetime import timedelta
from django.utils import timezone
from .models import Chamados
from io import BytesIO
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
from django.conf import settings
import os

PESOS_DEPRECIACAO = {
    # FATOR IDADE: Quantos pontos perder por mês de uso
    'pontos_por_mes_de_idade': 0.5,  # Ex: 24 meses = -12 pontos

    # FATOR HARDWARE: Penalidades baseadas em componentes
    'penalidade_hdd': 15, # Penalidade se o armazenamento principal for HDD
    'penalidade_ram_ddr4': 10, # Penalidade se a RAM for DDR4 (assumindo que DDR5 é o novo padrão)
    'penalidade_ram_insuficiente': 10, # Penalidade se tiver menos de 8GB de RAM

    # FATOR CHAMADOS: Penalidades baseadas no histórico de problemas
    'pontos_por_manutencao': 5, # Penalidade para cada chamado de "Manutenção"
    'pontos_por_chamado_geral': 2, # Penalidade para cada chamado de outras categorias

    # FATOR PERFORMANCE: Penalidade por S.O. moderno em hardware antigo
    'penalidade_so_incompativel': 20,


    'impressora_pontos_por_mes': 0.7, # Impressoras depreciam um pouco mais rápido
    'impressora_pontos_por_manutencao': 8, # Manutenção em impressora é mais crítico
    'impressora_pontos_por_chamado_geral': 3,

    'roteador_pontos_por_mes': 0.4, # Roteadores têm um ciclo de vida mais longo
    'roteador_pontos_por_manutencao': 10, # Manutenção em um roteador é um sinal de alerta
    'roteador_pontos_por_chamado_geral': 4,


    'servidor_pontos_por_mes': 0.3, # Servidores são feitos para durar, depreciam mais devagar
    'servidor_penalidade_hdd': 10,  # Penalidade se o S.O. não estiver em SSD
    'servidor_pontos_por_manutencao': 15, # Manutenção em servidor é muito crítico
    'servidor_pontos_por_chamado_geral': 5,
}

def criar_plano_manutencao(
    dispositivo_obj: Dispositivos,
    data_manu: date,
    descricao: str,
    situacao: str = 'Agendada'
):
    """
    Cria um novo Plano de Manutenção Preventiva para um dispositivo específico.
    Evita duplicatas para o mesmo dispositivo na mesma data.
    """
    plano_obj, created = PlanoManuPrevent.objects.get_or_create(
        dispositivos=dispositivo_obj, # Busca pela relação com o dispositivo
        data_manu=data_manu,         # e pela data
        defaults={
            'descricao': descricao,
            'situacao': situacao
        }
    )

    if created:
        print(f"SUCESSO: Manutenção para '{dispositivo_obj.nome_descritivo}' agendada para {data_manu}.")
    else:
        print(f"AVISO: Já existe uma manutenção para este dispositivo nesta data.")
    
    return plano_obj

def criar_login_pc(computador_obj: Computadores, nome_user: str, senha: str):
    login_obj, created = LoginUsuarioPc.objects.get_or_create(
        computadores=computador_obj,
        nome_user=nome_user,
        defaults={'senha': senha}
    )
    if created:
        print(f"SUCESSO: Login para '{nome_user}' no computador '{computador_obj.nome}' foi criado.")
    else:
        login_obj.senha = senha
        login_obj.save()
        print(f"AVISO: Login para '{nome_user}' neste computador já existia. Senha foi atualizada.")
    return login_obj

def criar_pasta_publica(nome_user: str, senha: str, setor_obj: Setores = None):
    pasta_obj, created = PastaPublica.objects.get_or_create(
        nome_user=nome_user,
        defaults={
            'senha': senha,
            'setores': setor_obj
        }
    )
    if created:
        print(f"SUCESSO: Pasta pública para '{nome_user}' foi criada.")
    else:
        pasta_obj.senha = senha
        pasta_obj.save()
        print(f"AVISO: Pasta pública para '{nome_user}' já existia. Senha foi atualizada.")
    return pasta_obj

def criar_host(nome_host: str, ip_host: str):
    host_obj, created = Hosts.objects.get_or_create(
        ip_host=ip_host,
        defaults={'nome_host': nome_host}
    )
    if created:
        print(f"SUCESSO: Host '{nome_host}' ({ip_host}) foi criado.")
    else:
        host_obj.nome_host = nome_host
        host_obj.save()
        print(f"AVISO: Host com IP '{ip_host}' já existia. Nome foi atualizado para '{nome_host}'.")
    return host_obj

def criar_email_novo(nome_email: str, tamanho_email: int, senha: str, setor_obj: Setores = None):
    email_obj, created = EmailsNovos.objects.get_or_create(
        nome_email=nome_email,
        defaults={
            'tamanho_email': tamanho_email,
            'senha': senha,
            'setores': setor_obj
        }
    )
    if created:
        print(f"SUCESSO: Email (novo) '{nome_email}' foi criado.")
    else:
        email_obj.senha = senha
        email_obj.save()
        print(f"AVISO: Email (novo) '{nome_email}' já existia. Senha foi atualizada.")
    return email_obj

def criar_email_antigo(nome_email: str, tamanho_email: int, senha: str, setor_obj: Setores = None):
    email_obj, created = EmailsAntigos.objects.get_or_create(
        nome_email=nome_email,
        defaults={
            'tamanho_email': tamanho_email,
            'senha': senha,
            'setores': setor_obj
        }
    )
    if created:
        print(f"SUCESSO: Email (antigo) '{nome_email}' foi criado.")
    else:
        email_obj.senha = senha
        email_obj.save()
        print(f"AVISO: Email (antigo) '{nome_email}' já existia. Senha foi atualizada.")
    return email_obj

def criar_computador(
    endereco_mac: str,
    setor_obj: Setores,
    nome: str,
    modelo: str,
    ip_dispositivo: str,
    data_instalacao: date,
    marca_processador: str,
    frequencia_processador: float,
    tamanho_memoria: int,
    velocidade_memoria: int,
    tipo_armazenamento: str,
    tamanho_armazenamento: int,
    versao_so: str,
    potencia_fonte: int,
    ativo: bool = True
):
    """Cria um novo Computador se ele não existir, buscando pelo endereço MAC."""
    
    computador_obj, created = Computadores.objects.get_or_create(
        endereco_mac=endereco_mac, 
        defaults={
            'setor': setor_obj,
            'nome': nome,
            'modelo': modelo,
            'ip_dispositivo': ip_dispositivo,
            'data_instalacao': data_instalacao,
            'marca_processador': marca_processador,
            'frequencia_processador': frequencia_processador,
            'tamanho_memoria': tamanho_memoria,
            'velocidade_memoria': velocidade_memoria,
            'tipo_armazenamento': tipo_armazenamento,
            'tamanho_armazenamento': tamanho_armazenamento,
            'versao_so': versao_so,
            'potencia_fonte': potencia_fonte,
            'ativo': ativo
        }
    )

    if created:
        print(f"SUCESSO: Computador '{computador_obj.nome}' (MAC: {computador_obj.endereco_mac}) foi criado.")
    else:
        print(f"AVISO: Computador com MAC '{computador_obj.endereco_mac}' já existe.")
        
    return computador_obj

def criar_servidor(
    service_tag: str,
    setor_obj: Setores,
    modelo: str,
    marca: str,
    endereco_mac: str,
    ip_dispositivo: str,
    data_instalacao: date,
    marca_processador: str,
    frequencia_processador: float,
    tamanho_memoria: int,
    velocidade_memoria: int,
    tipo_armazenamento: str,
    tamanho_armazenamento: int,
    versao_so: str,
    express_code: str,
    ativo: bool = True
):
    servidor_obj, created = Servidores.objects.get_or_create(
        service_tag=service_tag,
        defaults={
            'setor': setor_obj,
            'modelo': modelo,
            'marca': marca,
            'endereco_mac': endereco_mac,
            'ip_dispositivo': ip_dispositivo,
            'data_instalacao': data_instalacao,
            'marca_processador': marca_processador,
            'frequencia_processador': frequencia_processador,
            'tamanho_memoria': tamanho_memoria,
            'velocidade_memoria': velocidade_memoria,
            'tipo_armazenamento': tipo_armazenamento,
            'tamanho_armazenamento': tamanho_armazenamento,
            'versao_so': versao_so,
            'express_code': express_code,
            'ativo': ativo
        }
    )

    if created:
        print(f"SUCESSO: Servidor '{servidor_obj.modelo}' (ST: {servidor_obj.service_tag}) foi criado.")
    else:
        print(f"AVISO: Servidor com Service Tag '{servidor_obj.service_tag}' já existe.")
        
    return servidor_obj

def criar_roteador(
    endereco_mac: str,
    setor_obj: Setores,
    marca: str,
    modelo: str,
    ip_dispositivo: str,
    data_instalacao: date
):   
    roteador_obj, created = Roteadores.objects.get_or_create(
        endereco_mac=endereco_mac, 
        defaults={
            'setor': setor_obj,
            'marca': marca,
            'modelo': modelo,
            'ip_dispositivo': ip_dispositivo,
            'data_instalacao': data_instalacao
        }
    )

    if created:
        print(f"SUCESSO: Roteador '{roteador_obj.marca} {roteador_obj.modelo}' foi criado.")
    else:
        print(f"AVISO: Roteador com MAC '{roteador_obj.endereco_mac}' já existe.")
        
    return roteador_obj

def criar_impressora(
    serial: str,
    setor_obj: Setores,
    modelo: str,
    toner: str,
    nome_impressora: str,
    proprietario: str,
    tipo_conexao: str,
    ip_dispositivo: str = None
):
    """Cria uma nova Impressora se ela não existir, buscando pelo serial."""

    impressora_obj, created = Impressoras.objects.get_or_create(
        serial=serial, 
        defaults={
            'setor': setor_obj,
            'modelo': modelo,
            'toner': toner,
            'nome_impressora': nome_impressora,
            'proprietario': proprietario,
            'tipo_conexao': tipo_conexao,
            'ip_dispositivo': ip_dispositivo 
        }
    )
    if created:
        print(f"SUCESSO: Impressora '{impressora_obj.nome_impressora}' foi criada.")
    else:
        print(f"AVISO: Impressora com serial '{impressora_obj.serial}' já existe.")
        
    return impressora_obj

def criar_usuario(nome: str, senha: str, cpf: str, funcao: str):
    if not all([nome, senha, cpf, funcao]):
        print("Erro: Todos os campos (nome, senha, cpf, funcao) são obrigatórios.")
        return

    senha_hash_segura = make_password(senha)
    usuario_obj, created = Usuarios.objects.get_or_create(
        cpf=cpf,  
        defaults={
            'nome': nome,
            'senha_hash': senha_hash_segura,
            'funcao': funcao,
            'data_cadastro': timezone.now().date()
        }
    )
    if created:
        print(f"SUCESSO: Usuário '{usuario_obj.nome}' com CPF '{usuario_obj.cpf}' foi criado.")
    else:
        print(f"AVISO: Usuário com CPF '{usuario_obj.cpf}' já existe no banco de dados. Nenhum novo usuário foi criado.")

def criar_chamado(
    titulo: str,
    descricao_problema: str,
    usuario_obj: Usuarios,
    dispositivo_obj: Dispositivos,
    setor_obj: Setores,
    data_finalizacao: datetime,
    nivel_atendimento: int,
    data_chamado: datetime = None
):
    """Cria um novo chamado no sistema."""
    
    # Se a data do chamado não for fornecida, usa a data e hora atuais
    if data_chamado is None:
        data_chamado = timezone.now()

    chamado_obj, created = Chamados.objects.get_or_create(
        dispositivos=dispositivo_obj,
        data_chamado=data_chamado,
        defaults={
            'titulo': titulo,
            'descricao_problema': descricao_problema,
            'usuario': usuario_obj,
            'setores': setor_obj,
            'data_finalizacao': data_finalizacao,
            'nivel_atendimento_cliente': nivel_atendimento,
            'data_dia': data_chamado.date()
        }
    )

    if created:
        print(f"SUCESSO: Chamado '{chamado_obj.titulo}' foi aberto.")
    else:
        print(f"AVISO: Um chamado para este dispositivo nesta data/hora já existe.")
        
    return chamado_obj

def autenticar_usuario(nome_usuario: str, senha_plana: str):
    try:
        usuario = Usuarios.objects.get(nome=nome_usuario)
        senha_valida = check_password(senha_plana, usuario.senha_hash)
        if senha_valida:
            print(f"SUCESSO: Autenticação bem-sucedida para o usuário '{usuario.nome}'.")
            return usuario
        else:
            print(f"FALHA: Senha incorreta para o usuário '{nome_usuario}'.")
            return None
    except Usuarios.DoesNotExist:
        print(f"FALHA: Usuário '{nome_usuario}' não encontrado.")
        return None
    
def calcular_qualidade_servico():
    """
    Calcula uma pontuação de Qualidade de Serviço de TI com base em um conjunto de regras.
    Retorna uma porcentagem de 0 a 100.
    """
    qualidade = 100.0  # Começa com a pontuação perfeita
    penalidades = [] # Para depuração, podemos ver por que os pontos foram perdidos

    # --- REGRA 1: INCIDENTES REPETIDOS ---
    # Encontra chamados críticos (nível 5) dos últimos 30 dias para análise
    hoje = timezone.now()
    limite_tempo = hoje - timedelta(days=30)
    chamados_criticos_recentes = Chamados.objects.filter(
        nivel_atendimento_cliente=5,
        data_chamado__gte=limite_tempo
    ).order_by('dispositivos_id', 'categoria_id', 'data_chamado')

    # Lógica para encontrar repetições
    ocorrencias = {}
    for chamado in chamados_criticos_recentes:
        chave = (chamado.dispositivos_id, chamado.categoria_id)
        if chave in ocorrencias:
            # Se já vimos um chamado para esta combinação, verificamos a data
            if chamado.data_chamado - ocorrencias[chave] <= timedelta(days=5):
                qualidade -= 10 # Penalidade pesada para reincidência rápida
                penalidades.append(f"Reincidência no dispositivo {chave[0]} ({qualidade}%)")
        ocorrencias[chave] = chamado.data_chamado

    # --- REGRA 2: VIOLAÇÃO DE SLA (TEMPO DE ATENDIMENTO) ---
    # Define os limites de tempo (SLA) por nível de urgência
    sla_por_nivel = {
        5: timedelta(hours=1),   # Urgente: 1 hora
        4: timedelta(hours=3),   # Alta: 3 horas (1+2)
        3: timedelta(hours=5),   # Média: 5 horas (3+2)
        2: timedelta(hours=7),   # Normal: 7 horas (5+2)
        1: timedelta(hours=9),   # Baixa: 9 horas (7+2)
    }
    chamados_fechados_recentes = Chamados.objects.filter(data_finalizacao__isnull=False, data_chamado__gte=limite_tempo)
    for chamado in chamados_fechados_recentes:
        if chamado.duracao:
            sla = sla_por_nivel.get(chamado.nivel_atendimento_cliente, timedelta(days=99))
            if chamado.duracao > sla:
                qualidade -= 5 # Penalidade média por estourar o tempo
                penalidades.append(f"SLA violado no chamado {chamado.id} ({qualidade}%)")

    # --- REGRA 3: CHAMADOS PENDENTES / ATRASADOS ---
    chamados_nao_feitos = Chamados.objects.filter(situacao='NAO FEITO').count()
    chamados_atrasados = Chamados.objects.filter(situacao='ATRASADO').count()
    
    qualidade -= (chamados_nao_feitos * 1) # Penalidade pequena por chamado pendente
    if chamados_nao_feitos > 0:
        penalidades.append(f"{chamados_nao_feitos} chamados pendentes (-{chamados_nao_feitos*1}%)")

    qualidade -= (chamados_atrasados * 2) # Penalidade um pouco maior por atraso
    if chamados_atrasados > 0:
        penalidades.append(f"{chamados_atrasados} chamados atrasados (-{chamados_atrasados*2}%)")
    
    # --- REGRA 4: RECUPERAÇÃO DA QUALIDADE ---
    # A sua regra de "recuperar após 10 dias" é complexa. Uma forma mais simples
    # é que a qualidade é calculada dinamicamente. Se nos últimos 30 dias não houver
    # penalidades, a pontuação será 100%. A recuperação é automática!

    print("Penalidades de Qualidade:", penalidades) # Para depuração no terminal
    return max(0, int(qualidade)) # Garante que a nota não seja negativa e retorna um inteiro

def calcular_depreciacao_computador(computador):
    """
    Calcula uma pontuação de saúde/depreciação para um objeto Computador.
    Retorna uma pontuação de 0 a 100.
    """
    score = 100.0
    
    # --- FATOR 1: IDADE ---
    if computador.data_instalacao:
        hoje = date.today()
        meses_de_uso = (hoje.year - computador.data_instalacao.year) * 12 + (hoje.month - computador.data_instalacao.month)
        score -= meses_de_uso * PESOS_DEPRECIACAO['pontos_por_mes_de_idade']

    # --- FATOR 2: HARDWARE ---
    # (Esta é uma simplificação, mas ilustra a lógica)
    if 'hdd' in computador.tipo_armazenamento.lower():
        score -= PESOS_DEPRECIACAO['penalidade_hdd']
    if computador.tamanho_memoria < 8:
        score -= PESOS_DEPRECIACAO['penalidade_ram_insuficiente']
    # Para a versão do DDR, precisaríamos de um campo extra no modelo. Por agora, vamos omitir.
    
    # --- FATOR 3 & 5: CHAMADOS (MANUTENÇÕES E FREQUÊNCIA) ---
    # Para isto funcionar, a view precisa de passar os chamados relacionados
    # usando .prefetch_related() para ser eficiente.
    chamados_do_dispositivo = computador.dispositivos.chamados_set.all()
    
    if chamados_do_dispositivo:
        for chamado in chamados_do_dispositivo:
            score -= PESOS_DEPRECIACAO['pontos_por_chamado_geral']
            if chamado.categoria and 'manutenção' in chamado.categoria.nome.lower():
                score -= PESOS_DEPRECIACAO['pontos_por_manutencao']
                
    # --- FATOR 4: PERFORMANCE (S.O. vs HARDWARE) ---
    is_hardware_antigo = (computador.tamanho_memoria < 8 or 'hdd' in computador.tipo_armazenamento.lower())
    if '11' in computador.versao_so and is_hardware_antigo:
        score -= PESOS_DEPRECIACAO['penalidade_so_incompativel']

    # Garante que a pontuação final está entre 0 e 100
    return max(0, int(score))

def calcular_depreciacao_impressora(impressora):
    """
    Calcula uma pontuação de saúde/depreciação para um objeto Impressora.
    Retorna uma pontuação de 0 a 100.
    """
    score = 100.0
    
    # --- FATOR 1: IDADE ---
    if hasattr(impressora, 'instalacao') and impressora.instalacao:
        hoje = date.today()
        meses_de_uso = (hoje.year - impressora.instalacao.year) * 12 + (hoje.month - impressora.instalacao.month)
        score -= meses_de_uso * PESOS_DEPRECIACAO['impressora_pontos_por_mes']

    # --- FATOR 2: CHAMADOS (MANUTENÇÕES E FREQUÊNCIA) ---
    # Para isto funcionar, a view precisa de passar os chamados relacionados
    # usando .prefetch_related() para ser eficiente.
    try:
        chamados_da_impressora = impressora.dispositivos.chamados_set.all()
        
        if chamados_da_impressora:
            for chamado in chamados_da_impressora:
                score -= PESOS_DEPRECIACAO['impressora_pontos_por_chamado_geral']
                if chamado.categoria and 'manutenção' in chamado.categoria.nome.lower():
                    score -= PESOS_DEPRECIACAO['impressora_pontos_por_manutencao']
    except Dispositivos.DoesNotExist:
        # Se a impressora não tiver um registro correspondente em Dispositivos, não há chamados
        pass

    # Garante que a pontuação final está entre 0 e 100
    return max(0, int(score))

def calcular_depreciacao_roteador(roteador):
    """
    Calcula uma pontuação de saúde/depreciação para um objeto Roteador.
    """
    score = 100.0
    
    # FATOR 1: IDADE
    if roteador.data_instalacao:
        hoje = date.today()
        meses_de_uso = (hoje.year - roteador.data_instalacao.year) * 12 + (hoje.month - roteador.data_instalacao.month)
        score -= meses_de_uso * PESOS_DEPRECIACAO['roteador_pontos_por_mes']

    # FATOR 2: CHAMADOS (MANUTENÇÕES E FREQUÊNCIA)
    try:
        chamados_do_roteador = roteador.dispositivos.chamados_set.all()
        if chamados_do_roteador:
            for chamado in chamados_do_roteador:
                score -= PESOS_DEPRECIACAO['roteador_pontos_por_chamado_geral']
                if chamado.categoria and 'manutenção' in chamado.categoria.nome.lower():
                    score -= PESOS_DEPRECIACAO['roteador_pontos_por_manutencao']
    except Dispositivos.DoesNotExist:
        pass # Se não houver registro em Dispositivos, não há chamados.

    return max(0, int(score))

def calcular_depreciacao_servidor(servidor):
    """
    Calcula uma pontuação de saúde/depreciação para um objeto Servidor.
    """
    score = 100.0
    
    # FATOR 1: IDADE
    if servidor.data_instalacao:
        hoje = date.today()
        meses_de_uso = (hoje.year - servidor.data_instalacao.year) * 12 + (hoje.month - servidor.data_instalacao.month)
        score -= meses_de_uso * PESOS_DEPRECIACAO['servidor_pontos_por_mes']

    # FATOR 2: HARDWARE
    if 'hdd' in servidor.tipo_armazenamento.lower():
        score -= PESOS_DEPRECIACAO['servidor_penalidade_hdd']

    # FATOR 3: CHAMADOS (MANUTENÇÕES E FREQUÊNCIA)
    try:
        chamados_do_servidor = servidor.dispositivos.chamados_set.all()
        if chamados_do_servidor:
            for chamado in chamados_do_servidor:
                score -= PESOS_DEPRECIACAO['servidor_pontos_por_chamado_geral']
                if chamado.categoria and 'manutenção' in chamado.categoria.nome.lower():
                    score -= PESOS_DEPRECIACAO['servidor_pontos_por_manutencao']
    except Dispositivos.DoesNotExist:
        pass

    return max(0, int(score))

def fetch_resources(uri, rel):
    """
    Callback para encontrar recursos como imagens e CSS.
    Procura na sua pasta STATICFILES_DIRS.
    """
    # Converte a URL (ex: /static/images/logo.png) para um caminho de arquivo
    # C:\SeuProjeto\static\images\logo.png
    path = os.path.join(settings.STATICFILES_DIRS[0], uri.replace(settings.STATIC_URL, ""))
    return path

def render_to_pdf(template_path: str, context_dict: dict = {}):
    """
    Renderiza um template Django para um PDF e o retorna como uma resposta HTTP.
    """
    template = get_template(template_path)
    html = template.render(context_dict)
    
    result = BytesIO()
    
    # Cria o PDF, passando o callback para encontrar os recursos (imagens, etc.)
    pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result, link_callback=fetch_resources)
    
    if not pdf.err:
        return HttpResponse(result.getvalue(), content_type='application/pdf')
    
    # Se houver um erro, retorna None
    print(f"Erro ao gerar PDF: {pdf.err}")
    return None

def link_callback(uri, rel):
    """
    Converte URLs de media/estáticos para caminhos absolutos no sistema de arquivos
    para que o xhtml2pdf possa encontrá-los.
    """
    # Usa STATICFILES_DIRS que aponta para a sua pasta 'static' de desenvolvimento
    if settings.STATICFILES_DIRS:
        static_root = settings.STATICFILES_DIRS[0]
    else:
        static_root = settings.STATIC_ROOT

    static_url = settings.STATIC_URL # Geralmente /static/
    
    # Converte a URL em um caminho de arquivo
    if uri.startswith(static_url):
        path = os.path.join(static_root, uri.replace(static_url, ""))
    else:
        return uri

    # Garante que o arquivo realmente existe no caminho
    if not os.path.isfile(path):
        # Se não encontrar, não quebra a geração do PDF
        print(f"AVISO: O arquivo estático não foi encontrado em: {path}")
        return uri
    return path









