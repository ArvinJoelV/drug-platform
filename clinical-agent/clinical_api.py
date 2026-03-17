import requests
from typing import List, Dict

def fetch_trials(drug: str) -> List[Dict]:
    """
    Fetch up to 75 clinical trials for a specific drug from ClinicalTrials.gov (v2 API).
    """
    url = "https://clinicaltrials.gov/api/v2/studies"
    params = {
        "query.term": drug,
        "pageSize": 75,
        "fields": "NCTId,BriefTitle,Condition,Phase,OverallStatus,ReferencesModule,BriefSummary"
    }
    
    response = requests.get(url, params=params)
    response.raise_for_status()
    data = response.json()
    
    studies = data.get("studies", [])
    
    trials = []
    for study in studies:
        protocol = study.get("protocolSection", {})
        
        # ID Module
        id_module = protocol.get("identificationModule", {})
        trial_id = id_module.get("nctId", "N/A")
        title = id_module.get("briefTitle", "N/A")
        
        # Conditions Module
        cond_module = protocol.get("conditionsModule", {})
        conditions_list = cond_module.get("conditions", [])
        condition = conditions_list[0] if conditions_list else "N/A"
        
        # Design Module (Phase)
        design_module = protocol.get("designModule", {})
        phases = design_module.get("phases", [])
        phase = phases[0] if phases else "N/A"
        
        # Status Module
        status_module = protocol.get("statusModule", {})
        status = status_module.get("overallStatus", "N/A")
        
        # References Module
        ref_module = protocol.get("referencesModule", {})
        references = ref_module.get("references", [])
        pmids = []
        for ref in references:
            if "pmid" in ref:
                pmids.append(ref["pmid"])
                
        # Summary Module
        description_module = protocol.get("descriptionModule", {})
        summary = description_module.get("briefSummary", "N/A")
        
        trials.append({
            "trial_id": trial_id,
            "title": title,
            "condition": condition,
            "phase": phase,
            "status": status,
            "summary": summary,
            "pmids": pmids
        })
        
    return trials
