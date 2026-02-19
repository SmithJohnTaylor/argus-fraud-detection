#!/usr/bin/env python3
"""
Minimal dashboard test to isolate button visibility issues
"""

import streamlit as st

def main():
    st.title("Test Dashboard")
    st.markdown("### Testing Button Visibility")
    
    st.markdown("If you can see this text, Streamlit is working.")
    
    if st.button("Test Button", type="primary"):
        st.success("Button clicked!")
    
    st.markdown("---")
    st.markdown("**Debug Info:**")
    st.write(f"Streamlit version: {st.__version__}")

if __name__ == "__main__":
    main()