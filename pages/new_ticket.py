"""
New Ticket Submission Page for SupportFlow AI (Phase 1).

Allows customers / support representatives to submit a new support ticket.
Validates input fields and persists the record to the SQLite database.
"""

import streamlit as st
from services.ticket_service import create_ticket


def render_new_ticket_page():
    st.markdown(
        """
        <div style="margin-bottom: 2rem;">
            <h1 style="margin: 0; font-size: 1.85rem; font-weight: 700; color: #1e293b;">
                Create Support Ticket
            </h1>
            <p style="margin: 0.35rem 0 0 0; color: #64748b; font-size: 0.95rem;">
                Submit a new customer inquiry or incident into the support queue
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Initialize form state in session if needed
    if "form_customer_name" not in st.session_state:
        st.session_state["form_customer_name"] = ""
    if "form_subject" not in st.session_state:
        st.session_state["form_subject"] = ""
    if "form_description" not in st.session_state:
        st.session_state["form_description"] = ""
    if "ticket_created_success" not in st.session_state:
        st.session_state["ticket_created_success"] = None

    if st.session_state["ticket_created_success"]:
        st.success(st.session_state["ticket_created_success"])
        st.session_state["ticket_created_success"] = None

    # Form card container
    with st.container():
        with st.form("new_ticket_form", clear_on_submit=True):
            st.markdown("##### Ticket Information")

            customer_name = st.text_input(
                "Customer Name *",
                placeholder="e.g. Jane Doe or Acme Corp",
                help="Enter the full name or company identity of the customer submitting the ticket."
            )

            subject = st.text_input(
                "Subject *",
                placeholder="e.g. Unable to process monthly billing invoice",
                help="A concise summary of the issue or inquiry."
            )

            description = st.text_area(
                "Ticket Description *",
                placeholder="Provide complete details regarding the problem, error messages, or questions...",
                height=180,
                help="Detailed description of the customer's request."
            )

            st.markdown("<div style='height: 0.5rem;'></div>", unsafe_allow_html=True)
            col_btn, _ = st.columns([1, 4])
            with col_btn:
                submitted = st.form_submit_button("Submit Ticket", use_container_width=True)

            if submitted:
                success, result = create_ticket(
                    customer_name=customer_name,
                    subject=subject,
                    description=description
                )

                if success:
                    st.session_state["ticket_created_success"] = (
                        f"✅ Ticket #{result} created successfully with status 'New'."
                    )
                    st.rerun()
                else:
                    st.error(f"❌ {result}")


if __name__ == "__main__" or True:
    render_new_ticket_page()
