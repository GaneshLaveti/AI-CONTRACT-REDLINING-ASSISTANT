import streamlit as st
import re
import json
from datetime import datetime
import PyPDF2
from io import BytesIO

# Risk detection patterns and keywords
RISK_PATTERNS = {
    'liability': {
        'keywords': ['unlimited liability', 'no limitation', 'all liability', 'any and all liability', 
                    'indemnify', 'hold harmless', 'without limitation', 'to the fullest extent'],
        'risk_level': 'High',
        'rationale': 'Unlimited liability clauses expose the organization to excessive financial risk.',
        'suggestion': 'Liability should be limited to direct damages and capped at a reasonable amount (e.g., fees paid in the last 12 months).'
    },
    'termination': {
        'keywords': ['termination for convenience', 'terminate at will', 'without cause', 
                    'immediate termination', 'no notice'],
        'risk_level': 'Medium',
        'rationale': 'Lack of termination protections can result in sudden contract cancellations.',
        'suggestion': 'Include minimum notice periods (e.g., 30-90 days) and allow termination only for material breach or with adequate notice.'
    },
    'intellectual_property': {
        'keywords': ['all rights', 'exclusive rights', 'assign all intellectual property', 
                    'waive all rights', 'work for hire', 'transfer of ownership'],
        'risk_level': 'High',
        'rationale': 'Broad IP assignment can result in loss of valuable intellectual property.',
        'suggestion': 'Limit IP transfer to only what is necessary for the specific project. Retain ownership of pre-existing IP and general methodologies.'
    },
    'confidentiality': {
        'keywords': ['perpetual confidentiality', 'indefinite', 'in perpetuity', 
                    'no time limit', 'forever'],
        'risk_level': 'Medium',
        'rationale': 'Indefinite confidentiality obligations create long-term compliance burdens.',
        'suggestion': 'Limit confidentiality obligations to 3-5 years post-contract termination, with standard exceptions for publicly available information.'
    },
    'payment': {
        'keywords': ['non-refundable', 'upfront payment', 'payment in full', 
                    'immediate payment', 'no refunds'],
        'risk_level': 'Medium',
        'rationale': 'Unfavorable payment terms can create cash flow issues and limit recourse.',
        'suggestion': 'Structure payments based on milestones or deliverables. Include provisions for refunds in case of non-performance.'
    },
    'warranty': {
        'keywords': ['no warranty', 'as is', 'without warranty', 'disclaim all warranties', 
                    'no guarantee', 'express or implied'],
        'risk_level': 'High',
        'rationale': 'Absence of warranties leaves no recourse if deliverables are defective.',
        'suggestion': 'Include express warranties for fitness for purpose, merchantability, and compliance with specifications for a reasonable period.'
    },
    'dispute_resolution': {
        'keywords': ['exclusive jurisdiction', 'mandatory arbitration', 'waive right to jury', 
                    'binding arbitration', 'foreign jurisdiction'],
        'risk_level': 'Medium',
        'rationale': 'Unfavorable dispute resolution terms can make it difficult and expensive to resolve conflicts.',
        'suggestion': 'Negotiate for mutual jurisdiction, mediation before arbitration, and reasonable venue selection.'
    },
    'force_majeure': {
        'keywords': ['no force majeure', 'limited force majeure', 'excludes pandemic', 
                    'narrow force majeure'],
        'risk_level': 'Low',
        'rationale': 'Narrow force majeure clauses may not protect against unforeseen events.',
        'suggestion': 'Include comprehensive force majeure language covering natural disasters, pandemics, government actions, and other unforeseeable events.'
    }
}

def extract_text_from_pdf(pdf_file):
    """Extract text from uploaded PDF file."""
    try:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text()
        return text
    except Exception as e:
        st.error(f"Error extracting PDF: {str(e)}")
        return None

def segment_into_clauses(text):
    """Segment contract text into clauses/paragraphs."""
    # Split by double newlines or numbered sections
    paragraphs = re.split(r'\n\s*\n+|\n\s*\d+\.', text)
    
    # Clean and filter
    clauses = []
    for i, para in enumerate(paragraphs):
        cleaned = para.strip()
        if len(cleaned) > 50:  # Minimum length to be considered a clause
            clauses.append({
                'id': i + 1,
                'text': cleaned,
                'detected_risks': []
            })
    
    return clauses

def analyze_clause_risk(clause_text):
    """Analyze a clause for risk patterns."""
    clause_lower = clause_text.lower()
    detected_risks = []
    
    for risk_type, risk_data in RISK_PATTERNS.items():
        # Check if any keywords match
        matches = [kw for kw in risk_data['keywords'] if kw.lower() in clause_lower]
        
        if matches:
            detected_risks.append({
                'type': risk_type.replace('_', ' ').title(),
                'risk_level': risk_data['risk_level'],
                'matched_keywords': matches,
                'rationale': risk_data['rationale'],
                'suggestion': risk_data['suggestion']
            })
    
    return detected_risks

def generate_redline(original_text, risk_type):
    """Generate redlined version based on risk type."""
    suggestions = {
        'Liability': 'SUGGESTED REDLINE: "Party\'s total liability under this Agreement shall be limited to direct damages only and shall not exceed the total fees paid by Client in the twelve (12) months preceding the claim."',
        'Termination': 'SUGGESTED REDLINE: "Either party may terminate this Agreement for convenience upon ninety (90) days prior written notice. In case of material breach, termination may occur with thirty (30) days notice and opportunity to cure."',
        'Intellectual Property': 'SUGGESTED REDLINE: "Client shall own IP specifically created for this project. Provider retains ownership of pre-existing IP, tools, methodologies, and any general knowledge or experience gained."',
        'Confidentiality': 'SUGGESTED REDLINE: "Confidentiality obligations shall survive for three (3) years following termination, except for information that: (a) is publicly available, (b) was known prior to disclosure, or (c) is independently developed."',
        'Payment': 'SUGGESTED REDLINE: "Payment shall be made in installments based on project milestones: 30% upon signing, 40% upon milestone completion, 30% upon final delivery and acceptance."',
        'Warranty': 'SUGGESTED REDLINE: "Provider warrants that deliverables will conform to specifications and be fit for their intended purpose for ninety (90) days. Provider will remedy any defects at no additional cost during this period."',
        'Dispute Resolution': 'SUGGESTED REDLINE: "Disputes shall first be addressed through good-faith negotiation, followed by mediation if necessary. If unresolved, disputes may proceed to arbitration under mutually agreed rules in a neutral jurisdiction."',
        'Force Majeure': 'SUGGESTED REDLINE: "Neither party shall be liable for delays or failures due to force majeure events including natural disasters, pandemics, war, government actions, or other events beyond reasonable control."'
    }
    
    return suggestions.get(risk_type, 'No specific redline suggestion available.')

def main():
    st.set_page_config(page_title="AI Contract Redlining Assistant", layout="wide")
    
    # Header
    st.title("🤖 AI Contract Redlining Assistant")
    st.markdown("**Automatically detect risky clauses and get redline suggestions**")
    st.markdown("---")
    
    # Sidebar
    with st.sidebar:
        st.header("📋 About")
        st.info(
            "This tool analyzes contract clauses and provides:\n"
            "- Risk level assessment\n"
            "- Identified risky keywords\n"
            "- Rationale for concerns\n"
            "- Suggested redlines\n\n"
            "Upload a contract to get started!"
        )
        
        st.header("📊 Statistics")
        if 'analyzed_clauses' in st.session_state:
            st.metric("Clauses Analyzed", len(st.session_state.analyzed_clauses))
            high_risk = sum(1 for c in st.session_state.analyzed_clauses 
                          if any(r['risk_level'] == 'High' for r in c['detected_risks']))
            st.metric("High Risk Clauses", high_risk)
    
    # Main content
    tab1, tab2, tab3 = st.tabs(["📄 Upload & Analyze", "🔍 Review Results", "💾 Export"])
    
    with tab1:
        st.header("Upload Contract")
        
        upload_type = st.radio("Choose input method:", ["Upload PDF", "Paste Text"])
        
        contract_text = None
        
        if upload_type == "Upload PDF":
            uploaded_file = st.file_uploader("Upload contract PDF", type=['pdf'])
            if uploaded_file:
                with st.spinner("Extracting text from PDF..."):
                    contract_text = extract_text_from_pdf(uploaded_file)
                    if contract_text:
                        st.success("✅ PDF extracted successfully!")
                        with st.expander("View extracted text"):
                            st.text_area("Extracted Text", contract_text, height=200)
        else:
            contract_text = st.text_area("Paste contract text here:", height=300)
        
        if contract_text and st.button("🔍 Analyze Contract", type="primary"):
            with st.spinner("Analyzing contract clauses..."):
                # Segment into clauses
                clauses = segment_into_clauses(contract_text)
                st.success(f"✅ Identified {len(clauses)} clauses")
                
                # Analyze each clause
                for clause in clauses:
                    clause['detected_risks'] = analyze_clause_risk(clause['text'])
                
                # Store in session state
                st.session_state.analyzed_clauses = clauses
                st.session_state.full_text = contract_text
                
                # Show summary
                total_risks = sum(len(c['detected_risks']) for c in clauses)
                high_risk_clauses = sum(1 for c in clauses 
                                       if any(r['risk_level'] == 'High' for r in c['detected_risks']))
                
                col1, col2, col3 = st.columns(3)
                col1.metric("Total Clauses", len(clauses))
                col2.metric("Risks Detected", total_risks)
                col3.metric("High Risk Clauses", high_risk_clauses)
                
                st.info("👉 Switch to the 'Review Results' tab to see detailed analysis")
    
    with tab2:
        st.header("Detailed Risk Analysis")
        
        if 'analyzed_clauses' not in st.session_state:
            st.warning("⚠️ Please analyze a contract first in the 'Upload & Analyze' tab")
        else:
            clauses = st.session_state.analyzed_clauses
            
            # Filter options
            risk_filter = st.multiselect(
                "Filter by risk level:",
                ["High", "Medium", "Low"],
                default=["High", "Medium", "Low"]
            )
            
            # Display clauses
            for clause in clauses:
                if clause['detected_risks']:
                    # Check if clause matches filter
                    if any(r['risk_level'] in risk_filter for r in clause['detected_risks']):
                        with st.expander(f"📌 Clause #{clause['id']} - {len(clause['detected_risks'])} risk(s) detected", expanded=False):
                            st.markdown("**Original Clause:**")
                            st.text_area("", clause['text'], height=100, key=f"clause_{clause['id']}", disabled=True)
                            
                            st.markdown("---")
                            
                            for risk in clause['detected_risks']:
                                # Risk level badge
                                color = {"High": "🔴", "Medium": "🟡", "Low": "🟢"}[risk['risk_level']]
                                st.markdown(f"### {color} {risk['type']} Risk - **{risk['risk_level']}**")
                                
                                col1, col2 = st.columns([1, 1])
                                
                                with col1:
                                    st.markdown("**🔍 Matched Keywords:**")
                                    st.write(", ".join(f"`{kw}`" for kw in risk['matched_keywords']))
                                    
                                    st.markdown("**📝 Rationale:**")
                                    st.write(risk['rationale'])
                                
                                with col2:
                                    st.markdown("**✏️ Suggested Redline:**")
                                    redline = generate_redline(clause['text'], risk['type'])
                                    st.info(redline)
                                
                                st.markdown("---")
            
            if not any(c['detected_risks'] for c in clauses):
                st.success("✅ No significant risks detected in this contract!")
    
    with tab3:
        st.header("Export Results")
        
        if 'analyzed_clauses' not in st.session_state:
            st.warning("⚠️ Please analyze a contract first")
        else:
            st.markdown("### Export Options")
            
            export_format = st.radio("Choose export format:", ["JSON", "Text Report"])
            
            if export_format == "JSON":
                # Prepare JSON data
                export_data = {
                    'analysis_date': datetime.now().isoformat(),
                    'total_clauses': len(st.session_state.analyzed_clauses),
                    'total_risks': sum(len(c['detected_risks']) for c in st.session_state.analyzed_clauses),
                    'clauses': st.session_state.analyzed_clauses
                }
                
                json_str = json.dumps(export_data, indent=2)
                st.download_button(
                    label="📥 Download JSON",
                    data=json_str,
                    file_name=f"contract_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )
                
                with st.expander("Preview JSON"):
                    st.json(export_data)
            
            else:
                # Generate text report
                report = f"""CONTRACT RISK ANALYSIS REPORT
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
{'='*80}

SUMMARY
-------
Total Clauses Analyzed: {len(st.session_state.analyzed_clauses)}
Total Risks Detected: {sum(len(c['detected_risks']) for c in st.session_state.analyzed_clauses)}
High Risk Clauses: {sum(1 for c in st.session_state.analyzed_clauses if any(r['risk_level'] == 'High' for r in c['detected_risks']))}

DETAILED FINDINGS
-----------------
"""
                
                for clause in st.session_state.analyzed_clauses:
                    if clause['detected_risks']:
                        report += f"\n\nCLAUSE #{clause['id']}\n"
                        report += f"Text: {clause['text'][:200]}...\n"
                        report += f"Risks: {len(clause['detected_risks'])}\n"
                        
                        for risk in clause['detected_risks']:
                            report += f"\n  - {risk['type']} ({risk['risk_level']})\n"
                            report += f"    Rationale: {risk['rationale']}\n"
                            report += f"    Suggestion: {generate_redline(clause['text'], risk['type'])}\n"
                
                st.download_button(
                    label="📥 Download Text Report",
                    data=report,
                    file_name=f"contract_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    mime="text/plain"
                )
                
                with st.expander("Preview Report"):
                    st.text(report)

if __name__ == "__main__":
    main()