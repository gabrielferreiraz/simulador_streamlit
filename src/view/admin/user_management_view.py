"""
Refatorado: Módulo da view para Gerenciamento de Usuários.

Esta view agora é puramente declarativa. Ela utiliza o AdminService para
realizar todas as operações de backend e apenas se preocupa em renderizar
os widgets do Streamlit e exibir os dados ou mensagens de erro recebidas
do serviço. A lógica complexa foi completamente removida da camada de visão.
"""
import streamlit as st
import pandas as pd
from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, NoResultFound, SQLAlchemyError
from pydantic import ValidationError # Importa ValidationError do Pydantic

from src.view.admin.admin_service import AdminService
from src.config import config
from src.schemas.user import UserCreate, UserUpdate # Importa os esquemas Pydantic
from src.utils.cached_data import get_cached_all_users_with_team_info # Importa a função cacheada

def show_user_management(service: AdminService, db: Session):
    """Renderiza a UI para gerenciamento de usuários."""
    st.header("Gerenciamento de Usuários")

    # --- Formulário para Adicionar/Editar Usuário ---
    with st.expander("Adicionar Novo Usuário", expanded=False):
        with st.form("new_user_form", clear_on_submit=True):
            nome = st.text_input("Nome Completo")
            email = st.text_input("E-mail")
            password = st.text_input("Senha", type="password")
            role = st.selectbox("Papel", options=config.USER_ROLES)
            tipo_consultor = st.selectbox("Tipo de Consultor", options=config.CONSULTOR_TYPES)
            telefone = st.text_input("Telefone")
            foto = st.file_uploader("Foto (Opcional)", type=["jpg", "png"])

            submitted = st.form_submit_button("Adicionar Usuário")
            if submitted:
                user_data = {
                    "nome": nome,
                    "email": email,
                    "password": password,
                    "role": role,
                    "tipo_consultor": tipo_consultor,
                    "telefone": telefone,
                }
                try:
                    # Valida os dados com Pydantic
                    new_user_schema = UserCreate(**user_data)
                    foto_bytes = foto.getvalue() if foto else None
                    service.create_user(db, new_user_schema, foto_bytes)
                    st.success(f"Usuário '{nome}' criado com sucesso!")
                    st.rerun()
                except ValidationError as e:
                    st.error(f"Erro de validação: {e}")
                except IntegrityError as e:
                    st.error(f"Erro ao criar usuário: O nome ou e-mail já existem. Detalhes: {e}")
                except SQLAlchemyError as e:
                    st.error(f"Erro de banco de dados ao criar usuário: {e}")

    st.divider()

    # --- Lista de Usuários ---
    st.subheader("Usuários Cadastrados")
    try:
        # Usa a função cacheada para obter os usuários
        users = get_cached_all_users_with_team_info()
        if not users:
            st.info("Nenhum usuário cadastrado.")
            return

        # Converte os objetos SQLAlchemy User para dicionários para o DataFrame
        users_data = []
        for user in users:
            user_dict = {
                'id': user.id,
                'nome': user.nome,
                'role': user.role,
                'email': user.email,
                'team_name': user.team.name if user.team else None # Acessa o nome da equipe via relação
            }
            users_data.append(user_dict)

        df = pd.DataFrame(users_data)
        df_display = df[['id', 'nome', 'role', 'email', 'team_name']]
        df_display.rename(columns={'id': 'ID', 'nome': 'Nome', 'role': 'Papel', 'email': 'E-mail', 'team_name': 'Equipe'}, inplace=True)
        
        st.dataframe(df_display, use_container_width=True, hide_index=True)

        # --- Ações de Edição/Exclusão ---
        st.subheader("Ações")
        selected_user_id = st.selectbox("Selecione um usuário para editar ou excluir", options=df['id'], format_func=lambda x: f"{df.loc[df['id'] == x, 'nome'].values[0]} (ID: {x})")
        
        if selected_user_id:
            user_to_edit = service.get_user_by_id(db, selected_user_id)
            if user_to_edit:
                with st.form(f"edit_user_{selected_user_id}"):
                    st.write(f"Editando: **{user_to_edit.nome}**")
                    edited_nome = st.text_input("Nome", value=user_to_edit.nome)
                    edited_email = st.text_input("Email", value=user_to_edit.email)
                    edited_role = st.selectbox("Papel", options=config.USER_ROLES, index=config.USER_ROLES.index(user_to_edit.role))
                    edited_tipo_consultor = st.selectbox("Tipo de Consultor", options=config.CONSULTOR_TYPES, index=config.CONSULTOR_TYPES.index(user_to_edit.tipo_consultor) if user_to_edit.tipo_consultor else 0)
                    edited_telefone = st.text_input("Telefone", value=user_to_edit.telefone)
                    edited_foto = st.file_uploader("Foto (Opcional)", type=["jpg", "png"])
                    new_password = st.text_input("Nova Senha (deixe em branco para não alterar)", type="password")

                    col1, col2 = st.columns([1, 5])
                    if col1.form_submit_button("Salvar Alterações"):
                        user_update_data = {
                            "nome": edited_nome,
                            "email": edited_email,
                            "role": edited_role,
                            "tipo_consultor": edited_tipo_consultor,
                            "telefone": edited_telefone,
                        }
                        if new_password: user_update_data["password"] = new_password

                        try:
                            # Valida os dados com Pydantic
                            user_update_schema = UserUpdate(**user_update_data)
                            edited_foto_bytes = edited_foto.getvalue() if edited_foto else None
                            service.update_user(db, user_to_edit.id, user_update_schema, edited_foto_bytes)
                            st.success("Usuário atualizado com sucesso!")
                            st.rerun()
                        except ValidationError as e:
                            st.error(f"Erro de validação: {e}")
                        except IntegrityError as e:
                            st.error(f"Erro ao atualizar: O nome ou e-mail já existem. Detalhes: {e}")
                        except NoResultFound as e:
                            st.error(f"Erro ao atualizar: {e}")
                        except SQLAlchemyError as e:
                            st.error(f"Erro de banco de dados ao atualizar: {e}")

                    if col2.form_submit_button("Excluir Usuário", type="primary"):
                        try:
                            service.delete_user(db, user_to_edit.id)
                            st.success("Usuário excluído com sucesso!")
                            st.rerun()
                        except NoResultFound as e:
                            st.error(f"Erro ao excluir: {e}")
                        except SQLAlchemyError as e:
                            st.error(f"Erro de banco de dados ao excluir: {e}")

    except SQLAlchemyError as e:
        st.error(f"Não foi possível carregar os usuários: {e}")
