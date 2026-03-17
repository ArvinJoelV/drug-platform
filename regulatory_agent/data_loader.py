import json
import logging
from typing import List, Dict, Any
from pathlib import Path
from chroma_client import ChromaRegulatoryClient
from models import RegulatoryDocument, RegulatorySection

logger = logging.getLogger(__name__)


class RegulatoryDataLoader:
    """
    Loads regulatory data from various sources into ChromaDB.
    This is a sample implementation - in production, you'd connect to real APIs.
    """
    
    def __init__(self, chroma_client: ChromaRegulatoryClient):
        self.chroma_client = chroma_client
    
    def load_sample_data(self):
        """Load sample regulatory data for testing"""
        
        # Sample regulatory documents
        sample_docs = [
            # Aspirin
            RegulatoryDocument(
                drug_name="aspirin",
                section=RegulatorySection.INDICATIONS,
                content="ASPIRIN is indicated for: relief of pain and fever; reduction of risk of transient ischemic attacks and ischemic stroke in men; reduction of risk of myocardial infarction in patients with unstable angina or prior infarction; treatment of acute myocardial infarction; reduction of risk of cardiovascular events in patients with chronic stable angina.",
                source="FDA Label - Aspirin"
            ),
            RegulatoryDocument(
                drug_name="aspirin",
                section=RegulatorySection.WARNINGS,
                content="WARNINGS: Reye's syndrome - aspirin should not be used in children or teenagers for viral infections. Risk of bleeding - aspirin increases risk of bleeding, including gastrointestinal bleeding. Avoid in patients with active peptic ulcer disease. May cause severe allergic reactions including anaphylaxis.",
                source="FDA Label - Aspirin"
            ),
            RegulatoryDocument(
                drug_name="aspirin",
                section=RegulatorySection.ADVERSE,
                content="ADVERSE REACTIONS: Most common: gastrointestinal irritation, nausea, dyspepsia. Serious: gastrointestinal bleeding, hemorrhagic stroke, anaphylactic reactions. Other: tinnitus at high doses, rash, hepatic dysfunction.",
                source="FDA Label - Aspirin"
            ),
            RegulatoryDocument(
                drug_name="aspirin",
                section=RegulatorySection.CONTRADICTIONS,
                content="CONTRAINDICATIONS: Hypersensitivity to aspirin or NSAIDs; history of asthma, urticaria, or allergic reactions; children with viral infections (Reye's syndrome risk); active bleeding disorders; severe hepatic impairment.",
                source="FDA Label - Aspirin"
            ),
            
            # Metformin
            RegulatoryDocument(
                drug_name="metformin",
                section=RegulatorySection.INDICATIONS,
                content="METFORMIN is indicated as an adjunct to diet and exercise to improve glycemic control in adults and children with type 2 diabetes mellitus.",
                source="FDA Label - Metformin"
            ),
            RegulatoryDocument(
                drug_name="metformin",
                section=RegulatorySection.WARNINGS,
                content="WARNINGS: Lactic acidosis is a rare but serious complication. Risk factors include renal impairment, age, radiological studies with contrast, surgery, and hypoxic states. Monitor renal function before initiation and annually thereafter.",
                source="FDA Label - Metformin"
            ),
            RegulatoryDocument(
                drug_name="metformin",
                section=RegulatorySection.ADVERSE,
                content="ADVERSE REACTIONS: Most common: diarrhea, nausea, vomiting, flatulence, asthenia, indigestion, abdominal discomfort, headache. These are more common during initiation and usually resolve spontaneously.",
                source="FDA Label - Metformin"
            ),
            RegulatoryDocument(
                drug_name="metformin",
                section=RegulatorySection.CONTRADICTIONS,
                content="CONTRAINDICATIONS: Renal impairment (eGFR below 30 mL/min/1.73 m²); acute or chronic metabolic acidosis; hypersensitivity to metformin; acute conditions that can alter renal function.",
                source="FDA Label - Metformin"
            ),
            
            # Ibuprofen
            RegulatoryDocument(
                drug_name="ibuprofen",
                section=RegulatorySection.INDICATIONS,
                content="IBUPROFEN is indicated for relief of mild to moderate pain, reduction of fever, relief of signs and symptoms of rheumatoid arthritis and osteoarthritis, relief of primary dysmenorrhea.",
                source="FDA Label - Ibuprofen"
            ),
            RegulatoryDocument(
                drug_name="ibuprofen",
                section=RegulatorySection.WARNINGS,
                content="WARNINGS: Cardiovascular thrombotic events; gastrointestinal bleeding, ulceration, and perforation; hypertension; heart failure; renal toxicity; anaphylactic reactions; serious skin reactions.",
                source="FDA Label - Ibuprofen"
            ),
            RegulatoryDocument(
                drug_name="ibuprofen",
                section=RegulatorySection.ADVERSE,
                content="ADVERSE REACTIONS: Common: dyspepsia, nausea, gastrointestinal pain, constipation, diarrhea. Serious: gastrointestinal bleeding, cardiovascular events, renal impairment.",
                source="FDA Label - Ibuprofen"
            ),
            
            # Atorvastatin
            RegulatoryDocument(
                drug_name="atorvastatin",
                section=RegulatorySection.INDICATIONS,
                content="ATORVASTATIN is indicated: as an adjunct to diet to reduce elevated total-C, LDL-C, apo B, and TG levels; for primary prevention of cardiovascular disease; in patients with type 2 diabetes for primary prevention of CVD.",
                source="FDA Label - Atorvastatin"
            ),
            RegulatoryDocument(
                drug_name="atorvastatin",
                section=RegulatorySection.WARNINGS,
                content="WARNINGS: Skeletal muscle effects (myopathy, rhabdomyolysis); hepatic effects (increased transaminases); increased risk of diabetes mellitus; interactions with CYP3A4 inhibitors.",
                source="FDA Label - Atorvastatin"
            ),
            
            # Lisinopril
            RegulatoryDocument(
                drug_name="lisinopril",
                section=RegulatorySection.INDICATIONS,
                content="LISINOPRIL is indicated for treatment of hypertension, as adjunctive therapy in heart failure, and for treatment of acute myocardial infarction to improve survival.",
                source="FDA Label - Lisinopril"
            ),
            RegulatoryDocument(
                drug_name="lisinopril",
                section=RegulatorySection.WARNINGS,
                content="WARNINGS: Angioedema; hypotension; hyperkalemia; renal impairment; fetal toxicity; cough; avoid in pregnancy.",
                source="FDA Label - Lisinopril"
            ),
        ]
        
        self.chroma_client.add_documents(sample_docs)
        logger.info(f"Loaded {len(sample_docs)} sample documents")
        return len(sample_docs)
    
    def load_from_json(self, json_path: str):
        """
        Load regulatory data from JSON file.
        Expected format: list of dicts with keys: drug_name, section, content, source
        """
        path = Path(json_path)
        if not path.exists():
            logger.error(f"File not found: {json_path}")
            return 0
        
        with open(path, 'r') as f:
            data = json.load(f)
        
        documents = []
        for item in data:
            try:
                doc = RegulatoryDocument(
                    drug_name=item['drug_name'].lower(),
                    section=RegulatorySection(item['section']),
                    content=item['content'],
                    source=item['source'],
                    metadata=item.get('metadata', {})
                )
                documents.append(doc)
            except Exception as e:
                logger.warning(f"Skipping invalid item: {e}")
        
        if documents:
            self.chroma_client.add_documents(documents)
            logger.info(f"Loaded {len(documents)} documents from {json_path}")
        
        return len(documents)


# For testing
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    client = ChromaRegulatoryClient()
    loader = RegulatoryDataLoader(client)
    
    # Load sample data
    count = loader.load_sample_data()
    print(f"Loaded {count} documents")
    print(client.get_collection_stats())