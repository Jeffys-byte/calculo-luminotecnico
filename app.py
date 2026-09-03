import streamlit as st
import datetime

# --- SISTEMA DE AUTENTICAÇÃO E CONTROLE DE LICENÇA ---
def verificar_autenticacao():
    if "autenticado" not in st.session_state:
        st.session_state.autenticado = False
    if "usuario_email" not in st.session_state:
        st.session_state.usuario_email = None

    if not st.session_state.autenticado:
        st.markdown("## 🔐 Área Restrita - Luminotécnica Profissional")
        st.markdown("Faça login com sua conta ou escolha um plano de acesso para continuar.")
        
        tab_login, tab_planos = st.tabs(["🔑 Fazer Login", "💳 Assinar por R$ 14,90/mês"])
        
        with tab_login:
            with st.form("form_login"):
                email_input = st.text_input("E-mail cadastrado", value="").strip().lower()
                senha_input = st.text_input("Senha", type="password", value="").strip()
                btn_entrar = st.form_submit_button("Entrar no Sistema")
                
                if btn_entrar:
                    # Exemplo de regra de validade / licenciamento
                    if email_input == "jefkar27@gmail.com":
                        st.session_state.autenticado = True
                        st.session_state.usuario_email = email_input
                        st.session_state.plano_ativo = "Acesso Administrador (Vitalício)"
                        st.success("Login realizado com sucesso!")
                        st.rerun()
                    elif email_input != "":
                        # Aqui no futuro você valida se a data de hoje é menor que o vencimento no Supabase
                        # Simulando um usuário válido por enquanto:
                        st.session_state.autenticado = True
                        st.session_state.usuario_email = email_input
                        st.session_state.plano_ativo = "Assinatura Mensal (R$ 14,90)"
                        st.success("Login realizado com sucesso!")
                        st.rerun()
                    else:
                        st.error("Preencha o e-mail e a senha.")
                        
        with tab_planos:
            st.markdown("### 🚀 Assinatura Profissional de Baixo Custo")
            st.markdown("Tenha acesso completo a todos os cálculos de luminotécnica, fitas LED e geração de relatórios ilimitados em Word.")
            
            st.info("💡 **Apenas R$ 14,90 / mês** (Cancele quando quiser).")
            
            # Substitua o link abaixo pelo seu link de Assinatura/Pagamento gerado no Mercado Pago
            link_mercado_pago = "https://www.mercadopago.com.br/subscriptions/checkout?preapproval_id=SEU_ID_DE_ASSINATURA"
            
            st.link_button("💳 Assinar Agora por R$ 14,90/mês via Mercado Pago", link_mercado_pago, use_container_width=True)
            
            st.markdown("---")
            st.markdown("*(Após a confirmação do pagamento, seu acesso é liberado automaticamente para o e-mail utilizado na compra).*")
                    
        return False

    return True
