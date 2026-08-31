"""
New Ticket Submission Page for SupportFlow AI.

Allows customers / support representatives to submit a new support ticket.
Validates input fields and persists the record to the SQLite database.
Layout is centered with balanced equal margins on both left and right sides.
"""

import streamlit as st
from services.ticket_service import create_ticket


def render_new_ticket_page():
    st.title("Create Support Ticket")
    st.caption("Submit a new customer inquiry or incident into the support queue")
    st.divider()

    # Form success notification
    if "ticket_created_success" not in st.session_state:
        st.session_state["ticket_created_success"] = None

    if st.session_state["ticket_created_success"]:
        st.success(st.session_state["ticket_created_success"])
        st.session_state["ticket_created_success"] = None

    # Centered layout with equal margins on both left and right sides
    _, col_form, _ = st.columns([1, 3, 1])

    with col_form:
        with st.container(border=True):
            with st.form("new_ticket_form", clear_on_submit=True):
                st.markdown("<h4 style='margin: 0 0 12px 0;'>Ticket Details</h4>", unsafe_allow_html=True)

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
                submitted = st.form_submit_button("Submit Ticket", type="primary", use_container_width=True)

                if submitted:
                    success, result = create_ticket(
                        customer_name=customer_name,
                        subject=subject,
                        description=description
                    )

                    if success:
                        st.session_state["ticket_created_success"] = (
                            f"Ticket #{result} created successfully with status 'New'."
                        )
                        st.rerun()
                    else:
                        st.error(result)


if __name__ == "__main__" or True:
    render_new_ticket_page()
