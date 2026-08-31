"""
New Ticket Submission Page for SupportFlow AI.

Allows customers / support representatives to submit a new support ticket.
Validates input fields and persists the record to the SQLite database.
"""

import streamlit as st
from services.ticket_service import create_ticket


def render_new_ticket_page():
    st.markdown(
        """
        <div style="display: flex; justify-content: space-between; align-items: flex-end; margin-bottom: 0.5rem;">
            <div>
                <h1 style="margin: 0; font-size: 1.75rem; font-weight: 700;">Submit Support Ticket</h1>
                <div style="color: #94A3B8; font-size: 0.88rem; margin-top: 4px;">Ingest a new customer inquiry, bug report, or incident into the support queue</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    st.divider()

    # Form success notification
    if "ticket_created_success" not in st.session_state:
        st.session_state["ticket_created_success"] = None

    if st.session_state["ticket_created_success"]:
        st.success(st.session_state["ticket_created_success"])
        st.session_state["ticket_created_success"] = None

    col_form, _ = st.columns([2.2, 1])
    with col_form:
        with st.container(border=True):
            with st.form("new_ticket_form", clear_on_submit=True):
                st.markdown(
                    """
                    <div style="font-size: 1.05rem; font-weight: 700; color: #F8FAFC; margin-bottom: 12px;">
                        Ticket Details
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                customer_name = st.text_input(
                    "Customer Name *",
                    placeholder="e.g. Jane Doe or Acme Corp",
                    help="Enter the customer or organization identity."
                )

                subject = st.text_input(
                    "Subject *",
                    placeholder="e.g. Unable to process monthly billing invoice",
                    help="A concise summary of the issue."
                )

                description = st.text_area(
                    "Ticket Description *",
                    placeholder="Provide complete details regarding the problem, error messages, or questions...",
                    height=180,
                    help="Detailed description of the customer request."
                )

                st.markdown("<div style='height: 0.5rem;'></div>", unsafe_allow_html=True)
                submitted = st.form_submit_button("Submit Ticket to Queue", type="primary", use_container_width=True)

                if submitted:
                    success, result = create_ticket(
                        customer_name=customer_name,
                        subject=subject,
                        description=description
                    )

                    if success:
                        st.session_state["ticket_created_success"] = (
                            f"Ticket #{result} submitted successfully with status 'New'."
                        )
                        st.rerun()
                    else:
                        st.error(result)


if __name__ == "__main__" or True:
    render_new_ticket_page()
