# Em dispositivos/forms.py

from django import forms
from .models import Chamados, Setores, Usuarios, Dispositivos, CategoriasAtend, PastaPublica,LoginUsuarioPc,Hosts,EmailsNovos,EmailsAntigos,Computadores, Servidores, Roteadores, Impressoras,PlanoManuPrevent,Treinamentos

class CadastroUsuarioForm(forms.ModelForm):
    senha = forms.CharField(
        label='Senha', 
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        help_text='A senha será armazenada de forma segura (hash).'
    )
    confirmacao_senha = forms.CharField(
        label='Confirme a Senha', 
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = Usuarios
        fields = ['nome', 'cpf', 'funcao']
        labels = {
            'nome': 'Nome de Usuário',
            'cpf': 'CPF',
            'funcao': 'Função no Sistema'
        }

    def clean_confirmacao_senha(self):
        """
        Este método especial de validação verifica se os dois campos de senha são iguais.
        """
        senha = self.cleaned_data.get("senha")
        confirmacao_senha = self.cleaned_data.get("confirmacao_senha")
        if senha and confirmacao_senha and senha != confirmacao_senha:
            raise forms.ValidationError("As senhas não coincidem.")
        return confirmacao_senha

class CadastroChamadoForm(forms.ModelForm):
    # Um dropdown customizado para o nível de urgência
    NIVEL_CHOICES = [ (i, f"{i} - {'Baixa' if i==1 else 'Normal' if i==2 else 'Média' if i==3 else 'Alta' if i==4 else 'Crítica'}") for i in range(1, 6) ]
    nivel_atendimento_cliente = forms.ChoiceField(
        choices=NIVEL_CHOICES, 
        label="Nível de Urgência",
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    class Meta:
        model = Chamados
        # Incluímos todos os campos que o usuário deve preencher
        fields = [
            'titulo', 
            'descricao_problema',
            'setores',
            'usuario',
            'dispositivos',
            'categoria',
            'nivel_atendimento_cliente',
            'data_chamado',
            'data_finalizacao'
        ]
        labels = {
            'titulo': 'Título do Chamado',
            'descricao_problema': 'Descrição Detalhada do Problema',
            'setores': 'Setor Afetado',
            'usuario': 'Solicitante',
            'dispositivos': 'Dispositivo Relacionado',
            'categoria': 'Categoria do Atendimento',
            'data_chamado': 'Início do Atendimento',
            'data_finalizacao': 'Fim do Atendimento'
        }
        widgets = {
            'data_chamado': forms.DateTimeInput(
                format='%Y-%m-%dT%H:%M',
                attrs={'type': 'datetime-local', 'class': 'form-control'}
            ),
            'data_finalizacao': forms.DateTimeInput(
                format='%Y-%m-%dT%H:%M',
                attrs={'type': 'datetime-local', 'class': 'form-control'}
            ),
            'descricao_problema': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'setores': forms.Select(attrs={'class': 'form-select'}),
            'usuario': forms.Select(attrs={'class': 'form-select'}),
            'dispositivos': forms.Select(attrs={'class': 'form-select'}),
            'categoria': forms.Select(attrs={'class': 'form-select'}),
        }

class CadastroPastaPublicaForm(forms.ModelForm):
    class Meta:
        model = PastaPublica
        fields = ['nome_user', 'senha', 'setores']
        labels = {
            'nome_user': 'Nome de Usuário / Pasta',
            'senha': 'Senha (será visível)',
            'setores': 'Setor Associado (Opcional)'
        }
        widgets = {
            # Garante que o campo de senha seja um input de texto normal
            'senha': forms.TextInput(attrs={'class': 'form-control'}),
            'setores': forms.Select(attrs={'class': 'form-select'}),
        }

class CadastroLoginPcForm(forms.ModelForm):
    class Meta:
        model = LoginUsuarioPc
        fields = ['nome_user', 'senha', 'computadores']
        labels = {
            'nome_user': 'Nome de Usuário no PC',
            'senha': 'Senha (será visível)',
            'computadores': 'Computador Associado'
        }
        widgets = {
            'senha': forms.TextInput(attrs={'class': 'form-control'}),
            'computadores': forms.Select(attrs={'class': 'form-select'}),
        }

class CadastroHostForm(forms.ModelForm):
    # DEFINIMOS O CAMPO EXPLICITAMENTE AQUI COM O NOME CORRETO
    ip_host = forms.GenericIPAddressField(
        protocol='IPv4', # Especificamos que só aceitamos IPv4
        label="Endereço IPv4 do Host",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: 192.168.1.1'})
    )

    class Meta:
        model = Hosts
        fields = ['nome_host', 'ip_host']
        labels = {
            'nome_host': 'Nome do Host (Ex: SRV-AD-01)',
        }
        widgets = {
            'nome_host': forms.TextInput(attrs={'class': 'form-control'}),
        }

class CadastroEmailNovoForm(forms.ModelForm):
    class Meta:
        model = EmailsNovos
        fields = ['nome_email', 'tamanho_email', 'senha', 'setores']
        labels = {
            'nome_email': 'Endereço de Email',
            'tamanho_email': 'Tamanho da Caixa (GB)',
            'senha': 'Senha (será visível)',
            'setores': 'Setor Associado (Opcional)'
        }
        widgets = {
            'nome_email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'exemplo@hospital.com'}),
            'tamanho_email': forms.NumberInput(attrs={'class': 'form-control'}),
            'senha': forms.TextInput(attrs={'class': 'form-control'}), # Garante que seja um input de texto normal
            'setores': forms.Select(attrs={'class': 'form-select'}),
        }

class CadastroEmailAntigoForm(forms.ModelForm):
    class Meta:
        model = EmailsAntigos
        fields = ['nome_email', 'tamanho_email', 'senha', 'setores']
        labels = {
            'nome_email': 'Endereço de Email',
            'tamanho_email': 'Tamanho da Caixa (GB)',
            'senha': 'Senha (será visível)',
            'setores': 'Setor Associado (Opcional)'
        }
        widgets = {
            'nome_email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'exemplo@hospital.com'}),
            'tamanho_email': forms.NumberInput(attrs={'class': 'form-control'}),
            'senha': forms.TextInput(attrs={'class': 'form-control'}),
            'setores': forms.Select(attrs={'class': 'form-select'}),
        }

    class Meta:
        model = Impressoras
        fields = '__all__'

class PlanoManutencaoForm(forms.ModelForm):
    class Meta:
        model = PlanoManuPrevent
        fields = ['dispositivos', 'data_manu', 'situacao', 'descricao']
        labels = {
            'dispositivos': 'Dispositivo Alvo',
            'data_manu': 'Data da Manutenção',
            'situacao': 'Situação',
            'descricao': 'Descrição do Procedimento',
        }
        widgets = {
            'data_manu': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'descricao': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'dispositivos': forms.Select(attrs={'class': 'form-select'}),
            # Esta linha garante que o campo será um dropdown com a classe do Bootstrap
            'situacao': forms.Select(attrs={'class': 'form-select'}),
        }


class TreinamentoForm(forms.ModelForm):
    class Meta:
        model = Treinamentos
        # Adicionamos os campos de data/hora ao formulário
        fields = ['titulo', 'descricao', 'setores', 'data_ts_treinamento', 'data_finalizacao', 'data_trei']
        labels = {
            'titulo': 'Título do Treinamento',
            'descricao': 'Descrição Detalhada',
            'setores': 'Setor Responsável',
            'data_ts_treinamento': 'Início do Treinamento/Evento',
            'data_finalizacao': 'Fim do Treinamento/Evento',
            'data_trei': 'Data de Referência (Opcional)',
        }
        # Adicionamos widgets para os campos de data/hora
        widgets = {
            'data_ts_treinamento': forms.DateTimeInput(
                format='%Y-%m-%dT%H:%M', # Adiciona o formato esperado pelo HTML
                attrs={'type': 'datetime-local', 'class': 'form-control'}
            ),
            'data_finalizacao': forms.DateTimeInput(
                format='%Y-%m-%dT%H:%M', # Adiciona o formato esperado pelo HTML
                attrs={'type': 'datetime-local', 'class': 'form-control'}
            ),
            'data_trei': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'descricao': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'setores': forms.Select(attrs={'class': 'form-select'}),
        }

class CadastroLoginPcForm(forms.ModelForm):
    class Meta:
        model = LoginUsuarioPc
        fields = ['nome_user', 'senha', 'computadores']
        labels = {
            'nome_user': 'Nome de Usuário no PC',
            'senha': 'Senha (será visível)',
            'computadores': 'Computador Associado'
        }
        widgets = {
            # Forçamos um input de texto normal para a senha
            'senha': forms.TextInput(attrs={'class': 'form-control'}),
            'computadores': forms.Select(attrs={'class': 'form-select'}),
        }

class UsuarioForm(forms.ModelForm):
    # Campos extras para a alteração de senha, que não estão no modelo diretamente
    nova_senha = forms.CharField(
        label='Nova Senha',
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        required=False, # Não é obrigatório preencher
        help_text="Deixe em branco para não alterar a senha atual."
    )
    confirmacao_senha = forms.CharField(
        label='Confirme a Nova Senha',
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        required=False # Não é obrigatório preencher
    )

    class Meta:
        model = Usuarios
        # O campo 'senha_hash' é omitido de propósito
        fields = ['nome', 'cpf', 'funcao']
        labels = {
            'nome': 'Nome de Usuário',
            'cpf': 'CPF',
            'funcao': 'Função no Sistema'
        }
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'cpf': forms.TextInput(attrs={'class': 'form-control'}),
            'funcao': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def clean(self):
        """ Validação customizada para os campos de senha. """
        cleaned_data = super().clean()
        nova_senha = cleaned_data.get("nova_senha")
        confirmacao_senha = cleaned_data.get("confirmacao_senha")

        if nova_senha and nova_senha != confirmacao_senha:
            self.add_error('confirmacao_senha', "As senhas não coincidem.")
        
        return cleaned_data

class ComputadorForm(forms.ModelForm):
    class Meta:
        model = Computadores
        fields = '__all__'
        widgets = {
            'data_instalacao': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'ativo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if field_name not in ['ativo']:
                field.widget.attrs.update({'class': 'form-control form-control-sm'})
            if isinstance(field.widget, forms.Select):
                field.widget.attrs.update({'class': 'form-select form-select-sm'})


class ServidorForm(forms.ModelForm):
    class Meta:
        model = Servidores
        fields = '__all__'
        widgets = {
            'data_instalacao': forms.DateInput(attrs={'type': 'date', 'class': 'form-control form-control-sm'}),
            'ativo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if field_name not in ['ativo']:
                field.widget.attrs.update({'class': 'form-control form-control-sm'})
            if isinstance(field.widget, forms.Select):
                field.widget.attrs.update({'class': 'form-select form-select-sm'})


class RoteadorForm(forms.ModelForm):
    class Meta:
        model = Roteadores
        fields = '__all__'
        widgets = {
            'data_instalacao': forms.DateInput(attrs={'type': 'date', 'class': 'form-control form-control-sm'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': 'form-control form-control-sm'})
            if isinstance(field.widget, forms.Select):
                field.widget.attrs.update({'class': 'form-select form-select-sm'})


class ImpressoraForm(forms.ModelForm):
    class Meta:
        model = Impressoras
        fields = '__all__'
        widgets = {
            'data_instalacao': forms.DateInput(attrs={'type': 'date', 'class': 'form-control form-control-sm'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': 'form-control form-control-sm'})
            if isinstance(field.widget, forms.Select):
                field.widget.attrs.update({'class': 'form-select form-select-sm'})
    