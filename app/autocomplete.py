"""
Enhanced Search Component
-------------------------
Provides a YouTube-style autocomplete dropdown that filters as you type.
Uses Streamlit's session state to track input and show filtered suggestions.
"""

import streamlit as st


def autocomplete_search(options, key="search", placeholder="Start typing..."):
    """Create an autocomplete search box with live filtering.
    
    Args:
        options: List of strings to search through
        key: Unique key for this search box
        placeholder: Placeholder text
    
    Returns:
        The selected option or None
    """
    
    # Initialize session state for this search box
    if f"{key}_input" not in st.session_state:
        st.session_state[f"{key}_input"] = ""
    if f"{key}_selected" not in st.session_state:
        st.session_state[f"{key}_selected"] = None
    
    # Text input for typing
    user_input = st.text_input(
        "Search",
        value=st.session_state[f"{key}_input"],
        placeholder=placeholder,
        key=f"{key}_text",
        label_visibility="collapsed",
    )
    
    # Update session state
    st.session_state[f"{key}_input"] = user_input
    
    # Filter options based on input (case-insensitive)
    if user_input:
        filtered = [
            opt for opt in options 
            if user_input.lower() in opt.lower()
        ][:20]  # Limit to 20 suggestions
        
        if filtered:
            # Show dropdown with filtered results
            st.caption(f"💡 Showing {len(filtered)} matches")
            selected = st.selectbox(
                "Select from suggestions",
                options=[""] + filtered,
                key=f"{key}_dropdown",
                label_visibility="collapsed",
            )
            
            if selected:
                st.session_state[f"{key}_selected"] = selected
                st.session_state[f"{key}_input"] = selected
                return selected
        else:
            st.caption("No matches found. Try a different search term.")
    
    return st.session_state.get(f"{key}_selected")
